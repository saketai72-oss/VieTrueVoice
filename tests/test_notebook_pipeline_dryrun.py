"""Dry-run end-to-end simulation of train.ipynb pipeline logic.

Validates that:
1. ManifestRecord has all required fields and methods.
2. The _rget helper handles all legacy and new record types safely.
3. Audio path relative conversions and transcript extractions work cleanly.
4. Paired triplets maintain exact 1:1:1 integer equality.
5. All 18 manifest columns match across bonafide and spoof.
6. Dynamic loss weights formula and JSON serialization succeed without NaNs.
"""

import dataclasses
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import torch

from vitruevoice.base import ManifestRecord
from vitruevoice.text_utils import normalize_for_eval, fix_tone_token, has_digits

MANIFEST_COLUMNS = [
    "utt_id", "audio_path", "speaker_id", "source", "label", "role",
    "tts_generator", "codec", "pre_codec", "split", "duration_sec", "transcript",
    "raw_wer", "raw_cer", "ecapa_sim", "wavlm_sim", "derived_tier", "seed",
]


def _rget(obj, names, default=None):
    """Helper used in Cell 4 to dynamically extract fields."""
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if v is not None:
                return v
    if isinstance(obj, dict):
        for n in names:
            if obj.get(n) is not None:
                return obj[n]
    return default


def test_manifest_record_and_rget():
    """Verify ManifestRecord fields and _rget behavior."""
    rec = ManifestRecord(
        audio_path="data/spoof_f5tts/SPK_0001/SPK_0001_prompt_000.wav",
        speaker_id="SPK_0001",
        is_bonafide=False,
        ecapa_sim=0.75,
        raw_wer=0.08,
        raw_cer=0.03,
        source="vivos",
        role="eval",
        codec="clean_16khz",
        transcript="xin chào tôi là người nhà",
        tts_generator="F5-TTS-Vietnamese",
    )

    # 1. Inspect dataclass fields
    fields = dataclasses.asdict(rec)
    assert "transcript" in fields
    assert fields["transcript"] == "xin chào tôi là người nhà"
    assert rec.derive_attack_tier() == "Tier 1 (Strong)"

    # 2. Test _rget on dataclass
    assert _rget(rec, ["transcript", "text"]) == "xin chào tôi là người nhà"
    assert _rget(rec, ["tts_generator", "engine"]) == "F5-TTS-Vietnamese"
    assert _rget(rec, ["nonexistent"], default="default_val") == "default_val"

    # 3. Test _rget on dict
    d = {"prompt_text": "câu nói thử nghiệm", "engine": "VieNeu-TTS"}
    assert _rget(d, ["transcript", "prompt_text"]) == "câu nói thử nghiệm"
    assert _rget(d, ["tts_generator", "engine"]) == "VieNeu-TTS"


def test_cell4_serialization_simulation(tmp_path):
    """Simulate exact Cell 4 record processing loop."""
    working_dir = tmp_path
    candidate_prompts = [
        "câu prompt số không",
        "câu prompt số một",
    ]

    # Create dummy wav files on disk
    wav_dir = working_dir / "data" / "spoof_f5tts" / "SPK_0001"
    wav_dir.mkdir(parents=True, exist_ok=True)
    w1 = wav_dir / "SPK_0001_prompt_000.wav"
    w2 = wav_dir / "SPK_0001_prompt_000_g711.wav"
    w3 = wav_dir / "SPK_0001_prompt_000_amrnb.wav"
    for w in [w1, w2, w3]:
        w.write_bytes(b"RIFF" + b"\x00" * 36)

    records = [
        ManifestRecord(
            audio_path=str(w1),
            speaker_id="SPK_0001",
            is_bonafide=False,
            ecapa_sim=0.72,
            raw_wer=0.05,
            raw_cer=0.02,
            codec="clean_16khz",
            transcript="câu prompt số không",
            tts_generator="F5-TTS",
        ),
        ManifestRecord(
            audio_path=str(w2),
            speaker_id="SPK_0001",
            is_bonafide=False,
            ecapa_sim=0.68,
            raw_wer=0.05,
            raw_cer=0.02,
            codec="g711_alaw",
            transcript="câu prompt số không",
            tts_generator="F5-TTS",
        ),
        ManifestRecord(
            audio_path=str(w3),
            speaker_id="SPK_0001",
            is_bonafide=False,
            ecapa_sim=0.65,
            raw_wer=0.05,
            raw_cer=0.02,
            codec="amr_nb",
            transcript="câu prompt số không",
            tts_generator="F5-TTS",
        ),
    ]

    spk_source = "vivos"
    pre_codec_val = "none"
    spk_split = "dev"

    serialized = []
    for i, r in enumerate(records):
        w_path = Path(r.audio_path)
        if not w_path.is_absolute():
            w_path = working_dir / w_path

        try:
            rel_path = w_path.relative_to(working_dir).as_posix()
        except ValueError:
            rel_path = str(r.audio_path)

        t_val = _rget(r, ["transcript", "text", "prompt_text", "prompt", "gen_text"], "")
        if not t_val and "_prompt_" in w_path.stem:
            try:
                p_idx = int(w_path.stem.split("_prompt_")[1].split("_")[0])
                if 0 <= p_idx < len(candidate_prompts):
                    t_val = candidate_prompts[p_idx]
            except Exception:
                pass

        rec_dict = {
            "utt_id": w_path.stem,
            "audio_path": rel_path,
            "speaker_id": r.speaker_id,
            "source": spk_source,
            "label": "spoof",
            "role": "eval",
            "tts_generator": _rget(r, ["tts_generator", "engine_name", "engine"], "F5-TTS"),
            "codec": r.codec,
            "pre_codec": pre_codec_val,
            "split": spk_split,
            "duration_sec": 4.0,
            "transcript": t_val,
            "raw_wer": _rget(r, ["raw_wer"]),
            "raw_cer": _rget(r, ["raw_cer"]),
            "ecapa_sim": _rget(r, ["ecapa_sim"]),
            "wavlm_sim": _rget(r, ["wavlm_sim"]),
            "derived_tier": r.derive_attack_tier(),
            "seed": _rget(r, ["seed"], 100),
        }
        serialized.append(rec_dict)

    assert len(serialized) == 3
    df = pd.DataFrame(serialized)
    assert list(df.columns) == MANIFEST_COLUMNS
    assert df["transcript"].eq("").sum() == 0
    assert set(df["codec"]) == {"clean_16khz", "g711_alaw", "amr_nb"}
    assert df["audio_path"].str.startswith("data/spoof_f5tts/").all()


def test_cell5_manifest_and_loss_weights_simulation(tmp_path):
    """Simulate exact Cell 5 manifest splitting and loss weights calculation."""
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create bona fide records (with paired triplets)
    bonafide_rows = []
    for i in range(10):
        base_id = f"bona_{i:03d}"
        for c in ["clean_16khz", "g711_alaw", "amr_nb"]:
            bonafide_rows.append({
                "utt_id": f"{base_id}_{c}",
                "audio_path": f"data/raw/SPK_0001/{base_id}_{c}.wav",
                "speaker_id": "SPK_0001",
                "source": "vivos",
                "label": "bonafide",
                "role": "eval",
                "tts_generator": "none",
                "codec": c,
                "pre_codec": "none",
                "split": "train",
                "duration_sec": 3.5,
                "transcript": f"câu nói bona {i}",
                "raw_wer": None,
                "raw_cer": None,
                "ecapa_sim": None,
                "wavlm_sim": None,
                "derived_tier": "BonaFide",
                "seed": 100,
            })

    # 2. Create spoof records (with paired triplets, 2x ratio)
    spoof_rows = []
    for i in range(20):
        base_id = f"spoof_{i:03d}"
        for c in ["clean_16khz", "g711_alaw", "amr_nb"]:
            spoof_rows.append({
                "utt_id": f"{base_id}_{c}",
                "audio_path": f"data/spoof_f5tts/SPK_0001/{base_id}_{c}.wav",
                "speaker_id": "SPK_0001",
                "source": "vivos",
                "label": "spoof",
                "role": "eval",
                "tts_generator": "F5-TTS",
                "codec": c,
                "pre_codec": "none",
                "split": "train",
                "duration_sec": 4.0,
                "transcript": f"câu nói spoof {i}",
                "raw_wer": 0.05,
                "raw_cer": 0.02,
                "ecapa_sim": 0.70,
                "wavlm_sim": 0.85,
                "derived_tier": "Tier 1 (Strong)",
                "seed": 100,
            })

    full_df = pd.DataFrame(bonafide_rows + spoof_rows)
    assert list(full_df.columns) == MANIFEST_COLUMNS

    # Exact paired triplets integer equality
    eval_df = full_df[full_df["role"] == "eval"]
    count_clean = (eval_df["codec"] == "clean_16khz").sum()
    count_g711 = (eval_df["codec"] == "g711_alaw").sum()
    count_amr = (eval_df["codec"] == "amr_nb").sum()
    assert count_clean == count_g711 == count_amr == 30

    # Calculate dynamic loss weights
    train_df = full_df[full_df["split"] == "train"].copy().reset_index(drop=True)
    labels_num = train_df["label"].astype(str).str.lower().map({"spoof": 0, "bonafide": 1}).values
    assert not np.isnan(labels_num).any()
    counts = np.bincount(labels_num, minlength=2)
    assert counts.min() > 0

    total_train = len(labels_num)
    raw_w = total_train / (2.0 * counts)
    norm_w = raw_w / np.sum(raw_w)

    assert pytest.approx(norm_w[0], abs=0.01) == 0.3333
    assert pytest.approx(norm_w[1], abs=0.01) == 0.6667

    # JSON save check
    loss_weights_dict = {
        "spoof": round(float(norm_w[0]), 4),
        "bonafide": round(float(norm_w[1]), 4),
        "counts": {"spoof": int(counts[0]), "bonafide": int(counts[1])},
        "total_train": int(total_train),
    }
    json_path = manifests_dir / "loss_weights.json"
    json_path.write_text(json.dumps(loss_weights_dict, indent=2), encoding="utf-8")
    assert json_path.exists()
    loaded_w = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded_w["spoof"] == 0.3333
    assert loaded_w["bonafide"] == 0.6667
