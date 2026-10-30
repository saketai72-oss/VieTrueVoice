"""TDD tests for Zalo paired dataset and manifest generator (Pha 2 & Pha 4).

Verifies:
- Base utterance extraction (base_utt)
- Paired row generation for Profile A (aac_zalo_76k) and Profile B (opus_zalo_24k)
- Zero data leakage (speaker-disjoint, text-disjoint, base_utt-disjoint across splits)
- Strict exclusion of SPK_xxxx and VieNeu-TTS from Train/Dev
"""

from __future__ import annotations
import pandas as pd
import pytest

from scripts.generate_zalo_paired_manifests import (
    derive_base_utt,
    generate_paired_manifest,
    validate_split_leakage,
)


def test_derive_base_utt():
    assert derive_base_utt("common_voice_vi_21833213_clean") == "common_voice_vi_21833213"
    assert derive_base_utt("common_voice_vi_21833213_g711") == "common_voice_vi_21833213"
    assert derive_base_utt("common_voice_vi_21833213_amrnb") == "common_voice_vi_21833213"
    assert derive_base_utt("VIVOSDEV01_R002") == "VIVOSDEV01_R002"
    assert derive_base_utt("VIVOSDEV01_R002_clean") == "VIVOSDEV01_R002"
    assert derive_base_utt("SPK_0001_01") == "SPK_0001_01"


def test_generate_paired_manifest_structure():
    df_sample = pd.DataFrame([
        {
            "utt_id": "VIVOSDEV01_R002_clean",
            "audio_path": "data/raw/VIVOSDEV01/VIVOSDEV01_R002.wav",
            "speaker_id": "VIVOSDEV01",
            "source": "vivos",
            "label": "bonafide",
            "role": "eval",
            "tts_generator": "none",
            "codec": "clean_16khz",
            "pre_codec": "clean",
            "split": "dev",
            "duration_sec": 4.2,
            "transcript": "xin chào bạn",
            "raw_wer": 0.0,
            "raw_cer": 0.0,
            "ecapa_sim": 1.0,
            "wavlm_sim": 1.0,
            "derived_tier": "tier0_bonafide",
            "seed": 0,
        }
    ])

    paired = generate_paired_manifest(df_sample, generate_audio=False)
    # Original + 2 proxies (aac_zalo_76k and opus_zalo_24k)
    assert len(paired) == 3
    codecs = paired["codec"].tolist()
    assert "clean_16khz" in codecs
    assert "aac_zalo_76k" in codecs
    assert "opus_zalo_24k" in codecs

    # All share the same base_utt and split
    assert paired["base_utt"].nunique() == 1
    assert paired["base_utt"].iloc[0] == "VIVOSDEV01_R002"
    assert (paired["split"] == "dev").all()
    assert (paired["speaker_id"] == "VIVOSDEV01").all()


def test_validate_split_leakage_clean():
    train_df = pd.DataFrame({
        "speaker_id": ["SPK_A", "SPK_B"],
        "transcript": ["câu một", "câu hai"],
        "base_utt": ["utt_1", "utt_2"],
        "tts_generator": ["none", "f5tts"],
    })
    dev_df = pd.DataFrame({
        "speaker_id": ["SPK_C"],
        "transcript": ["câu ba"],
        "base_utt": ["utt_3"],
        "tts_generator": ["f5tts"],
    })
    test_df = pd.DataFrame({
        "speaker_id": ["SPK_D"],
        "transcript": ["câu bốn"],
        "base_utt": ["utt_4"],
        "tts_generator": ["vieneu"],
    })

    # Should pass without raising
    validate_split_leakage(train_df, dev_df, test_df)


def test_validate_split_leakage_rejects_spk_xxxx_in_train_or_dev():
    train_bad = pd.DataFrame({
        "speaker_id": ["SPK_0001", "SPK_B"],
        "transcript": ["câu một", "câu hai"],
        "base_utt": ["utt_1", "utt_2"],
        "tts_generator": ["none", "f5tts"],
    })
    dev_good = pd.DataFrame({
        "speaker_id": ["SPK_C"],
        "transcript": ["câu ba"],
        "base_utt": ["utt_3"],
        "tts_generator": ["f5tts"],
    })
    test_good = pd.DataFrame({
        "speaker_id": ["SPK_D"],
        "transcript": ["câu bốn"],
        "base_utt": ["utt_4"],
        "tts_generator": ["vieneu"],
    })

    with pytest.raises(ValueError, match="SPK_xxxx"):
        validate_split_leakage(train_bad, dev_good, test_good)


def test_validate_split_leakage_rejects_vieneu_in_train():
    train_bad = pd.DataFrame({
        "speaker_id": ["SPK_A", "SPK_B"],
        "transcript": ["câu một", "câu hai"],
        "base_utt": ["utt_1", "utt_2"],
        "tts_generator": ["none", "vieneu_turbo"],
    })
    dev_good = pd.DataFrame({
        "speaker_id": ["SPK_C"],
        "transcript": ["câu ba"],
        "base_utt": ["utt_3"],
        "tts_generator": ["f5tts"],
    })
    test_good = pd.DataFrame({
        "speaker_id": ["SPK_D"],
        "transcript": ["câu bốn"],
        "base_utt": ["utt_4"],
        "tts_generator": ["vieneu"],
    })

    with pytest.raises(ValueError, match="VieNeu"):
        validate_split_leakage(train_bad, dev_good, test_good)


def test_validate_split_leakage_rejects_speaker_overlap():
    train_df = pd.DataFrame({
        "speaker_id": ["SPK_A", "SPK_B"],
        "transcript": ["câu một", "câu hai"],
        "base_utt": ["utt_1", "utt_2"],
        "tts_generator": ["none", "f5tts"],
    })
    dev_leak = pd.DataFrame({
        "speaker_id": ["SPK_A"],  # Overlap with train!
        "transcript": ["câu ba"],
        "base_utt": ["utt_3"],
        "tts_generator": ["f5tts"],
    })
    test_df = pd.DataFrame({
        "speaker_id": ["SPK_D"],
        "transcript": ["câu bốn"],
        "base_utt": ["utt_4"],
        "tts_generator": ["none"],
    })

    with pytest.raises(ValueError, match="Speaker overlap"):
        validate_split_leakage(train_df, dev_leak, test_df)
