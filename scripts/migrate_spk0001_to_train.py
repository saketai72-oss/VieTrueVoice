"""Migration script to integrate SPK_0001 into Train split while isolating 5 acceptance volunteers.

Plan Reference: plan-spk0001-train-transfer.md (TASK-3)
1. Ingests 75 bona fide rows (15 clips x 5 codecs from data/raw/SPK_0001/).
2. Ingests 50 F5-TTS spoof rows (10 prompts x 5 codecs from data/spoof_f5tts/SPK_0001/).
3. Strictly EXCLUDES 100% of VieNeu-TTS files (preserving Hypothesis H2).
4. Creates backup: data/manifests_zalo/train_zalo.csv.bak_v5.
5. Verifies 0% text leakage against dev_zalo.csv and test_indomain_zalo.csv.
6. Validates zero leakage with validate_split_leakage and validate_manifest.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
import soundfile as sf

from scripts.generate_zalo_paired_manifests import (
    ACCEPTANCE_VOLUNTEERS,
    derive_base_utt,
    validate_split_leakage,
)
from scripts.train import validate_manifest

BONA_TRANSCRIPTS = {
    "SPK_0001_01": "Cả hai bên hãy cố gắng bình tĩnh lắng nghe và cùng nhau tìm giải pháp phù hợp nhất.",
    "SPK_0001_02": "Sáng nay thời tiết ở thành phố khá mát mẻ, bầu trời nhiều mây và có gió nhẹ dễ chịu.",
    "SPK_0001_03": "Những kỹ năng xử lý thông tin an toàn trên mạng xã hội là điều mọi người cần rèn luyện.",
    "SPK_0001_04": "Em đã kiểm tra lại toàn bộ lịch trình làm việc tuần tới để đảm bảo không bị trùng công việc.",
    "SPK_0001_05": "Mỗi buổi tối cả gia đình thường quây quần bên mâm cơm ấm cúng chia sẻ những buồn vui.",
    "SPK_0001_06": "Mẹ ơi tối nay con phải ở lại trường làm thêm bài tập nhóm với các bạn.",
    "SPK_0001_07": "Cuối tuần này nếu không có lịch học bù thì con sẽ bắt xe buýt về quê thăm ông bà.",
    "SPK_0001_08": "Bố nhớ uống thuốc huyết áp đúng giờ như bác sĩ đã dặn dò sau bữa sáng nhé.",
    "SPK_0001_09": "Hôm qua chỗ con ở mưa lớn ngập hết cả con đường nên xe máy bị chết máy giữa đường.",
    "SPK_0001_10": "Em mới gửi file tài liệu thuyết trình qua Zalo rồi, anh kiểm tra lại giúp em nhé.",
    "SPK_0001_11": "Chiều nay tan ca xong mình ghé siêu thị gần nhà mua ít rau củ và thịt tươi về nấu cơm.",
    "SPK_0001_12": "Điện thoại của con dạo này pin hơi yếu nên thỉnh thoảng sập nguồn, có gì mẹ nhắn tin nhé.",
    "SPK_0001_13": "Alo mẹ ơi cứu con với, con vừa mới va chạm xe trên đường đang phải vào viện cấp cứu gấp.",
    "SPK_0001_14": "Bố ơi máy con đang hỏng loa không nghe gọi lại được, bố chuyển khoản gấp vào số tài khoản này cho con.",
    "SPK_0001_15": "Mẹ đừng gọi lại cho con lúc này vì con đang làm việc với công an, cứ chuyển tiền theo số con nhắn.",
}

SPOOF_PROMPT_TRANSCRIPTS = {
    "SPK_0001_prompt_000": "Mẹ ơi tối nay con phải ở lại trường làm thêm bài tập nhóm với các bạn.",
    "SPK_0001_prompt_001": "Cuối tuần này nếu không có lịch học bù thì con sẽ bắt xe buýt về quê thăm ông bà.",
    "SPK_0001_prompt_002": "Bố nhớ uống thuốc huyết áp đúng giờ như bác sĩ đã dặn dò sau bữa sáng nhé.",
    "SPK_0001_prompt_003": "Hôm qua chỗ con ở mưa lớn ngập hết cả con đường nên xe máy bị chết máy giữa đường.",
    "SPK_0001_prompt_004": "Em mới gửi file tài liệu thuyết trình qua Zalo rồi, anh kiểm tra lại giúp em nhé.",
    "SPK_0001_prompt_005": "Chiều nay tan ca xong mình ghé siêu thị gần nhà mua ít rau củ và thịt tươi về nấu cơm.",
    "SPK_0001_prompt_006": "Điện thoại của con dạo này pin hơi yếu nên thỉnh thoảng sập nguồn, có gì mẹ nhắn tin nhé.",
    "SPK_0001_prompt_007": "Alo mẹ ơi cứu con với, con vừa mới va chạm xe trên đường đang phải vào viện cấp cứu gấp.",
    "SPK_0001_prompt_008": "Bố ơi máy con đang hỏng loa không nghe gọi lại được, bố chuyển khoản gấp vào số tài khoản này cho con.",
    "SPK_0001_prompt_009": "Mẹ đừng gọi lại cho con lúc này vì con đang làm việc với công an, cứ chuyển tiền theo số con nhắn.",
}

CODEC_CONFIGS = [
    {
        "suffix": "",
        "utt_suffix": "_clean",
        "codec": "clean_16khz",
        "pre_codec": "clean_16khz",
    },
    {
        "suffix": "_aac_zalo",
        "utt_suffix": "_aac_zalo",
        "codec": "aac_zalo_76k",
        "pre_codec": "aac_76k_m4a",
    },
    {
        "suffix": "_opus_zalo",
        "utt_suffix": "_opus_zalo",
        "codec": "opus_zalo_24k",
        "pre_codec": "opus_24k_ogg",
    },
    {
        "suffix": "_amrnb",
        "utt_suffix": "_amrnb",
        "codec": "amr_nb",
        "pre_codec": "none",
    },
    {
        "suffix": "_g711",
        "utt_suffix": "_g711",
        "codec": "g711_alaw",
        "pre_codec": "none",
    },
]


def load_spoof_metrics(spoof_manifest_path: Path) -> dict[str, dict]:
    """Load ECAPA similarity, WER, CER and tier from legacy spoof_manifest.csv."""
    metrics_map = {}
    if not spoof_manifest_path.exists():
        return metrics_map

    df = pd.read_csv(spoof_manifest_path)
    f5_df = df[(df["speaker_id"] == "SPK_0001") & (df["engine_name"] == "F5-TTS-Vietnamese")]
    for _, row in f5_df.iterrows():
        stem = Path(row["audio_path"]).stem
        base = derive_base_utt(stem)
        if base not in metrics_map:
            metrics_map[base] = {
                "raw_wer": row["raw_wer"] if pd.notna(row["raw_wer"]) else np.nan,
                "raw_cer": row["raw_cer"] if pd.notna(row["raw_cer"]) else np.nan,
                "ecapa_sim": row["ecapa_sim"] if pd.notna(row["ecapa_sim"]) else np.nan,
                "derived_tier": row["derived_tier"] if pd.notna(row["derived_tier"]) else "Tier 1 (Strong)",
                "seed": int(row["seed"]) if pd.notna(row["seed"]) else 100,
            }
    return metrics_map


def build_spk0001_rows(
    spoof_manifest_path: Path = Path("data/manifests/spoof_manifest.csv"),
) -> list[dict]:
    """Build the exact 125 rows for SPK_0001 (75 bonafide, 50 F5-TTS spoof)."""
    metrics_map = load_spoof_metrics(spoof_manifest_path)
    rows: list[dict] = []

    # 1. 75 Bonafide Rows (15 clips x 5 codecs)
    raw_dir = Path("data/raw/SPK_0001")
    for i in range(1, 16):
        base_utt = f"SPK_0001_{i:02d}"
        transcript = BONA_TRANSCRIPTS[base_utt]

        for cfg in CODEC_CONFIGS:
            audio_path = raw_dir / f"{base_utt}{cfg['suffix']}.wav"
            if not audio_path.exists():
                raise FileNotFoundError(f"Missing bona fide audio file: {audio_path}")

            dur = round(float(sf.info(str(audio_path)).duration), 4)
            utt_id = f"{base_utt}{cfg['utt_suffix']}"

            rows.append({
                "utt_id": utt_id,
                "audio_path": audio_path.as_posix(),
                "speaker_id": "SPK_0001",
                "source": "volunteer_deep",
                "label": "bonafide",
                "role": "train",
                "tts_generator": "none",
                "codec": cfg["codec"],
                "pre_codec": cfg["pre_codec"],
                "split": "train",
                "duration_sec": dur,
                "transcript": transcript,
                "raw_wer": np.nan,
                "raw_cer": np.nan,
                "ecapa_sim": np.nan,
                "wavlm_sim": np.nan,
                "derived_tier": "BonaFide",
                "seed": 42,
                "base_utt": base_utt,
            })

    # 2. 50 Spoof Rows (10 prompts x 5 codecs) - F5-TTS ONLY, ZERO VieNeu-TTS
    f5_dir = Path("data/spoof_f5tts/SPK_0001")
    for i in range(10):
        base_utt = f"SPK_0001_prompt_{i:03d}"
        transcript = SPOOF_PROMPT_TRANSCRIPTS[base_utt]
        metrics = metrics_map.get(base_utt, {
            "raw_wer": np.nan,
            "raw_cer": np.nan,
            "ecapa_sim": np.nan,
            "derived_tier": "Tier 1 (Strong)",
            "seed": 100,
        })

        for cfg in CODEC_CONFIGS:
            audio_path = f5_dir / f"{base_utt}{cfg['suffix']}.wav"
            if not audio_path.exists():
                raise FileNotFoundError(f"Missing F5-TTS spoof audio file: {audio_path}")

            dur = round(float(sf.info(str(audio_path)).duration), 4)
            utt_id = f"{base_utt}{cfg['utt_suffix']}"

            rows.append({
                "utt_id": utt_id,
                "audio_path": audio_path.as_posix(),
                "speaker_id": "SPK_0001",
                "source": "volunteer_deep",
                "label": "spoof",
                "role": "train",
                "tts_generator": "F5-TTS-Vietnamese",
                "codec": cfg["codec"],
                "pre_codec": cfg["pre_codec"],
                "split": "train",
                "duration_sec": dur,
                "transcript": transcript,
                "raw_wer": metrics["raw_wer"],
                "raw_cer": metrics["raw_cer"],
                "ecapa_sim": metrics["ecapa_sim"],
                "wavlm_sim": np.nan,
                "derived_tier": metrics["derived_tier"],
                "seed": metrics["seed"],
                "base_utt": base_utt,
            })

    return rows


def migrate_spk0001(
    manifest_dir: Path = Path("data/manifests_zalo"),
    backup: bool = True,
) -> pd.DataFrame:
    """Execute migration: append SPK_0001 rows to train_zalo.csv after strict verification."""
    train_path = manifest_dir / "train_zalo.csv"
    dev_path = manifest_dir / "dev_zalo.csv"
    test_path = manifest_dir / "test_indomain_zalo.csv"

    if not train_path.exists():
        raise FileNotFoundError(f"Train manifest not found: {train_path}")

    # Backup existing manifest
    if backup:
        bak_path = manifest_dir / "train_zalo.csv.bak_v5"
        shutil.copy2(train_path, bak_path)
        print(f"📦 Đã tạo tệp sao lưu manifest: {bak_path}")

    orig_df = pd.read_csv(train_path)
    print(f"📊 Tập train_zalo hiện tại có: {len(orig_df)} dòng.")

    # Remove existing SPK_0001 if already present to guarantee idempotent migration
    if "speaker_id" in orig_df.columns and (orig_df["speaker_id"] == "SPK_0001").any():
        print("⚠️ Phát hiện SPK_0001 cũ trong train_zalo.csv, tiến hành làm mới...")
        orig_df = orig_df[orig_df["speaker_id"] != "SPK_0001"].copy()

    # Build new 125 rows
    spk0001_rows = build_spk0001_rows()
    spk0001_df = pd.DataFrame(spk0001_rows)

    assert len(spk0001_df) == 125, f"Expected exactly 125 rows, got {len(spk0001_df)}"
    assert (spk0001_df["label"] == "bonafide").sum() == 75, "Expected 75 bonafide rows"
    assert (spk0001_df["label"] == "spoof").sum() == 50, "Expected 50 spoof rows"
    assert not spk0001_df["audio_path"].str.contains("vieneu", case=False).any(), "Found forbidden VieNeu file!"
    assert not spk0001_df["tts_generator"].str.contains("vieneu", case=False).any(), "Found forbidden VieNeu generator!"

    # Ensure identical columns
    merged_df = pd.concat([orig_df, spk0001_df[orig_df.columns]], ignore_index=True)
    print(f"✅ Đã hợp nhất dữ liệu: {len(orig_df)} + {len(spk0001_df)} = {len(merged_df)} dòng.")

    # Validation 1: Hard Text-Disjoint check
    dev_df = pd.read_csv(dev_path)
    test_df = pd.read_csv(test_path)

    dev_texts = set(dev_df["transcript"].dropna().str.strip().str.lower().unique())
    test_texts = set(test_df["transcript"].dropna().str.strip().str.lower().unique())
    spk1_texts = set(spk0001_df["transcript"].dropna().str.strip().str.lower().unique())

    if leak_dev := spk1_texts.intersection(dev_texts):
        raise ValueError(f"Text leakage detected between SPK_0001 and Dev: {leak_dev}")
    if leak_test := spk1_texts.intersection(test_texts):
        raise ValueError(f"Text leakage detected between SPK_0001 and Test: {leak_test}")
    print("🔒 0% Text leakage: SPK_0001 hoàn toàn Text-Disjoint với Dev và Test.")

    # Validation 2: validate_split_leakage
    validate_split_leakage(merged_df, dev_df, test_df)
    print("🔒 validate_split_leakage PASS: Zero leakage giữa Train, Dev, Test.")

    # Validation 3: validate_manifest on train
    validate_manifest(merged_df, "train")
    print("🔒 validate_manifest PASS: 5 SPK nghiệm thu được bảo vệ 100%, SPK_0001 hợp lệ trong Train.")

    # Write out
    merged_df.to_csv(train_path, index=False, encoding="utf-8")
    print(f"💾 Đã ghi đè manifest mới tại: {train_path}")

    return merged_df


if __name__ == "__main__":
    migrate_spk0001()
