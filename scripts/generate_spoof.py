"""Automated spoofed audio generation script for ViTrueVoice.

Integrates F5-TTS-Vietnamese, VieNeu-TTS, and Unseen tool pipelines.
Implements prompt normalization and duration validation per Step 1.2 of PLAN.md.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional
import soundfile as sf


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
        import numpy as np
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
    parser.add_argument("--ref_audio", type=str, required=True, help="Path to clean 3-5s reference audio")
    parser.add_argument("--gen_text", type=str, required=True, help="Text to synthesize")
    parser.add_argument("--ref_text", type=str, default="", help="Transcript of reference audio")
    parser.add_argument("--output_path", type=str, required=True, help="Target output wav path")
    parser.add_argument("--mock", action="store_true", help="Generate mock sample for local unit testing")

    args = parser.parse_args()
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
