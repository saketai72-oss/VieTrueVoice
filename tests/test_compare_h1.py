import numpy as np
import pandas as pd
import pytest
from scripts.compare_h1 import (
    relative_reduction, build_h1, build_h2, to_markdown,
)


def _row(split, cond, tts, eer, lo=None, hi=None):
    return {"split": split, "condition": cond, "tts": tts, "eer": eer,
            "eer_ci_lo": eer - 0.01 if lo is None else lo,
            "eer_ci_hi": eer + 0.01 if hi is None else hi}


def test_relative_reduction_basic():
    assert relative_reduction(0.20, 0.10) == pytest.approx(50.0)
    assert relative_reduction(0.20, 0.30) == pytest.approx(-50.0)


def test_relative_reduction_tiny_baseline_is_nan():
    assert np.isnan(relative_reduction(0.0, 0.0))
    assert np.isnan(relative_reduction(1e-6, 0.0))
    assert np.isnan(relative_reduction(float("nan"), 0.1))


def test_h1_pass_when_all_compressed_conditions_reach_target():
    a = pd.DataFrame([_row("in_domain", "g711_alaw", "all", 0.20),
                      _row("in_domain", "amr_nb", "all", 0.30),
                      _row("in_domain", "clean_16khz", "all", 0.05)])
    b = pd.DataFrame([_row("in_domain", "g711_alaw", "all", 0.10),
                      _row("in_domain", "amr_nb", "all", 0.15),
                      _row("in_domain", "clean_16khz", "all", 0.05)])
    res = build_h1(a, b, compressed=["g711_alaw", "amr_nb"])
    assert set(res["condition"]) == {"g711_alaw", "amr_nb"}  # bỏ clean
    assert (res["verdict"] == "PASS").all()
    assert (res["split_verdict"] == "PASS").all()


def test_h1_fail_if_one_condition_below_target():
    a = pd.DataFrame([_row("t", "g711_alaw", "all", 0.20),
                      _row("t", "amr_nb", "all", 0.30)])
    b = pd.DataFrame([_row("t", "g711_alaw", "all", 0.10),
                      _row("t", "amr_nb", "all", 0.27)])
    res = build_h1(a, b, compressed=["g711_alaw", "amr_nb"]).set_index("condition")
    assert res.loc["g711_alaw", "verdict"] == "PASS"
    assert res.loc["amr_nb", "verdict"] == "FAIL"
    assert (res["split_verdict"] == "FAIL").all()


def test_h1_incomplete_when_condition_missing_in_b():
    a = pd.DataFrame([_row("t", "g711_alaw", "all", 0.20),
                      _row("t", "amr_nb", "all", 0.30)])
    b = pd.DataFrame([_row("t", "g711_alaw", "all", 0.10)])
    res = build_h1(a, b, compressed=["g711_alaw", "amr_nb"])
    assert (res["split_verdict"] == "INCOMPLETE").all()


def test_h1_na_when_baseline_near_zero():
    a = pd.DataFrame([_row("t", "g711_alaw", "all", 0.0)])
    b = pd.DataFrame([_row("t", "g711_alaw", "all", 0.0)])
    res = build_h1(a, b, compressed=["g711_alaw"])
    assert res.loc[0, "verdict"] == "N/A"
    assert res.loc[0, "split_verdict"] != "PASS"


def test_h1_ci_overlap_flag():
    a = pd.DataFrame([_row("t", "g711_alaw", "all", 0.20, 0.15, 0.25)])
    b = pd.DataFrame([_row("t", "g711_alaw", "all", 0.10, 0.08, 0.17)])
    res = build_h1(a, b, compressed=["g711_alaw"])
    assert bool(res.loc[0, "ci_overlap"]) is True


def test_h2_selects_unseen_tts_case_insensitive():
    b = pd.DataFrame([
        _row("ood", "g711_alaw", "all", 0.10),
        _row("ood", "g711_alaw", "F5-TTS", 0.05),
        _row("ood", "g711_alaw", "VieNeu-TTS v3 Turbo", 0.12, hi=0.14),
        _row("ood", "amr_nb", "VieNeu-TTS v3 Turbo", 0.18, hi=0.21),
    ])
    res = build_h2(b, unseen_pattern="vieneu", threshold=0.15)
    assert len(res) == 2
    r = res.set_index("condition")
    assert r.loc["g711_alaw", "verdict"] == "PASS"
    assert bool(r.loc["g711_alaw", "ci_hi_pass"]) is True
    assert r.loc["amr_nb", "verdict"] == "FAIL"


def test_h2_empty_when_no_unseen_rows():
    b = pd.DataFrame([_row("ood", "g711_alaw", "F5-TTS", 0.05)])
    assert len(build_h2(b, unseen_pattern="vieneu")) == 0


def test_to_markdown_has_header_and_rows():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    md = to_markdown(df)
    lines = md.splitlines()
    assert lines[0].startswith("| a | b |")
    assert set(lines[1].replace("|", "").replace(" ", "")) <= {"-", ":"}
    assert len(lines) == 4
