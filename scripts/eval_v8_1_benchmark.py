#!/usr/bin/env python3
"""Comprehensive V8.1 evaluation and V7 vs V8.0 vs V8.1 fair benchmark script.

Covers:
1. 4 Gates x 3 Pooling Modes (`max`, `mean`, `asymmetric_veto`) + Dev Bona BPCER@0 (2,000 clips).
2. Fair 4,979-clip / 4,969-clip comparative control set (Gate 1: 15, Gate 2: 84, Dev Bona: 2,000,
   Dev F5: 960, Dev Omni V8.0: 965 / V8.1: 955, Unseen VieNeu: 955).
3. Full `test_indomain_v8_f5_omni.csv` (15,980 clips, plus `role == 'eval'` 15,665 clips) and
   `unseen_vieneu_benchmark.csv` (955 clips) with per-TTS and per-codec breakdowns.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
import pandas as pd
import torch

from scripts.eval_ssl_aasist import load_model
from src.evaluation.metrics import compute_eer, compute_min_dcf
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores

POOLING_MODES = ("max", "mean", "asymmetric_veto")
CODECS_ORDER = ("clean_16khz", "aac_zalo_76k", "opus_zalo_24k", "g711_alaw", "amr_nb")
ACCEPTANCE_SPEAKERS = ("SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007")


def _load_windows_for_path(rel_or_abs: str | Path) -> torch.Tensor:
    p = Path(rel_or_abs)
    if not p.is_absolute():
        p = _ROOT / p
    y = load_audio(p, target_sr=16000)
    return extract_window_batch(y, win=64000, hop=16000, max_windows=5, dense_slicing=True)


def _score_chunk_for_model(
    model: torch.nn.Module,
    chunk_items: list[tuple[str, torch.Tensor]],
    device: str,
    max_batch_windows: int = 16,
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    pending_keys: list[str] = []
    pending_tensors: list[torch.Tensor] = []
    pending_counts: list[int] = []
    pending_win_total = 0

    def _flush() -> None:
        nonlocal pending_keys, pending_tensors, pending_counts, pending_win_total
        if not pending_tensors:
            return
        cat = torch.cat(pending_tensors, dim=0).to(device)
        with torch.inference_mode():
            sc = model.score(cat).detach().float().cpu().numpy()
        offset = 0
        for key, cnt in zip(pending_keys, pending_counts):
            out[key] = [float(x) for x in sc[offset : offset + cnt]]
            offset += cnt
        pending_keys = []
        pending_tensors = []
        pending_counts = []
        pending_win_total = 0

    for key, wb in chunk_items:
        n_w = int(wb.shape[0])
        if pending_win_total > 0 and pending_win_total + n_w > max_batch_windows:
            _flush()
        pending_keys.append(key)
        pending_tensors.append(wb)
        pending_counts.append(n_w)
        pending_win_total += n_w
    _flush()
    return out


def infer_window_scores_multi_ckpt(
    ckpt_specs: dict[str, str | Path | dict[str, Any]],
    paths: list[str | Path],
    device: str = "cuda",
    max_batch_windows: int = 16,
    chunk_size: int = 500,
    desc: str = "MultiEval",
) -> dict[str, dict[str, list[float]]]:
    """Decode audio once in bounded CPU chunks and score across multiple models/state_dicts."""
    from src.models.ssl_aasist import SSLAASIST

    unique_keys: list[str] = []
    seen: set[str] = set()
    for p in paths:
        k = str(p).replace("\\", "/")
        if k not in seen:
            seen.add(k)
            unique_keys.append(k)

    # Keep models on CPU and swap onto GPU per chunk so peak VRAM stays < 1 GB
    cpu_models: dict[str, torch.nn.Module] = {}
    for name, spec in ckpt_specs.items():
        if isinstance(spec, dict) and "state_dict" in spec:
            m = SSLAASIST(**spec.get("model_kwargs", {}))
            m.load_state_dict(spec["state_dict"])
        else:
            m, _ = load_model(str(spec), "cpu")
        m.eval()
        cpu_models[name] = m

    all_scores: dict[str, dict[str, list[float]]] = {name: {} for name in ckpt_specs}
    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=4) as pool:
        for start in range(0, len(unique_keys), chunk_size):
            sub_keys = unique_keys[start : start + chunk_size]
            wbs = list(pool.map(_load_windows_for_path, sub_keys))
            chunk_items = list(zip(sub_keys, wbs))
            for name, m in cpu_models.items():
                m.to(device)
                chunk_res = _score_chunk_for_model(m, chunk_items, device=device, max_batch_windows=max_batch_windows)
                all_scores[name].update(chunk_res)
                m.to("cpu")
            if device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
            done = min(start + chunk_size, len(unique_keys))
            dt = time.perf_counter() - t0
            print(f"  [{desc}] {done}/{len(unique_keys)} unique clips ({done/max(dt,1e-6):.1f} clips/s)", flush=True)

    return all_scores


def infer_window_scores_batched(
    model: torch.nn.Module,
    paths: list[str | Path],
    device: str = "cuda",
    max_batch_windows: int = 16,
    desc: str = "Eval",
) -> dict[str, list[float]]:
    """Extract windows and compute raw per-window scores once per unique path."""
    unique_keys: list[str] = []
    seen: set[str] = set()
    for p in paths:
        k = str(p).replace("\\", "/")
        if k not in seen:
            seen.add(k)
            unique_keys.append(k)

    results: dict[str, list[float]] = {}
    model.eval()
    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=4) as pool:
        for start in range(0, len(unique_keys), 500):
            sub_keys = unique_keys[start : start + 500]
            wbs = list(pool.map(_load_windows_for_path, sub_keys))
            results.update(_score_chunk_for_model(model, list(zip(sub_keys, wbs)), device=device, max_batch_windows=max_batch_windows))
            done = min(start + 500, len(unique_keys))
            dt = time.perf_counter() - t0
            print(f"  [{desc}] {done}/{len(unique_keys)} unique clips ({done/max(dt,1e-6):.1f} clips/s)", flush=True)

    return results


def _pool_map(score_cache: dict[str, list[float]], paths: list[str], mode: str) -> np.ndarray:
    return np.array(
        [pool_scores(score_cache[str(p).replace("\\", "/")], mode=mode) for p in paths],
        dtype=np.float64,
    )


def _binary_metrics(bona_scores: np.ndarray, spoof_scores: np.ndarray) -> dict[str, Any]:
    all_s = np.concatenate([bona_scores, spoof_scores])
    all_y = np.concatenate([np.ones(len(bona_scores), dtype=int), np.zeros(len(spoof_scores), dtype=int)])
    eer, thr = compute_eer(all_s, all_y)
    min_dcf = compute_min_dcf(all_s, all_y)
    n_blocked = int(np.sum(spoof_scores <= 0.0))
    return {
        "total_spoof": int(len(spoof_scores)),
        "total_bona": int(len(bona_scores)),
        "eer_pct": float(eer * 100.0),
        "eer_threshold": float(thr),
        "min_dcf": float(min_dcf),
        "blocked_count": n_blocked,
        "block_rate_pct": float((n_blocked / len(spoof_scores)) * 100.0) if len(spoof_scores) else 0.0,
        "mean_spoof_score": float(np.mean(spoof_scores)) if len(spoof_scores) else 0.0,
        "median_spoof_score": float(np.median(spoof_scores)) if len(spoof_scores) else 0.0,
        "mean_bona_score": float(np.mean(bona_scores)) if len(bona_scores) else 0.0,
    }


def collect_4979_paths() -> dict[str, Any]:
    """Collect exact file lists for the 4,979-clip / 4,969-clip comparative benchmark."""
    spk1_dir = _ROOT / "data/raw/SPK_0001"
    spk1_files = sorted(
        f for f in spk1_dir.glob("*.wav")
        if not any(c in f.name for c in ("_g711", "_amrnb", "_aac_zalo", "_opus_zalo"))
    )
    spk1_paths = [f.relative_to(_ROOT).as_posix() for f in spk1_files]

    acc_items: list[tuple[str, str]] = []
    for spk in ACCEPTANCE_SPEAKERS:
        d = _ROOT / f"data/raw/{spk}"
        clean = [
            f for f in sorted(list(d.glob("*.wav")) + list(d.glob("*.m4a")))
            if not any(c in f.name for c in ("_g711", "_amrnb", "_aac_zalo", "_opus_zalo"))
        ]
        for f in clean:
            acc_items.append((spk, f.relative_to(_ROOT).as_posix()))

    dev_df = pd.read_csv(_ROOT / "data/manifests_zalo/dev_v8_f5_omni.csv")
    bona_sample = (
        dev_df[dev_df["label"] == "bonafide"]
        .groupby("codec", group_keys=False)
        .apply(lambda x: x.sample(min(len(x), 400), random_state=42))
    )
    f5_dev = dev_df[dev_df["tts_generator"] == "F5-TTS-Vietnamese"].copy()
    omni_dev_v8_1 = dev_df[dev_df["tts_generator"] == "OmniVoice"].copy()
    omni_v8_0_df = pd.read_csv(_ROOT / "data/manifests_zalo/unseen_omnivoice_15spk_benchmark.csv")
    vieneu_df = pd.read_csv(_ROOT / "data/manifests_zalo/unseen_vieneu_benchmark.csv")

    v7_cache = pd.read_csv(_ROOT / "benchmarks/cached_scores_15spk_v7.csv")
    omni_missed_df = v7_cache[(v7_cache["tts_generator"] == "OmniVoice") & (v7_cache["score"] > 0)].copy()

    return {
        "spk1_paths": spk1_paths,
        "acc_items": acc_items,
        "bona_2000_df": bona_sample,
        "f5_dev_df": f5_dev,
        "omni_v8_0_df": omni_v8_0_df,
        "omni_v8_1_df": omni_dev_v8_1,
        "vieneu_df": vieneu_df,
        "omni_missed_df": omni_missed_df,
    }


def summarize_4979_from_cache(
    cache: dict[str, list[float]],
    bundle: dict[str, Any],
    ckpt_label: str,
    ck_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute 4-Gate + 4,979-clip / 4,969-clip metrics from precomputed window-score cache."""
    spk1_paths = bundle["spk1_paths"]
    acc_items = bundle["acc_items"]
    bona_paths = bundle["bona_2000_df"]["audio_path"].astype(str).tolist()
    f5_paths = bundle["f5_dev_df"]["audio_path"].astype(str).tolist()
    omni_v8_0_paths = bundle["omni_v8_0_df"]["audio_path"].astype(str).tolist()
    omni_v8_1_paths = bundle["omni_v8_1_df"]["audio_path"].astype(str).tolist()
    vieneu_paths = bundle["vieneu_df"]["audio_path"].astype(str).tolist()
    missed_df = bundle["omni_missed_df"]
    missed_paths = missed_df["audio_path"].astype(str).tolist()

    by_mode: dict[str, Any] = {}
    for mode in POOLING_MODES:
        g1_sc = _pool_map(cache, spk1_paths, mode)
        g1_pass = int(np.sum(g1_sc > 0.0))

        acc_sc = _pool_map(cache, [p for _, p in acc_items], mode)
        g2_bona = int(np.sum(acc_sc > 0.0))
        by_spk = {}
        ctrl4_total, ctrl4_bona = 0, 0
        for spk in ACCEPTANCE_SPEAKERS:
            idx = [i for i, (s_id, _) in enumerate(acc_items) if s_id == spk]
            s_arr = acc_sc[idx]
            n_b = int(np.sum(s_arr > 0.0))
            if spk != "SPK_0003":
                ctrl4_total += len(s_arr)
                ctrl4_bona += n_b
            by_spk[spk] = {
                "total": int(len(s_arr)),
                "bona": n_b,
                "pass_rate_pct": float(n_b / len(s_arr) * 100.0) if len(s_arr) else 0.0,
                "mean_score": float(np.mean(s_arr)) if len(s_arr) else 0.0,
            }

        bona_sc = _pool_map(cache, bona_paths, mode)
        bona_rej = int(np.sum(bona_sc <= 0.0))
        f5_sc = _pool_map(cache, f5_paths, mode)
        omni0_sc = _pool_map(cache, omni_v8_0_paths, mode)
        omni1_sc = _pool_map(cache, omni_v8_1_paths, mode)
        vn_sc = _pool_map(cache, vieneu_paths, mode)
        missed_sc = _pool_map(cache, missed_paths, mode)
        n_rev = int(np.sum(missed_sc <= 0.0))

        vivos_p0 = {}
        for (_, row), new_s in zip(missed_df.iterrows(), missed_sc):
            if "VIVOSDEV02_omnivoice_prompt_000" in str(row["utt_id"]):
                vivos_p0[str(row["utt_id"])] = {
                    "old": float(row["score"]),
                    "new": float(new_s),
                }

        by_mode[mode] = {
            "gate1_spk0001": {
                "n_pass": g1_pass,
                "total": len(spk1_paths),
                "pass_rate_pct": float(g1_pass / len(spk1_paths) * 100.0),
                "mean_score": float(np.mean(g1_sc)),
                "median_score": float(np.median(g1_sc)),
                "passed": g1_pass >= 12,
            },
            "gate2_acceptance_5spk": {
                "total_bona": g2_bona,
                "total_files": len(acc_items),
                "overall_pass_rate_pct": float(g2_bona / len(acc_items) * 100.0),
                "ctrl4_bona": ctrl4_bona,
                "ctrl4_files": ctrl4_total,
                "ctrl4_pass_rate_pct": float(ctrl4_bona / ctrl4_total * 100.0) if ctrl4_total else 0.0,
                "by_speaker": by_spk,
            },
            "gate3_unseen_vieneu": _binary_metrics(bona_sc, vn_sc),
            "gate4_omnivoice_reversal": {
                "n_reversed": n_rev,
                "total": len(missed_paths),
                "reversal_rate_pct": float(n_rev / len(missed_paths) * 100.0),
                "vivosdev02_prompt0_details": vivos_p0,
            },
            "dev_bona_bpcer_2000": {
                "rejected_count": bona_rej,
                "total": len(bona_sc),
                "bpcer_pct": float(bona_rej / len(bona_sc) * 100.0),
                "mean_score": float(np.mean(bona_sc)),
                "median_score": float(np.median(bona_sc)),
            },
            "seen_f5_dev_960": _binary_metrics(bona_sc, f5_sc),
            "seen_omni_v8_0_965": _binary_metrics(bona_sc, omni0_sc),
            "seen_omni_v8_1_955": _binary_metrics(bona_sc, omni1_sc),
            "seen_v8_1_pooled_1915": _binary_metrics(bona_sc, np.concatenate([f5_sc, omni1_sc])),
            "seen_v8_0_pooled_1925": _binary_metrics(bona_sc, np.concatenate([f5_sc, omni0_sc])),
        }

    meta = ck_meta or {}
    return {
        "checkpoint": str(ckpt_label).replace("\\", "/"),
        "ckpt_meta": {
            "phase": meta.get("phase"),
            "epoch": meta.get("epoch"),
            "dev_eer": meta.get("dev_eer"),
        },
        "clip_counts": {
            "set_4979": 15 + 84 + 2000 + 960 + 965 + 955,
            "set_4969_v8_1_sym": 15 + 84 + 2000 + 960 + 955 + 955,
        },
        "modes": by_mode,
    }


def evaluate_4979_and_4gates(
    ckpt_path: str | Path,
    bundle: dict[str, Any],
    device: str = "cuda",
) -> dict[str, Any]:
    """Evaluate 4 Gates + Seen/Unseen Dev across all 3 pooling modes."""
    print(f"\n=== Evaluating 4-Gate + 4,979-Clip Set: {ckpt_path} ===", flush=True)
    model, ck = load_model(str(ckpt_path), device)
    all_paths = _bundle_all_paths(bundle)
    cache = infer_window_scores_batched(model, all_paths, device=device, desc=Path(ckpt_path).parent.name)
    return summarize_4979_from_cache(cache, bundle, ckpt_label=str(ckpt_path), ck_meta=ck)


def _bundle_all_paths(bundle: dict[str, Any]) -> list[str]:
    return (
        bundle["spk1_paths"]
        + [p for _, p in bundle["acc_items"]]
        + bundle["bona_2000_df"]["audio_path"].astype(str).tolist()
        + bundle["f5_dev_df"]["audio_path"].astype(str).tolist()
        + bundle["omni_v8_0_df"]["audio_path"].astype(str).tolist()
        + bundle["omni_v8_1_df"]["audio_path"].astype(str).tolist()
        + bundle["vieneu_df"]["audio_path"].astype(str).tolist()
        + bundle["omni_missed_df"]["audio_path"].astype(str).tolist()
    )


def summarize_test_indomain_from_cache(
    cache: dict[str, list[float]],
    df: pd.DataFrame,
    ckpt_label: str,
) -> dict[str, Any]:
    """Summarize 15,980-clip test_indomain_v8_f5_omni.csv metrics from precomputed cache."""
    paths = df["audio_path"].astype(str).tolist()
    is_bona = (df["label"] == "bonafide").to_numpy()
    is_spoof = (df["label"] == "spoof").to_numpy()
    is_eval = (df["role"] == "eval").to_numpy()
    is_f5 = (df["tts_generator"] == "F5-TTS-Vietnamese").to_numpy()
    is_omni = (df["tts_generator"] == "OmniVoice").to_numpy()
    codecs = df["codec"].astype(str).to_numpy()

    out_modes: dict[str, Any] = {}
    for mode in POOLING_MODES:
        sc = _pool_map(cache, paths, mode)

        def _summarize(mask_subset: np.ndarray) -> dict[str, Any]:
            m_b = mask_subset & is_bona
            m_s = mask_subset & is_spoof
            b_sc = sc[m_b]
            s_sc = sc[m_s]
            rej = int(np.sum(b_sc <= 0.0))
            ov = _binary_metrics(b_sc, s_sc)
            ov["bona_bpcer_pct"] = float(rej / len(b_sc) * 100.0) if len(b_sc) else 0.0
            ov["bona_rejected_count"] = rej

            f5_m = mask_subset & is_f5
            omni_m = mask_subset & is_omni
            by_tts = {
                "F5-TTS-Vietnamese": _binary_metrics(b_sc, sc[f5_m]),
                "OmniVoice": _binary_metrics(b_sc, sc[omni_m]),
            }
            by_codec = {}
            for c in CODECS_ORDER:
                cm_b = mask_subset & is_bona & (codecs == c)
                cm_s = mask_subset & is_spoof & (codecs == c)
                if np.any(cm_b) and np.any(cm_s):
                    cb = sc[cm_b]
                    cs = sc[cm_s]
                    c_res = _binary_metrics(cb, cs)
                    c_rej = int(np.sum(cb <= 0.0))
                    c_res["bona_bpcer_pct"] = float(c_rej / len(cb) * 100.0)
                    c_res["f5_block_rate_pct"] = float(np.mean(sc[mask_subset & is_f5 & (codecs == c)] <= 0.0) * 100.0)
                    c_res["omni_block_rate_pct"] = float(np.mean(sc[mask_subset & is_omni & (codecs == c)] <= 0.0) * 100.0)
                    by_codec[c] = c_res
            return {"overall": ov, "by_tts": by_tts, "by_codec": by_codec}

        out_modes[mode] = {
            "full_15980": _summarize(np.ones(len(df), dtype=bool)),
            "eval_only_15665": _summarize(is_eval),
        }

    return {
        "checkpoint": str(ckpt_label).replace("\\", "/"),
        "total_rows": len(df),
        "modes": out_modes,
    }


def evaluate_test_indomain(
    ckpt_path: str | Path,
    test_manifest_path: str | Path = "data/manifests_zalo/test_indomain_v8_f5_omni.csv",
    device: str = "cuda",
) -> dict[str, Any]:
    """Evaluate full 15,980-clip test_indomain_v8_f5_omni.csv across all 3 pooling modes."""
    print(f"\n=== Evaluating test_indomain (15,980 clips): {ckpt_path} ===", flush=True)
    model, _ = load_model(str(ckpt_path), device)
    df = pd.read_csv(_ROOT / str(test_manifest_path))
    paths = df["audio_path"].astype(str).tolist()
    cache = infer_window_scores_batched(model, paths, device=device, desc=f"Test15k:{Path(ckpt_path).parent.name}")
    return summarize_test_indomain_from_cache(cache, df, ckpt_label=str(ckpt_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate V8.1 checkpoints and V7 vs V8.0 vs V8.1 benchmark")
    parser.add_argument("--checkpoints", nargs="+", required=True, help="name=path pairs")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--include-test-indomain", action="store_true")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    bundle = collect_4979_paths()
    ckpt_specs = dict(s.split("=", 1) for s in args.checkpoints)
    ckpt_metas = {
        name: torch.load(str(_ROOT / p if not Path(p).is_absolute() else p), map_location="cpu")
        for name, p in ckpt_specs.items()
    }
    ckpt_metas = {
        name: {"phase": ck.get("phase"), "epoch": ck.get("epoch"), "dev_eer": ck.get("dev_eer")}
        for name, ck in ckpt_metas.items()
    }

    print(f"Running shared-decode multi-model eval for {list(ckpt_specs.keys())}...", flush=True)
    caches_4979 = infer_window_scores_multi_ckpt(
        ckpt_specs, _bundle_all_paths(bundle), device=args.device, desc="4979Set"
    )

    test_df = None
    caches_test: dict[str, dict[str, list[float]]] = {}
    if args.include_test_indomain:
        test_df = pd.read_csv(_ROOT / "data/manifests_zalo/test_indomain_v8_f5_omni.csv")
        caches_test = infer_window_scores_multi_ckpt(
            ckpt_specs, test_df["audio_path"].astype(str).tolist(), device=args.device, desc="Test15980"
        )

    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checkpoints": {},
    }
    for name, ck_path in ckpt_specs.items():
        entry = summarize_4979_from_cache(caches_4979[name], bundle, ck_path, ck_meta=ckpt_metas[name])
        if args.include_test_indomain and test_df is not None:
            entry["test_indomain"] = summarize_test_indomain_from_cache(caches_test[name], test_df, ck_path)
        report["checkpoints"][name] = entry

    out_p = _ROOT / args.out_json
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved benchmark report -> {out_p}", flush=True)


if __name__ == "__main__":
    main()
