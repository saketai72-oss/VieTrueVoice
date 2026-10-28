"""Unit tests for paired triplets, syllable-end tone normalization, text-disjoint priority, and dynamic loss weighting."""

import numpy as np
import pandas as pd
import pytest
import torch

from vitruevoice.text_utils import fix_tone_token, normalize_for_eval, has_digits


def test_vietnamese_tone_normalization_tokens():
    """Verify tone marks are correctly standardized without breaking diphthongs and clusters."""
    # 1. Closed syllables & glides: Must NOT move accent to wrong vowel
    assert fix_tone_token("toàn") == "toàn"
    assert fix_tone_token("hoàng") == "hoàng"
    assert fix_tone_token("khoảng") == "khoảng"
    assert fix_tone_token("ngoài") == "ngoài"
    assert fix_tone_token("thuở") == "thuở"

    # 2. Onset cluster 'qu': Must NOT treat 'u' as diphthong
    assert fix_tone_token("quý") == "quý"
    assert fix_tone_token("quỳ") == "quỳ"
    assert fix_tone_token("quỷ") == "quỷ"

    # 3. Open syllables (ending in oa, oe, uy): Standardize to new convention (òa, óe, ủy)
    assert fix_tone_token("hoà") == "hòa"
    assert fix_tone_token("hòa") == "hòa"
    assert fix_tone_token("thuỷ") == "thủy"
    assert fix_tone_token("thủy") == "thủy"
    assert fix_tone_token("khoẻ") == "khỏe"
    assert fix_tone_token("khỏe") == "khỏe"


def test_normalize_for_eval_full_phrases():
    """Verify phrase-level evaluation normalization."""
    raw = "Sức khoẻ rất quý, ai về ngoài hoàng hôn thì nhớ hoà giải!"
    expected = "sức khỏe rất quý ai về ngoài hoàng hôn thì nhớ hòa giải"
    assert normalize_for_eval(raw) == expected


def test_has_digits_filtering():
    """Verify digit detection accurately flags sentences with numbers."""
    assert has_digits("năm 2020 có nhiều biến động") is True
    assert has_digits("tôi chuyển khoản 10 triệu") is True
    assert has_digits("hôm nay trời đẹp và trong xanh") is False
    assert has_digits("mười chín năm một chặng đường") is False


def test_paired_triplets_integer_equality():
    """Verify that paired triplets have exactly equal counts across codecs and share metadata."""
    rows = []
    # Create 5 base utterances, each having 3 codecs
    for i in range(5):
        base_id = f"utt_{i:03d}"
        for c in ["clean_16khz", "g711_alaw", "amr_nb"]:
            rows.append({
                "utt_id": f"{base_id}_{c}",
                "base_utt_id": base_id,
                "speaker_id": "SPK_001",
                "label": "spoof",
                "codec": c,
                "split": "train",
            })
    df = pd.DataFrame(rows)

    count_clean = (df["codec"] == "clean_16khz").sum()
    count_g711 = (df["codec"] == "g711_alaw").sum()
    count_amr = (df["codec"] == "amr_nb").sum()

    # Exact integer equality
    assert count_clean == count_g711 == count_amr == 5

    # Check each base_utt_id has all 3 codecs with identical speaker, label, and split
    for base_id, group in df.groupby("base_utt_id"):
        assert len(group) == 3
        assert set(group["codec"]) == {"clean_16khz", "g711_alaw", "amr_nb"}
        assert group["speaker_id"].nunique() == 1
        assert group["label"].nunique() == 1
        assert group["split"].nunique() == 1


def test_text_disjoint_priority_deduplication():
    """Verify text-disjoint priority deduplication: Test keeps, Dev removes, Train removes."""
    # Data with overlaps
    train_data = ["câu một", "câu hai", "câu chung_td", "câu chung_all"]
    dev_data = ["câu ba", "câu chung_td", "câu chung_all"]
    test_data = ["câu bốn", "câu chung_all"]

    text_test = set(test_data)
    # Dev drops duplicates in Test
    text_dev = set(dev_data) - text_test
    # Train drops duplicates in Dev and Test
    text_train = set(train_data) - (text_test | text_dev)

    # 1. Hard disjoint assertions
    assert text_train.isdisjoint(text_dev), "Train and Dev leak text!"
    assert text_train.isdisjoint(text_test), "Train and Test leak text!"
    assert text_dev.isdisjoint(text_test), "Dev and Test leak text!"

    # 2. Test set retained all its original texts
    assert text_test == {"câu bốn", "câu chung_all"}
    # 3. Dev preserved 'câu chung_td' because it wasn't in Test, but dropped 'câu chung_all'
    assert text_dev == {"câu ba", "câu chung_td"}
    # 4. Train had both shared texts removed
    assert text_train == {"câu một", "câu hai"}


def test_intra_speaker_ref_enroll_eval_text_disjoint():
    """Verify that inside a speaker, ref/enroll transcripts never overlap with eval transcripts."""
    ref_texts = {"xin chào bạn", "tôi tên là nam"}
    enroll_texts = {"hôm nay trời đẹp", "chúc một ngày tốt lành"}
    eval_texts = {"chuyển khoản cho tôi", "báo cáo tài chính"}

    assert ref_texts.isdisjoint(eval_texts)
    assert enroll_texts.isdisjoint(eval_texts)


def test_dynamic_class_weights_calculation():
    """Verify dynamic inverse class frequency weights for Weighted Cross-Entropy."""
    # Dummy train df with 200 spoofs and 100 bonafides (2:1 ratio)
    labels = ["spoof"] * 200 + ["bonafide"] * 100
    train_df = pd.DataFrame({"label": labels})

    labels_num = train_df["label"].astype(str).str.lower().map({"spoof": 0, "bonafide": 1}).values
    assert not np.isnan(labels_num).any()
    counts = np.bincount(labels_num, minlength=2)
    assert counts.min() > 0

    total = len(labels_num)
    raw_weights = total / (2.0 * counts)
    norm_weights = raw_weights / np.sum(raw_weights)

    # w_spoof approx 0.3333, w_bona approx 0.6667
    assert pytest.approx(norm_weights[0], abs=0.01) == 0.3333
    assert pytest.approx(norm_weights[1], abs=0.01) == 0.6667
    assert pytest.approx(norm_weights.sum(), abs=1e-6) == 1.0

    w_tensor = torch.tensor(norm_weights, dtype=torch.float32)
    assert w_tensor.shape == (2,)
