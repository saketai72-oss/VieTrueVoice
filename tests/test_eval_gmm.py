import numpy as np
import pandas as pd
import pytest
from scripts.eval_gmm import (
    normalize_labels, to_long, fix_length, evaluate_subset, build_table,
)


def test_normalize_labels_mixed_formats():
    out = normalize_labels(pd.Series(["bonafide", "spoof", "1", "0", "Bona_Fide"]))
    assert out.tolist() == [1, 0, 1, 0, 1]


def test_normalize_labels_rejects_unknown():
    with pytest.raises(ValueError):
        normalize_labels(pd.Series(["bonafide", "???"]))


def test_fix_length_pad_and_crop():
    assert len(fix_length(np.ones(1000, dtype=np.float32))) == 64000
    assert len(fix_length(np.ones(100000, dtype=np.float32))) == 64000


def test_fix_length_rejects_empty():
    with pytest.raises(ValueError):
        fix_length(np.array([], dtype=np.float32))


def test_to_long_wide_to_long():
    df = pd.DataFrame({
        "label": ["bonafide", "spoof"], "speaker_id": ["a", "b"],
        "tts": ["none", "f5"], "clean": ["c1.wav", "c2.wav"],
        "g711": ["g1.wav", "g2.wav"],
    })
    long = to_long(df, {"clean": "clean", "g711": "g711"},
                   ["label", "speaker_id", "tts"])
    assert len(long) == 4
    assert set(long["condition"]) == {"clean", "g711"}
    assert {"path", "label", "speaker_id", "tts"} <= set(long.columns)


def test_evaluate_subset_perfect_separation():
    labels = np.array([1, 1, 1, 0, 0, 0])
    scores = np.array([0.9, 0.8, 0.7, 0.3, 0.2, 0.1])
    spk = np.array(list("aabbcc"))
    r = evaluate_subset(scores, labels, spk, n_boot=20, seed=0)
    assert r["eer"] == pytest.approx(0.0, abs=1e-9)
    assert r["bona_rejected"] == 0 and r["spoof_accepted"] == 0
    assert r["n_bona"] == 3 and r["n_spoof"] == 3
    assert r["eer_ci_lo"] <= r["eer"] <= r["eer_ci_hi"]


def _synthetic(seed=0, n_spk=20, per_spk=10):
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_spk):
        for _ in range(per_spk):
            rows.append(("bonafide", f"s{s}", "none", "clean",
                         rng.normal(1.0, 0.5)))
            rows.append(("spoof", f"s{s}", "easy_tts", "clean",
                         rng.normal(-3.0, 0.5)))
            rows.append(("spoof", f"s{s}", "hard_tts", "clean",
                         rng.normal(0.8, 1.0)))
    return pd.DataFrame(rows, columns=["label", "speaker_id", "tts",
                                       "condition", "score"])


def test_build_table_tts_breakdown_shares_bonafide():
    df = _synthetic()
    df["label"] = normalize_labels(df["label"])
    tab = build_table(df, split="test", n_boot=20, seed=0)
    clean = tab[tab["condition"] == "clean"].set_index("tts")
    assert {"all", "easy_tts", "hard_tts"} <= set(clean.index)
    assert clean.loc["easy_tts", "eer"] < clean.loc["hard_tts", "eer"]
    # mọi dòng đều dùng chung toàn bộ bonafide của điều kiện
    assert clean.loc["easy_tts", "n_bona"] == clean.loc["hard_tts", "n_bona"] == 200
    assert (tab["split"] == "test").all()


def test_build_table_skips_subset_without_both_classes():
    df = _synthetic().iloc[:0]
    tab = build_table(df.assign(label=[]), split="x", n_boot=5, seed=0)
    assert len(tab) == 0
