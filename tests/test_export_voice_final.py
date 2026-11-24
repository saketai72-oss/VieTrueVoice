"""Unit tests for scripts/export_voice_final_dataset.py (V8.1 1:1 OmniVoice_CFM export)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf

from scripts import export_voice_final_dataset as evf


def _write_dummy_wav(path: Path, sr: int = 16000, dur_s: float = 0.6) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    y = np.zeros(int(sr * dur_s), dtype=np.float32)
    sf.write(str(path), y, sr, subtype="PCM_16")


def test_v8_omnivoice_export_1_to_1_parity_and_legacy_cleanup(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    dest = tmp_path / "Voice_Final"

    speakers = ["VIVOSSPK01", "CV_abcd1234", "SPK_0001", "SPK_0003"]
    codecs = ["", "_g711", "_amrnb", "_aac_zalo", "_opus_zalo"]

    # Create symmetric VieNeu (v7 Seen) and OmniVoice V8.1 (v8 Seen) corpora
    for spk in speakers:
        for suf in codecs:
            fname = f"{spk}_prompt_000{suf}.wav"
            _write_dummy_wav(root / "data/spoof_vieneu" / spk / fname)
            _write_dummy_wav(root / "data/spoof_omnivoice_v8" / spk / fname)

    # Create legacy incomplete directory that MUST NOT be exported to v8/Seen/OmniVoice_CFM
    _write_dummy_wav(root / "data/spoof_train/omnivoice/VIVOSSPK99/VIVOSSPK99_omnivoice_000.wav")

    # Seed stale legacy V8.0 artifacts inside destination before export
    for legacy_sub in ("Train_55Spk", "Dev_Eval_15Spk", "SPK_Volunteers_5SPK"):
        _write_dummy_wav(dest / "spoof/v8/Seen/OmniVoice_CFM" / legacy_sub / "OLD/old.wav")
    _write_dummy_wav(dest / "spoof/v8/Seen/OmniVoice_CFM/VIVOS/VIVOSSPK01/stale.wav")

    evf.main(root=root, dest_root=dest)

    v7_vn_dir = dest / "spoof/v7/Seen/VieNeu_TTS"
    v8_om_dir = dest / "spoof/v8/Seen/OmniVoice_CFM"

    v7_rels = sorted(p.relative_to(v7_vn_dir).as_posix() for p in v7_vn_dir.rglob("*.wav"))
    v8_rels = sorted(p.relative_to(v8_om_dir).as_posix() for p in v8_om_dir.rglob("*.wav"))
    assert v8_rels == v7_rels
    assert len(v8_rels) == len(speakers) * len(codecs)

    for legacy_sub in ("Train_55Spk", "Dev_Eval_15Spk", "SPK_Volunteers_5SPK"):
        assert not (v8_om_dir / legacy_sub).exists()
    assert not (v8_om_dir / "VIVOS/VIVOSSPK01/stale.wav").exists()

    df = pd.read_csv(dest / "VOICE_FINAL_MANIFEST.csv")
    v8_rows = df[df["category"] == "spoof/v8/Seen/OmniVoice_CFM"]
    assert len(v8_rows) == 20
    assert (v8_rows["tts_generator"] == "OmniVoice").all()
    assert (v8_rows["version"] == "v8").all()
    assert (v8_rows["split_role"] == "seen").all()

    # Verify SHA-256 matches exported files on disk
    for _, row in v8_rows.iterrows():
        fp = dest / str(row["rel_path"])
        assert fp.exists()
        assert row["sha256_hash"] == hashlib.sha256(fp.read_bytes()).hexdigest()

    readme_text = (dest / "README_NGHIEM_THU.md").read_text(encoding="utf-8")
    assert "V8.1" in readme_text
    assert "Train_55Spk" not in readme_text
    assert "SPK_0001` 5" in readme_text
