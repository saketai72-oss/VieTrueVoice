from pathlib import Path
import pytest
from scripts.generate_spoof import sanitize_prompt, validate_audio_duration


def test_sanitize_prompt():
    """Verify input prompt is lowercased and stripped of excessive whitespace."""
    raw = "  ALO MẸ ƠI, chuyển gấp cho con 10 triệu vào số tài khoản này nhé!   "
    clean = sanitize_prompt(raw, max_chars=250)
    assert clean == "alo mẹ ơi, chuyển gấp cho con 10 triệu vào số tài khoản này nhé!"
    assert len(clean) <= 250


def test_sanitize_prompt_max_chars():
    """Verify prompt exceeding max_chars is safely truncated."""
    long_text = "chuyển khoản " * 30  # > 250 chars
    clean = sanitize_prompt(long_text, max_chars=250)
    assert len(clean) <= 250


def test_validate_audio_duration():
    """Verify duration bounds checking (3s - 15s accepted, <1s or >30s rejected)."""
    assert validate_audio_duration(5.5, min_sec=1.0, max_sec=30.0) is True
    assert validate_audio_duration(0.5, min_sec=1.0, max_sec=30.0) is False
    assert validate_audio_duration(35.0, min_sec=1.0, max_sec=30.0) is False


def test_load_and_trim_audio(tmp_path):
    """Verify audio is loaded, converted to 16kHz mono, and silence is trimmed."""
    import numpy as np
    import soundfile as sf
    from scripts.generate_spoof import load_and_trim_audio

    sr = 16000
    silence = np.zeros(int(0.5 * sr), dtype=np.float32)
    t = np.linspace(0, 1.0, int(1.0 * sr), endpoint=False)
    tone = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    signal = np.concatenate([silence, tone, silence])
    test_wav = tmp_path / "test.wav"
    sf.write(str(test_wav), signal, sr)

    trimmed, out_sr = load_and_trim_audio(test_wav, target_sr=16000, top_db=30)
    assert out_sr == 16000
    assert len(trimmed) < len(signal)
    assert len(trimmed) >= int(0.9 * sr)


def test_preprocess_bonafide_batch(tmp_path):
    """Verify batch bonafide preprocessing generates raw, ref, and 17-col manifest."""
    import numpy as np
    import soundfile as sf
    import pandas as pd
    from scripts.generate_spoof import preprocess_bonafide_batch

    spk_dir = tmp_path / "SPK_0001"
    spk_dir.mkdir(parents=True)
    sr = 16000
    t = np.linspace(0, 2.0, int(2.0 * sr), endpoint=False)
    wav = (0.2 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
    sf.write(str(spk_dir / "SPK_0001_01.wav"), wav, sr)
    sf.write(str(spk_dir / "SPK_0001_06.wav"), wav, sr)

    meta_csv = tmp_path / "metadata.csv"
    pd.DataFrame([
        {"speaker_id": "SPK_0001", "filename": "SPK_0001_01.wav", "is_ref": True, "transcript": "Câu một"},
        {"speaker_id": "SPK_0001", "filename": "SPK_0001_06.wav", "is_ref": False, "transcript": "Câu sáu"}
    ]).to_csv(meta_csv, index=False)

    data_dir = tmp_path / "data"
    manifest_df = preprocess_bonafide_batch(
        src_spk_dirs=[spk_dir],
        data_dir=data_dir,
        metadata_csv_path=meta_csv
    )

    assert len(manifest_df) == 2
    assert (data_dir / "raw" / "SPK_0001" / "SPK_0001_01.wav").exists()
    assert (data_dir / "raw" / "SPK_0001" / "SPK_0001_06.wav").exists()
    assert (data_dir / "bonafide_ref" / "SPK_0001" / "SPK_0001_01.wav").exists()
    assert not (data_dir / "bonafide_ref" / "SPK_0001" / "SPK_0001_06.wav").exists()
    assert (data_dir / "manifests" / "bonafide_manifest.csv").exists()
    assert "utt_id" in manifest_df.columns
    assert "duration_sec" in manifest_df.columns

