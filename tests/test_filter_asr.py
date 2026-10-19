import pandas as pd
import pytest

from scripts.filter_asr_wer import compute_word_error_rate, filter_manifest_by_wer


def test_compute_word_error_rate_exact_match():
    """Identical strings should have WER = 0.0."""
    ref = "alo mẹ ơi chuyển tiền cho con"
    hyp = "alo mẹ ơi chuyển tiền cho con"
    assert compute_word_error_rate(ref, hyp) == 0.0


def test_compute_word_error_rate_substitutions_and_deletions():
    """Verify Levenshtein word distance calculation."""
    ref = "chuyển gấp cho con mười triệu"  # 6 words
    # 'mười lăm' has 1 substitution ('triệu' -> 'lăm') and 1 insertion
    hyp = "chuyển gấp cho con mười lăm"
    wer = compute_word_error_rate(ref, hyp)
    assert 0.0 < wer <= 0.5


def test_compute_word_error_rate_case_and_punctuation():
    """Punctuation and casing differences should be normalized before computing WER."""
    ref = "Alo mẹ ơi, chuyển tiền nhé!"
    hyp = "alo me oi chuyển tiền nhé"
    # Even if accents vary slightly or punctuation exists, punctuation shouldn't artificially inflate WER
    ref_norm = "alo mẹ ơi chuyển tiền nhé"
    assert compute_word_error_rate("Alo mẹ ơi, chuyển tiền nhé!", "alo mẹ ơi chuyển tiền nhé") == 0.0


def test_filter_manifest_by_wer():
    """Verify filtering removes samples exceeding max_wer threshold."""
    df = pd.DataFrame([
        {
            "audio_path": "sample1.wav",
            "ref_text": "chuyển tiền ngay nhé",
            "hyp_text": "chuyển tiền ngay nhé",
            "speaker_id": "SPK_0001",
            "label": 0,
        },
        {
            "audio_path": "sample2.wav",
            "ref_text": "chuyển tiền ngay nhé",
            "hyp_text": "hoàn toàn sai không giống chữ nào hết cả",
            "speaker_id": "SPK_0002",
            "label": 0,
        },
    ])

    kept_df, rejected_df = filter_manifest_by_wer(df, max_wer=0.35)
    assert len(kept_df) == 1
    assert kept_df.iloc[0]["audio_path"] == "sample1.wav"
    assert len(rejected_df) == 1
    assert rejected_df.iloc[0]["audio_path"] == "sample2.wav"
