"""Đánh giá toàn bộ tập Dev (seen-only) bằng checkpoint SSL-AASIST.

Hỗ trợ chạy theo lô an toàn, tự động lưu tiến độ (resumable),
đo VRAM/thời gian thực tế, và xuất bảng điểm chi tiết theo phát ngôn gốc.
"""

from __future__ import annotations
import argparse
import hashlib
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

from scripts.eval_ssl_aasist import load_model
from src.evaluation.metrics import compute_eer
from src.training.dataset import fit_length, load_wave


def compute_file_sha256(path: Path | str) -> str:
    p = Path(path)
    if not p.exists():
        return "NOT_FOUND"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def derive_base_utt(utt_id: str) -> str:
    """Tách mã phát ngôn gốc, loại bỏ hậu tố codec."""
    s = str(utt_id)
    for sfx in ["_g711", "_amrnb", "_clean"]:
        if s.endswith(sfx):
            return s[: -len(sfx)]
    return s


class DevInferenceDataset(Dataset):
    """Dataset đọc audio an toàn cho suy luận theo lô."""

    def __init__(self, df: pd.DataFrame, audio_root: Path | str, target_len: int = 64000):
        self.df = df.reset_index(drop=True)
        self.root = Path(audio_root)
        self.target_len = target_len
        self.rng = np.random.default_rng(42)

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.df.iloc[idx]
        audio_path = self.root / row["audio_path"]
        if not audio_path.exists():
            # Fallback nếu audio_path đã có tiền tố out hoặc root khác
            alt = Path(row["audio_path"])
            if alt.exists():
                audio_path = alt
            else:
                raise FileNotFoundError(f"Không tìm thấy file: {audio_path}")

        wav = load_wave(audio_path, sr=16000)
        wav = fit_length(wav, self.target_len, train=False, rng=self.rng)

        return {
            "index": idx,
            "utt_id": str(row["utt_id"]),
            "speaker_id": str(row["speaker_id"]),
            "base_utt": derive_base_utt(str(row["utt_id"])),
            "source": str(row.get("source", "")),
            "label": str(row["label"]),
            "tts_generator": str(row.get("tts_generator", "none")),
            "codec": str(row.get("codec", "clean_16khz")),
            "waveform": torch.from_numpy(wav).float(),
        }


def run_dev_eval(
    ckpt_path: Path | str,
    manifest_path: Path | str,
    audio_root: Path | str = ".",
    out_csv: Path | str = Path("out/diagnostics/dev_scores_full.csv"),
    batch_size: int = 16,
    chunk_save_interval: int = 256,
    device: str | None = None,
    limit: int = 0,
) -> pd.DataFrame:
    ckpt_p = Path(ckpt_path)
    manifest_p = Path(manifest_path)
    out_p = Path(out_csv)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 60)
    print("🔍 VIETRUEVOICE — ĐÁNH GIÁ TOÀN BỘ TẬP DEV (SEEN-ONLY)")
    print("=" * 60)

    # 1. Khóa và kiểm tra mã băm
    ckpt_sha = compute_file_sha256(ckpt_p)
    manifest_sha = compute_file_sha256(manifest_p)
    print(f"📦 Checkpoint: {ckpt_p} | SHA-256: {ckpt_sha}")
    print(f"📄 Manifest:   {manifest_p} | SHA-256: {manifest_sha}")
    print(f"⚙️ Thiết bị:   {device}")

    # 2. Đọc và xác thực manifest
    df_manifest = pd.read_csv(manifest_p, keep_default_na=False)
    if limit > 0:
        print(f"⚡ Giới hạn kiểm thử: {limit} dòng")
        df_manifest = df_manifest.head(limit)

    total_manifest_rows = len(df_manifest)
    print(f"📊 Tổng số dòng cần chấm: {total_manifest_rows}")
    print(f"   - Bonafide: {sum(df_manifest['label'] == 'bonafide')}")
    print(f"   - Spoof:    {sum(df_manifest['label'] == 'spoof')}")

    # 3. Kiểm tra khả năng tiếp tục (Resume)
    existing_records: list[dict[str, Any]] = []
    completed_utt_ids: set[str] = set()

    if out_p.exists():
        try:
            df_prev = pd.read_csv(out_p, keep_default_na=False)
            if "utt_id" in df_prev.columns and len(df_prev) > 0:
                completed_utt_ids = set(df_prev["utt_id"].astype(str))
                existing_records = df_prev.to_dict("records")
                print(f"🔄 Tìm thấy kết quả đã chấm trước đó: {len(completed_utt_ids)} mẫu.")
        except Exception as e:
            print(f"⚠️ Không thể đọc file kết quả cũ ({e}), bắt đầu lại từ đầu.")

    df_remaining = df_manifest[~df_manifest["utt_id"].astype(str).isin(completed_utt_ids)].copy()
    print(f"⏳ Số dòng còn lại cần chấm: {len(df_remaining)}")

    if len(df_remaining) == 0 and len(existing_records) == total_manifest_rows:
        print("✅ Toàn bộ manifest đã được chấm xong trước đó!")
        df_result = pd.DataFrame(existing_records)
        return df_result

    # 4. Nạp mô hình
    print("🤖 Đang nạp mô hình SSL-AASIST...")
    model, ckpt_meta = load_model(ckpt_p, device=device)
    print(f"   - Nhánh: {ckpt_meta.get('branch')} | Phase: {ckpt_meta.get('phase')} | Epoch: {ckpt_meta.get('epoch')}")

    dataset = DevInferenceDataset(df_remaining, audio_root=audio_root)

    # 5. Khảo sát đo thời gian / VRAM thực tế trên lô nhỏ khởi động
    warmup_size = min(4, len(dataset))
    if warmup_size > 0:
        warmup_loader = DataLoader(dataset, batch_size=warmup_size, shuffle=False)
        w_batch = next(iter(warmup_loader))
        t_w0 = time.perf_counter()
        with torch.inference_mode():
            _ = model.score(w_batch["waveform"].to(device))
            if device == "cuda":
                torch.cuda.synchronize()
        dt_warmup = time.perf_counter() - t_w0
        vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024) if device == "cuda" else 0.0
        print(f"🚀 Đo thực tế lô khởi động ({warmup_size} mẫu): {dt_warmup:.2f}s | VRAM đỉnh: {vram_mb:.1f} MB")

    # 6. Chạy suy luận theo lô
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    current_chunk: list[dict[str, Any]] = []
    t_start = time.perf_counter()
    scored_since_start = 0

    print(f"▶️ Bắt đầu suy luận (batch_size={batch_size}, lưu mỗi {chunk_save_interval} mẫu)...")

    for batch in loader:
        waveforms = batch["waveform"].to(device)
        with torch.inference_mode():
            scores_tensor = model.score(waveforms)
            scores = scores_tensor.float().cpu().numpy().tolist()

        for idx_in_batch, score_val in enumerate(scores):
            raw_score = float(score_val)
            if np.isnan(raw_score) or np.isinf(raw_score):
                raise ValueError(f"Phát hiện điểm không hợp lệ (NaN/Inf) tại utt_id={batch['utt_id'][idx_in_batch]}")

            rec = {
                "utt_id": batch["utt_id"][idx_in_batch],
                "speaker_id": batch["speaker_id"][idx_in_batch],
                "base_utt": batch["base_utt"][idx_in_batch],
                "source": batch["source"][idx_in_batch],
                "label": batch["label"][idx_in_batch],
                "tts_generator": batch["tts_generator"][idx_in_batch],
                "codec": batch["codec"][idx_in_batch],
                "raw_score": round(raw_score, 4),
                "prediction_thr0": "BONA_FIDE" if raw_score >= 0.0 else "SPOOF",
                "checkpoint_sha256": ckpt_sha[:16],
                "manifest_sha256": manifest_sha[:16],
            }
            existing_records.append(rec)
            current_chunk.append(rec)
            scored_since_start += 1

        # Lưu checkpoint kết quả định kỳ
        if len(current_chunk) >= chunk_save_interval:
            pd.DataFrame(existing_records).to_csv(out_p, index=False)
            elapsed = time.perf_counter() - t_start
            speed = scored_since_start / elapsed if elapsed > 0 else 0
            print(f"  💾 Đã lưu {len(existing_records)}/{total_manifest_rows} mẫu ({speed:.1f} mẫu/s)...", flush=True)
            current_chunk = []

    # Lưu toàn bộ kết quả cuối cùng
    df_result = pd.DataFrame(existing_records)
    df_result.to_csv(out_p, index=False)
    total_elapsed = time.perf_counter() - t_start
    print(f"🏁 Hoàn thành chấm toàn bộ {len(df_result)} mẫu trong {total_elapsed:.1f}s!")

    # 7. Kiểm tra toàn vẹn
    assert len(df_result) == total_manifest_rows, f"Kích thước không khớp: {len(df_result)} vs {total_manifest_rows}"
    assert df_result["utt_id"].nunique() == total_manifest_rows, "Có utt_id bị trùng lặp trong kết quả!"

    # 8. Báo cáo nhanh tại ngưỡng 0.0
    bona_df = df_result[df_result["label"] == "bonafide"]
    spoof_df = df_result[df_result["label"] == "spoof"]
    far = (spoof_df["raw_score"] >= 0.0).mean() * 100.0 if len(spoof_df) > 0 else float("nan")
    frr = (bona_df["raw_score"] < 0.0).mean() * 100.0 if len(bona_df) > 0 else float("nan")

    print("\n" + "=" * 60)
    print("📈 TỔNG KẾT NHANH TẬP DEV (SEEN-ONLY)")
    print("=" * 60)
    if len(spoof_df) > 0 and len(bona_df) > 0:
        scores_arr = df_result["raw_score"].to_numpy()
        labels_arr = (df_result["label"] == "bonafide").astype(int).to_numpy()
        eer_val, eer_thr = compute_eer(scores_arr, labels_arr)
        print(f"• EER:                {eer_val * 100:.2f}% (tại ngưỡng EER = {eer_thr:+.4f})")
    else:
        print("• EER:                N/A (cần cả mẫu bonafide và spoof để tính EER)")

    print(f"• Tại ngưỡng θ = 0.0: FRR (Bona bị loại) = {frr:.2f}% | FAR (Spoof bị lọt) = {far:.2f}%")
    print(f"• Phát ngôn cơ sở:   {df_result['base_utt'].nunique()} phát ngôn độc lập")
    print(f"• File đã lưu tại:   {out_p}")
    print("=" * 60 + "\n")

    return df_result


def main() -> None:
    ap = argparse.ArgumentParser(description="Chấm điểm an toàn cho toàn bộ Dev seen-only.")
    ap.add_argument("--ckpt", default="out/run_B/best_model.pt", help="Đường dẫn checkpoint")
    ap.add_argument("--manifest", default="kaggle_v3_meta/data/manifests_seen_only/dev.csv", help="Đường dẫn dev manifest seen-only")
    ap.add_argument("--audio-root", default=".", help="Thư mục gốc của audio")
    ap.add_argument("--out", default="out/diagnostics/dev_scores_full.csv", help="Đường dẫn file CSV kết quả")
    ap.add_argument("--batch-size", type=int, default=16, help="Kích thước lô")
    ap.add_argument("--chunk-interval", type=int, default=256, help="Số mẫu giữa mỗi lần lưu đệm")
    ap.add_argument("--limit", type=int, default=0, help="Giới hạn số mẫu kiểm thử nhanh")
    args = ap.parse_args()

    run_dev_eval(
        ckpt_path=args.ckpt,
        manifest_path=args.manifest,
        audio_root=args.audio_root,
        out_csv=args.out,
        batch_size=args.batch_size,
        chunk_save_interval=args.chunk_interval,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
