"""Automated spoofed audio generation script for ViTrueVoice.

Integrates F5-TTS-Vietnamese, VieNeu-TTS, and Unseen tool pipelines.
Implements prompt normalization and duration validation per Step 1.2 of PLAN.md.
Supports batch preprocessing of bonafide audio and batch spoof generation via SPK_test.
"""

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Optional, Tuple, Union
import librosa
import numpy as np
import pandas as pd
import soundfile as sf


SPEAKER_SPLIT = {
    "SPK_0001": "train",
    "SPK_0004": "train",
    "SPK_0005": "train",
    "SPK_0006": "dev",
    "SPK_0007": "test",
}

MANIFEST_COLUMNS = [
    "utt_id",
    "audio_path",
    "speaker_id",
    "label",
    "tts_generator",
    "vocoder",
    "codec",
    "split",
    "duration_sec",
    "transcript",
    "wer",
    "cer",
    "ecapa_sim",
    "derived_tier",
    "engine_name",
    "ref_audio_path",
    "seed",
]


def sanitize_prompt(text: str, max_chars: int = 250) -> str:
    """Normalize synthesis text prompt to lowercase and enforce character limits.

    F5-TTS and VieNeu-TTS perform best on lowercase text with Vietnamese punctuation intact.
    """
    clean = " ".join(text.strip().split()).lower()
    if len(clean) > max_chars:
        clean = clean[:max_chars].rstrip()
    return clean


def validate_audio_duration(duration_sec: float, min_sec: float = 1.0, max_sec: float = 30.0) -> bool:
    """Validate whether synthesized audio falls within legitimate target duration (1s–30s)."""
    return min_sec <= duration_sec <= max_sec


def get_audio_file_duration(file_path: str | Path) -> float:
    """Get audio duration in seconds using soundfile."""
    info = sf.info(str(file_path))
    return float(info.duration)


def load_and_trim_audio(
    audio_path: str | Path,
    target_sr: int = 16000,
    top_db: float = 30.0,
) -> Tuple[np.ndarray, int]:
    """Load audio, resample to target_sr mono, and trim leading/trailing silence.

    Falls back to ffmpeg pipe if libsndfile cannot decode container (e.g. m4a or aac-in-wav).
    """
    p = Path(audio_path)
    try:
        wav, sr = sf.read(str(p), dtype="float32")
        if wav.ndim > 1:
            wav = np.mean(wav, axis=1)
        if sr != target_sr:
            wav = librosa.resample(wav, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
    except Exception:
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(p),
            "-ar", str(target_sr),
            "-ac", "1",
            "-f", "s16le",
            "-"
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        wav = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        sr = target_sr

    if len(wav) > 512:
        wav_trimmed, _ = librosa.effects.trim(wav, top_db=top_db)
        if len(wav_trimmed) > 0:
            wav = wav_trimmed

    return wav, target_sr


def preprocess_bonafide_batch(
    src_spk_dirs: List[Union[str, Path]],
    data_dir: Union[str, Path] = "data",
    metadata_csv_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Batch preprocess bonafide recordings to 16kHz mono PCM and build bonafide_manifest.csv.

    Args:
        src_spk_dirs: List of source directories containing speaker audio (e.g. SPK_0001/).
        data_dir: Destination data directory (e.g. data/).
        metadata_csv_path: Path to metadata.csv with transcripts and is_ref labels.

    Returns:
        DataFrame containing all 17 manifest columns for bonafide audio.
    """
    d_path = Path(data_dir)
    raw_dir = d_path / "raw"
    ref_dir = d_path / "bonafide_ref"
    manifests_dir = d_path / "manifests"

    raw_dir.mkdir(parents=True, exist_ok=True)
    ref_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    meta_lookup: Dict[str, dict] = {}
    csv_cand = Path(metadata_csv_path) if metadata_csv_path else Path("C:/Codes/SPK_test/data/metadata.csv")
    if csv_cand.exists():
        meta_df = pd.read_csv(csv_cand)
        for _, row in meta_df.iterrows():
            stem = Path(str(row["filename"])).stem
            meta_lookup[stem] = row.to_dict()

    audio_exts = {".wav", ".m4a", ".mp3", ".flac", ".ogg"}
    records = []

    for spk_path_in in src_spk_dirs:
        p_spk = Path(spk_path_in)
        if not p_spk.exists():
            continue
        spk_id = p_spk.name
        raw_spk_dir = raw_dir / spk_id
        ref_spk_dir = ref_dir / spk_id
        raw_spk_dir.mkdir(parents=True, exist_ok=True)

        for audio_file in sorted(p_spk.glob("*")):
            if audio_file.suffix.lower() not in audio_exts:
                continue

            stem = audio_file.stem
            wav, sr = load_and_trim_audio(audio_file, target_sr=16000, top_db=30.0)

            dst_raw_wav = raw_spk_dir / f"{stem}.wav"
            sf.write(str(dst_raw_wav), wav, sr, subtype="PCM_16")
            dur = len(wav) / sr

            meta_info = meta_lookup.get(stem, {})
            trans = meta_info.get("transcript", "")
            is_ref = meta_info.get("is_ref", False)
            if isinstance(is_ref, str):
                is_ref = is_ref.lower() in ["true", "1", "yes"]

            subgroup = str(meta_info.get("subgroup", ""))
            if is_ref or "ref" in subgroup.lower():
                ref_spk_dir.mkdir(parents=True, exist_ok=True)
                dst_ref_wav = ref_spk_dir / f"{stem}.wav"
                sf.write(str(dst_ref_wav), wav, sr, subtype="PCM_16")

            rec = {
                "utt_id": stem,
                "audio_path": dst_raw_wav.as_posix(),
                "speaker_id": spk_id,
                "label": "bonafide",
                "tts_generator": "none",
                "vocoder": "bonafide",
                "codec": "clean_16khz",
                "split": SPEAKER_SPLIT.get(spk_id, "train"),
                "duration_sec": round(dur, 4),
                "transcript": trans,
                "wer": None,
                "cer": None,
                "ecapa_sim": None,
                "derived_tier": "BonaFide",
                "engine_name": None,
                "ref_audio_path": None,
                "seed": None,
            }
            records.append(rec)

    manifest_df = pd.DataFrame(records)
    for col in MANIFEST_COLUMNS:
        if col not in manifest_df.columns:
            manifest_df[col] = None

    manifest_df = manifest_df[MANIFEST_COLUMNS]
    out_csv = manifests_dir / "bonafide_manifest.csv"
    manifest_df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"✅ Đã tiền xử lý {len(manifest_df)} file bonafide -> {out_csv}")
    return manifest_df


def run_batch(
    data_dir: Union[str, Path] = "data",
    mode: str = "ADAPTIVE",
    mock: bool = False,
    spk_test_src: str = "C:/Codes/SPK_test/src",
) -> List[dict]:
    """Execute batch spoof generation using SPK_test dual pipeline."""
    d_path = Path(data_dir)
    manifests_dir = d_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = d_path / "raw"
    spoof_f5_dir = d_path / "spoof_f5tts"
    spoof_vieneu_dir = d_path / "spoof_vieneu"

    bonafide_csv = manifests_dir / "bonafide_manifest.csv"
    if not bonafide_csv.exists():
        print("⚠️ Chưa có bonafide_manifest.csv. Đang chạy preprocess_bonafide_batch trước...")
        preprocess_bonafide_batch(
            src_spk_dirs=[Path(f"SPK_{i:04d}") for i in [1, 4, 5, 6, 7]],
            data_dir=data_dir,
        )
    bonafide_df = pd.read_csv(bonafide_csv)

    if mock:
        print("🧪 Đang sinh dữ liệu spoof mock cho kiểm thử...")
        mock_records = []
        for spk_id, spk_df in bonafide_df.groupby("speaker_id"):
            prompts = spk_df[spk_df["transcript"].notna()]["transcript"].tolist()[:2]
            out_spk_dir = spoof_f5_dir / str(spk_id)
            out_spk_dir.mkdir(parents=True, exist_ok=True)
            for idx, text in enumerate(prompts):
                out_wav = out_spk_dir / f"{spk_id}_prompt_{idx:03d}.wav"
                generate_spoof_sample(
                    engine="mock",
                    ref_audio="dummy.wav",
                    gen_text=text,
                    output_path=out_wav,
                    mock=True,
                )
                rec = {
                    "audio_path": out_wav.as_posix(),
                    "speaker_id": str(spk_id),
                    "is_bonafide": False,
                    "codec": "clean_16khz",
                    "ecapa_sim": 0.85,
                    "raw_wer": 0.05,
                    "raw_cer": 0.02,
                    "derived_tier": "Tier 1 (Strong)",
                    "engine_name": "F5-TTS",
                    "ref_audio_path": f"data/bonafide_ref/{spk_id}/{spk_id}_01.wav",
                    "seed": 100,
                    "duration_sec": 4.0,
                    "transcript": text,
                }
                mock_records.append(rec)

        spoof_manifest_df = pd.DataFrame(mock_records)
        spoof_manifest_csv = manifests_dir / "spoof_manifest.csv"
        spoof_manifest_df.to_csv(spoof_manifest_csv, index=False, encoding="utf-8")
        print(f"✅ Đã tạo mock spoof_manifest.csv tại: {spoof_manifest_csv}")
        return mock_records

    # Production execution via SPK_test pipeline
    if spk_test_src not in sys.path:
        sys.path.insert(0, spk_test_src)

    try:
        from vitruevoice.batch_processor import BatchDatasetProcessor
        from vitruevoice.pipeline import PipelineMode, ViTrueVoiceDualPipeline
        from vitruevoice.evaluator import MultiGateEvaluator
    except ImportError as e:
        print(f"❌ Không thể nạp module vitruevoice từ {spk_test_src}: {e}", file=sys.stderr)
        return []

    p_mode = getattr(PipelineMode, mode.upper(), PipelineMode.ADAPTIVE)
    import torch
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    evaluator = MultiGateEvaluator(device=device)
    pipeline = ViTrueVoiceDualPipeline(device=device, evaluator=evaluator)
    processor = BatchDatasetProcessor(pipeline=pipeline, evaluator=evaluator, device=device)
    all_manifest_records = []

    for spk_dir in sorted(raw_dir.glob("SPK_*")):
        spk_id = spk_dir.name
        wav_files = sorted([f.as_posix() for f in spk_dir.glob("*.wav")])
        if not wav_files:
            continue

        ref_stems = {f.stem for f in (ref_dir / spk_id).glob("*.wav")}
        spk_df = bonafide_df[bonafide_df["speaker_id"] == spk_id]
        non_ref_df = spk_df[~spk_df["utt_id"].isin(ref_stems)]
        spk_prompts = non_ref_df[non_ref_df["transcript"].notna()]["transcript"].tolist()

        out_synth_dir = spoof_f5_dir / spk_id
        records = processor.process_speaker(
            speaker_id=spk_id,
            speaker_wav_files=wav_files,
            prompts=spk_prompts,
            out_synth_dir=out_synth_dir,
            mode=p_mode,
            apply_telephony=True,
        )

        for r in records:
            if r.engine_name == "VieNeu-TTS":
                src_file = Path(r.audio_path)
                target_dest = spoof_vieneu_dir / spk_id / src_file.name
                target_dest.parent.mkdir(parents=True, exist_ok=True)
                if src_file.exists():
                    src_file.replace(target_dest)
                    r.audio_path = target_dest.as_posix()

        all_manifest_records.extend(records)

    out_spoof_csv = manifests_dir / "spoof_manifest.csv"
    BatchDatasetProcessor.export_manifest_csv(all_manifest_records, str(out_spoof_csv))
    print(f"✅ Đã hoàn thành sinh batch spoof -> {out_spoof_csv}")
    return all_manifest_records


def generate_spoof_sample(
    engine: str,
    ref_audio: str | Path,
    gen_text: str,
    output_path: str | Path,
    ref_text: Optional[str] = None,
    mock: bool = False,
) -> bool:
    """Generate a spoof audio sample using specified TTS engine.

    Args:
        engine: 'f5tts', 'vieneu', 'unseen', or 'mock'.
        ref_audio: Path to clean 3-5s reference speech.
        gen_text: Target fraudulent / impersonation text.
        output_path: Output .wav file path.
        ref_text: Transcript of reference audio (required for F5-TTS).
        mock: If True, writes dummy 4s sine wave for testing environments.

    Returns:
        True if generation and validation succeeded, False otherwise.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    clean_prompt = sanitize_prompt(gen_text)

    if mock:
        sr = 16000
        t = np.linspace(0, 4.0, int(sr * 4.0), endpoint=False)
        dummy_wav = (0.2 * np.sin(2 * np.pi * 350 * t)).astype(np.float32)
        sf.write(str(out_file), dummy_wav, sr)
        return True

    if engine == "f5tts":
        cmd = [
            "f5-tts_infer-cli",
            "--model", "F5TTS_Base",
            "--ref_audio", str(ref_audio),
            "--ref_text", ref_text or "",
            "--gen_text", clean_prompt,
            "--speed", "1.0",
            "--vocoder_name", "vocos",
            "--output_file", str(out_file),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Lỗi sinh F5-TTS: {result.stderr}", file=sys.stderr)
            return False

    elif engine == "vieneu":
        try:
            from vieneu import Vieneu
            tts = Vieneu(mode="v3turbo")
            tts.infer(text=clean_prompt, ref_audio=str(ref_audio), output_file=str(out_file))
        except ImportError:
            print("⚠️ Thư viện ViNeu-TTS chưa được cài đặt trong môi trường này.", file=sys.stderr)
            return False

    elif engine == "unseen":
        print(f"ℹ️ Chế độ Unseen tool (RVC / alternative TTS) cho: {out_file.name}")
        return False
    else:
        raise ValueError(f"Unknown engine: {engine}")

    if not out_file.exists():
        return False

    duration = get_audio_file_duration(out_file)
    if not validate_audio_duration(duration, min_sec=1.0, max_sec=30.0):
        print(f"⚠️ Mẫu sinh ra có độ dài không hợp lệ ({duration:.2f}s). Đang xóa bỏ.")
        out_file.unlink(missing_ok=True)
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic voice samples using F5-TTS or VieNeu-TTS.")
    parser.add_argument("--engine", type=str, choices=["f5tts", "vieneu", "unseen", "mock"], default="mock")
    parser.add_argument("--ref_audio", type=str, default="", help="Path to clean 3-5s reference audio")
    parser.add_argument("--gen_text", type=str, default="", help="Text to synthesize")
    parser.add_argument("--ref_text", type=str, default="", help="Transcript of reference audio")
    parser.add_argument("--output_path", type=str, default="", help="Target output wav path")
    parser.add_argument("--mock", action="store_true", help="Generate mock sample for local unit testing")
    parser.add_argument("--preprocess_only", action="store_true", help="Preprocess bonafide audio and generate bonafide_manifest.csv")
    parser.add_argument("--batch", action="store_true", help="Run batch spoof generation across speakers")
    parser.add_argument("--mode", type=str, default="ADAPTIVE", choices=["ADAPTIVE", "BEST_QUALITY", "F5_FIRST", "VIENEU_FIRST"])
    parser.add_argument("--data_dir", type=str, default="data", help="Root data directory")

    args = parser.parse_args()

    if args.preprocess_only:
        preprocess_bonafide_batch(
            src_spk_dirs=[Path(f"SPK_{i:04d}") for i in [1, 4, 5, 6, 7]],
            data_dir=args.data_dir,
        )
        return

    if args.batch:
        run_batch(data_dir=args.data_dir, mode=args.mode, mock=args.mock)
        return

    if not args.ref_audio or not args.gen_text or not args.output_path:
        parser.print_help()
        sys.exit(1)

    success = generate_spoof_sample(
        engine=args.engine,
        ref_audio=args.ref_audio,
        gen_text=args.gen_text,
        output_path=args.output_path,
        ref_text=args.ref_text,
        mock=args.mock or (args.engine == "mock"),
    )

    if success:
        print(f"✅ Đã sinh mẫu giả thành công tại: {args.output_path}")
    else:
        print("❌ Quá trình sinh mẫu thất bại.")
        sys.exit(1)


if __name__ == "__main__":
    main()
