"""Chẩn đoán chuyên sâu toàn diện các người nói pilot và SPK_0001.

Tính toán:
1. Điểm số (raw score, logits z0, z1, SHA-256) trên Checkpoint B cho toàn bộ file pilot (79 file).
2. Thông số âm học chuẩn hóa 16kHz (clipping, silence, RMS, SNR, 4-dải phổ, spectral centroid/rolloff, F0).
3. Trích xuất embedding 320 chiều và so sánh khoảng cách Cosine/Euclidean với centroid Bona fide và F5 spoof.
4. Đối chiếu SPK_0001 với mẫu Dev bona fide và F5 spoof gần nhất.
"""

from __future__ import annotations
import hashlib
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch
import torch.nn.functional as F

from scripts.eval_ssl_aasist import load_model
from src.training.dataset import fit_length, load_wave


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_acoustic_features(wav_16k: np.ndarray, native_path: str | Path) -> dict:
    native_info = sf.info(native_path)
    native_sr = native_info.samplerate
    native_dur = native_info.duration
    
    # Clipping % (|x| >= 0.999)
    clip_pct = float(np.mean(np.abs(wav_16k) >= 0.999) * 100.0)
    
    # RMS and Peak
    rms = float(np.sqrt(np.mean(wav_16k ** 2)))
    peak = float(np.max(np.abs(wav_16k)))
    
    # Frame-level RMS (25ms window, 10ms hop)
    frame_len = int(16000 * 0.025)
    hop_len = int(16000 * 0.010)
    frames = librosa.util.frame(wav_16k, frame_length=frame_len, hop_length=hop_len)
    frame_rms = np.sqrt(np.mean(frames ** 2, axis=0)) + 1e-9
    
    # Robust Silence and SNR definition
    rms_p90 = np.percentile(frame_rms, 90)
    silence_thr = max(1e-4, rms_p90 * 0.1)
    silence_frames = frame_rms[frame_rms < silence_thr]
    speech_frames = frame_rms[frame_rms >= silence_thr]
    silence_ratio = float(len(silence_frames) / len(frame_rms) * 100.0)
    
    # Handle files with and without explicit silence
    if len(silence_frames) >= 5:
        has_silence_ref = True
        noise_floor_rms = float(np.median(silence_frames))
        noise_floor_db = float(20 * np.log10(noise_floor_rms + 1e-9))
        speech_rms = float(np.mean(speech_frames)) if len(speech_frames) > 0 else rms
        estimated_snr_db = float(20 * np.log10((speech_rms + 1e-9) / (noise_floor_rms + 1e-9)))
    else:
        has_silence_ref = False
        noise_floor_rms = float(np.nan)
        noise_floor_db = float(np.nan)
        estimated_snr_db = float(np.nan)  # Đánh dấu không ước lượng được khi không có khoảng lặng
    
    # Spectral features
    spec_cent = float(np.mean(librosa.feature.spectral_centroid(y=wav_16k, sr=16000)))
    spec_bw = float(np.mean(librosa.feature.spectral_bandwidth(y=wav_16k, sr=16000)))
    spec_roll = float(np.mean(librosa.feature.spectral_rolloff(y=wav_16k, sr=16000, roll_percent=0.85)))
    spec_flat = float(np.mean(librosa.feature.spectral_flatness(y=wav_16k)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=wav_16k)))
    
    # 4-band spectral energies (FFT magnitude squared)
    n_fft = 2048
    freqs = librosa.fft_frequencies(sr=16000, n_fft=n_fft)
    stft = np.abs(librosa.stft(wav_16k, n_fft=n_fft, hop_length=hop_len)) ** 2
    avg_power = np.mean(stft, axis=1)
    total_power = np.sum(avg_power) + 1e-9
    
    # Spectral tilt (dB / kHz linear slope)
    freqs_khz = freqs / 1000.0
    valid_f = (freqs_khz >= 0.1) & (freqs_khz <= 7.5)
    log_power_db = 10 * np.log10(avg_power[valid_f] + 1e-12)
    p_fit = np.polyfit(freqs_khz[valid_f], log_power_db, 1)
    spectral_tilt_db_per_khz = float(p_fit[0])
    
    b1_mask = (freqs >= 0) & (freqs < 1000)
    b2_mask = (freqs >= 1000) & (freqs < 2000)
    b3_mask = (freqs >= 2000) & (freqs < 4000)
    b4_mask = (freqs >= 4000) & (freqs <= 8000)
    
    band_0_1k = float(np.sum(avg_power[b1_mask]) / total_power * 100.0)
    band_1_2k = float(np.sum(avg_power[b2_mask]) / total_power * 100.0)
    band_2_4k = float(np.sum(avg_power[b3_mask]) / total_power * 100.0)
    band_4_8k = float(np.sum(avg_power[b4_mask]) / total_power * 100.0)
    
    # Pitch estimation using pyin with window=1024 to support low male voice down to 65 Hz
    try:
        f0, voiced_flag, _ = librosa.pyin(
            wav_16k,
            fmin=65.0,
            fmax=350.0,
            sr=16000,
            frame_length=1024,
            hop_length=160,
        )
        voiced_f0 = f0[voiced_flag & ~np.isnan(f0)]
        f0_mean = float(np.mean(voiced_f0)) if len(voiced_f0) > 0 else 0.0
        f0_median = float(np.median(voiced_f0)) if len(voiced_f0) > 0 else 0.0
        f0_std = float(np.std(voiced_f0)) if len(voiced_f0) > 0 else 0.0
        voiced_pct = float(np.mean(voiced_flag) * 100.0)
    except Exception:
        f0_mean, f0_median, f0_std, voiced_pct = 0.0, 0.0, 0.0, 0.0

    return {
        "native_sr": native_sr,
        "native_dur": round(native_dur, 3),
        "clipping_pct": round(clip_pct, 4),
        "has_silence_ref": has_silence_ref,
        "silence_ratio": round(silence_ratio, 2),
        "rms": round(rms, 4),
        "peak": round(peak, 4),
        "noise_floor_db": round(noise_floor_db, 2) if not np.isnan(noise_floor_db) else None,
        "snr_db": round(estimated_snr_db, 2) if not np.isnan(estimated_snr_db) else None,
        "spec_centroid": round(spec_cent, 1),
        "spec_bandwidth": round(spec_bw, 1),
        "spec_rolloff": round(spec_roll, 1),
        "spec_flatness": round(spec_flat, 5),
        "spectral_tilt_db_per_khz": round(spectral_tilt_db_per_khz, 2),
        "zcr": round(zcr, 4),
        "band_0_1k_pct": round(band_0_1k, 2),
        "band_1_2k_pct": round(band_1_2k, 2),
        "band_2_4k_pct": round(band_2_4k, 2),
        "band_4_8k_pct": round(band_4_8k, 2),
        "f0_mean": round(f0_mean, 1),
        "f0_median": round(f0_median, 1),
        "f0_std": round(f0_std, 1),
        "voiced_pct": round(voiced_pct, 2),
    }


@torch.no_grad()
def extract_repr_and_logits(model, wav_tensor, device="cuda"):
    model.eval()
    wav_tensor = wav_tensor.to(device)
    feats = model.frontend(wav_tensor)
    x = F.max_pool2d(feats.transpose(1, 2).unsqueeze(1), (3, 3))
    x = model.conv(F.selu(model.bn_in(x)))
    g_s = model.gat_s(x.abs().amax(dim=3).transpose(1, 2))
    g_t = model.gat_t(x.abs().amax(dim=2).transpose(1, 2))
    master = model.master.expand(x.size(0), -1, -1)
    for layer in model.hs:
        g_t, g_s, master = layer(g_t, g_s, master)
    h = torch.cat([g_t.abs().amax(1), g_t.mean(1),
                   g_s.abs().amax(1), g_s.mean(1), master.squeeze(1)], dim=1)  # (B, 320)
    logits = model.out(h)  # (B, 2)
    return h.cpu().numpy(), logits.cpu().numpy()


def normalize_emb(x: np.ndarray) -> np.ndarray:
    a_f = np.asarray(x).flatten()
    norm = np.linalg.norm(a_f)
    return a_f / (norm + 1e-9)


def cos_dist(a: np.ndarray, b: np.ndarray) -> float:
    a_n = normalize_emb(a)
    b_n = normalize_emb(b)
    val = float(np.dot(a_n, b_n))
    return float(np.clip(1.0 - val, 0.0, 2.0))


def euc_dist(a: np.ndarray, b: np.ndarray) -> float:
    a_n = normalize_emb(a)
    b_n = normalize_emb(b)
    return float(np.linalg.norm(a_n - b_n))


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading checkpoint B on {device}...")
    model, meta = load_model("out/run_B/best_model.pt", device=device)
    model.eval()

    # 1. Process all 79 pilot files in data/raw
    pilot_spks = ["SPK_0001", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    pilot_records = []
    rng = np.random.default_rng(42)

    for spk in pilot_spks:
        pdir = Path("data/raw", spk)
        files = sorted(list(pdir.glob("*.wav")))
        for f in files:
            full_hash = sha256_file(f)
            short_hash = full_hash[:12]
            utt_id = f.stem

            # Load 16kHz and compute robust acoustic features
            wav = load_wave(f, sr=16000)
            ac = compute_acoustic_features(wav, f)

            # Fit 64000
            wav_fitted = fit_length(wav, 64000, train=False, rng=rng)
            t = torch.tensor(wav_fitted, dtype=torch.float32).unsqueeze(0)
            h, logits = extract_repr_and_logits(model, t, device=device)

            z0 = float(logits[0, 0])
            z1 = float(logits[0, 1])
            raw_score = float(z1 - z0)

            rec = {
                "speaker_id": spk,
                "utt_id": utt_id,
                "filename": f.name,
                "sha256": full_hash,
                "sha256_short": short_hash,
                "label": "bonafide",
                "is_enroll_subset": (utt_id.endswith(("_01", "_02", "_03", "_04", "_05"))),
                "z_spoof": round(z0, 4),
                "z_bona": round(z1, 4),
                "raw_score": round(raw_score, 4),
                **ac,
            }
            rec["_embedding"] = normalize_emb(h[0])
            pilot_records.append(rec)

    df_pilot = pd.DataFrame([{k: v for k, v in r.items() if k != "_embedding"} for r in pilot_records])
    os.makedirs("out/diagnostics", exist_ok=True)
    df_pilot.to_csv("out/diagnostics/pilot_speakers_scores_and_metrics.csv", index=False)
    print(f"Saved {len(df_pilot)} pilot records to out/diagnostics/pilot_speakers_scores_and_metrics.csv")

    # 2. Extract reference Bona fide and Spoof sets with Speaker-Disjoint & Base_utt-Disjoint Split
    print("Collecting reference Dev/VIVOS bona fide and F5 spoof files (Strict Speaker & Text Disjoint)...")
    vivos_spks = sorted([d.name for d in Path("out/data/bonafide_ref").glob("VIVOS*") if d.is_dir()])
    bona_proto_files = [sorted(list(Path("out/data/bonafide_ref", spk).glob("*.wav")))[0] for spk in vivos_spks[:25]]
    bona_eval_files = [sorted(list(Path("out/data/bonafide_ref", spk).glob("*.wav")))[0] for spk in vivos_spks[25:50]]

    # F5-TTS Spoof partitions: strictly exclude SPK_0001
    f5_proto_spks = ["SPK_0004", "SPK_0005", "VIVOSDEV01"]
    f5_eval_spks = ["SPK_0006", "SPK_0007", "VIVOSDEV02", "VIVOSDEV03"]

    def get_f5_files(spks):
        out = []
        seen_base = set()
        for s in spks:
            for f in sorted(list(Path("out/data/spoof_f5tts", s).glob("*.wav"))):
                base = f.stem.replace("_g711", "").replace("_amrnb", "")
                if base not in seen_base:
                    seen_base.add(base)
                    out.append(f)
        return out

    spoof_proto_files = get_f5_files(f5_proto_spks)
    spoof_eval_files = get_f5_files(f5_eval_spks)

    print(f"Bona fide: Proto={len(bona_proto_files)} spks, Eval={len(bona_eval_files)} spks (Speaker-Disjoint)")
    print(f"Spoof F5: Proto={len(spoof_proto_files)} base_utts, Eval={len(spoof_eval_files)} base_utts (Speaker & Base_utt Disjoint)")

    def load_and_embed(files):
        records = []
        for f in files:
            try:
                w = load_wave(f, sr=16000)
                wf = fit_length(w, 64000, train=False, rng=rng)
                t = torch.tensor(wf, dtype=torch.float32).unsqueeze(0)
                h, logits = extract_repr_and_logits(model, t, device=device)
                sc = float(logits[0, 1] - logits[0, 0])
                records.append({
                    "path": str(f),
                    "utt_id": f.stem,
                    "score": round(sc, 4),
                    "_embedding": normalize_emb(h[0]),
                })
            except Exception:
                continue
        return records

    print("Extracting Prototype pool embeddings...")
    bona_proto_recs = load_and_embed(bona_proto_files)
    spoof_proto_recs = load_and_embed(spoof_proto_files)

    print("Extracting Independent Evaluation pool embeddings...")
    bona_eval_recs = load_and_embed(bona_eval_files)
    spoof_eval_recs = load_and_embed(spoof_eval_files)

    # 3. Form Unit Prototypes
    mu_bona = normalize_emb(np.mean([r["_embedding"] for r in bona_proto_recs], axis=0))
    mu_spoof = normalize_emb(np.mean([r["_embedding"] for r in spoof_proto_recs], axis=0))
    inter_mu_cos = cos_dist(mu_bona, mu_spoof)

    # Independent reference distributions
    bona_eval_dists_to_mu_bona = np.array([cos_dist(r["_embedding"], mu_bona) for r in bona_eval_recs])
    spoof_eval_dists_to_mu_spoof = np.array([cos_dist(r["_embedding"], mu_spoof) for r in spoof_eval_recs])

    embedding_results = {
        "experiment_protocol": {
            "prototype_bona": {"speakers": 25, "base_utts": len(bona_proto_recs), "count": len(bona_proto_recs)},
            "independent_eval_bona": {"speakers": 25, "base_utts": len(bona_eval_recs), "count": len(bona_eval_recs)},
            "prototype_spoof": {"source_speakers": len(f5_proto_spks), "base_utts": len(spoof_proto_recs), "count": len(spoof_proto_recs)},
            "independent_eval_spoof": {"source_speakers": len(f5_eval_spks), "base_utts": len(spoof_eval_recs), "count": len(spoof_eval_recs)},
            "inter_prototype_cos_dist": round(inter_mu_cos, 4),
            "disjoint_guarantee": "Strict Speaker-Disjoint & Base_utt-Disjoint. SPK_0001 strictly excluded.",
        },
        "independent_reference_distributions": {
            "bona_eval_to_mu_bona": {
                "median": round(float(np.median(bona_eval_dists_to_mu_bona)), 4),
                "iqr": round(float(np.percentile(bona_eval_dists_to_mu_bona, 75) - np.percentile(bona_eval_dists_to_mu_bona, 25)), 4),
                "p05": round(float(np.percentile(bona_eval_dists_to_mu_bona, 5)), 4),
                "p95": round(float(np.percentile(bona_eval_dists_to_mu_bona, 95)), 4),
            },
            "spoof_eval_to_mu_spoof": {
                "median": round(float(np.median(spoof_eval_dists_to_mu_spoof)), 4),
                "iqr": round(float(np.percentile(spoof_eval_dists_to_mu_spoof, 75) - np.percentile(spoof_eval_dists_to_mu_spoof, 25)), 4),
                "p05": round(float(np.percentile(spoof_eval_dists_to_mu_spoof, 5)), 4),
                "p95": round(float(np.percentile(spoof_eval_dists_to_mu_spoof, 95)), 4),
            },
        },
        "pilot_speakers": {},
    }

    # Evaluate each pilot speaker against the prototypes and independent distribution
    for spk in pilot_spks:
        recs = [r for r in pilot_records if r["speaker_id"] == spk]
        cos_b = [cos_dist(r["_embedding"], mu_bona) for r in recs]
        cos_s = [cos_dist(r["_embedding"], mu_spoof) for r in recs]
        pct_b = [float(np.mean(bona_eval_dists_to_mu_bona <= d) * 100.0) for d in cos_b]
        pct_s = [float(np.mean(spoof_eval_dists_to_mu_spoof <= d) * 100.0) for d in cos_s]

        embedding_results["pilot_speakers"][spk] = {
            "speaker_id": spk,
            "utterance_count": len(recs),
            "cos_dist_to_mu_bona": {
                "median": round(float(np.median(cos_b)), 4),
                "iqr": round(float(np.percentile(cos_b, 75) - np.percentile(cos_b, 25)), 4),
                "min": round(float(np.min(cos_b)), 4),
                "max": round(float(np.max(cos_b)), 4),
            },
            "cos_dist_to_mu_spoof": {
                "median": round(float(np.median(cos_s)), 4),
                "iqr": round(float(np.percentile(cos_s, 75) - np.percentile(cos_s, 25)), 4),
                "min": round(float(np.min(cos_s)), 4),
                "max": round(float(np.max(cos_s)), 4),
            },
            "percentile_in_bona_eval_distribution": {
                "median": round(float(np.median(pct_b)), 2),
                "min": round(float(np.min(pct_b)), 2),
                "max": round(float(np.max(pct_b)), 2),
            },
            "percentile_in_spoof_eval_distribution": {
                "median": round(float(np.median(pct_s)), 2),
                "min": round(float(np.min(pct_s)), 2),
                "max": round(float(np.max(pct_s)), 2),
            },
        }

    # 4. Nearest Neighbor in Independent Evaluation Pool for SPK_0001
    spk1_enroll_recs = [r for r in pilot_records if r["speaker_id"] == "SPK_0001" and r["is_enroll_subset"]]
    spk1_nearest_info = []

    for r in spk1_enroll_recs:
        emb = r["_embedding"]
        sc = r["raw_score"]
        d_b = cos_dist(emb, mu_bona)
        d_s = cos_dist(emb, mu_spoof)

        pct_in_bona = float(np.mean(bona_eval_dists_to_mu_bona <= d_b) * 100.0)
        pct_in_spoof = float(np.mean(spoof_eval_dists_to_mu_spoof <= d_s) * 100.0)

        # Nearest Dev bona fide in INDEPENDENT evaluation pool
        best_bona_cos = float("inf")
        best_bona_match = None
        for b_rec in bona_eval_recs:
            d = cos_dist(emb, b_rec["_embedding"])
            if d < best_bona_cos:
                best_bona_cos = d
                best_bona_match = b_rec

        # Nearest F5 spoof in INDEPENDENT evaluation pool by cos distance
        best_spoof_cos = float("inf")
        best_spoof_cos_match = None
        for s_rec in spoof_eval_recs:
            d = cos_dist(emb, s_rec["_embedding"])
            if d < best_spoof_cos:
                best_spoof_cos = d
                best_spoof_cos_match = s_rec

        spk1_nearest_info.append({
            "utt_id": r["utt_id"],
            "sha256_short": r["sha256_short"],
            "score": r["raw_score"],
            "cos_dist_to_mu_bona": round(d_b, 4),
            "cos_dist_to_mu_spoof": round(d_s, 4),
            "percentile_in_indep_bona": round(pct_in_bona, 1),
            "percentile_in_indep_spoof": round(pct_in_spoof, 1),
            "nearest_indep_bona": {
                "utt_id": best_bona_match["utt_id"],
                "score": best_bona_match["score"],
                "cos_dist": round(best_bona_cos, 4),
            },
            "nearest_indep_spoof": {
                "utt_id": best_spoof_cos_match["utt_id"],
                "score": best_spoof_cos_match["score"],
                "cos_dist": round(best_spoof_cos, 4),
            },
        })

    embedding_results["spk_0001_nearest_analysis"] = spk1_nearest_info

    with open("out/diagnostics/embedding_analysis.json", "w", encoding="utf-8") as f:
        json.dump(embedding_results, f, indent=2)

    # 5. Acoustic dispersion (Median, IQR, std) table per speaker
    acoustic_cols = [
        "clipping_pct", "silence_ratio", "rms", "peak", "noise_floor_db", "snr_db",
        "spec_centroid", "spec_bandwidth", "spec_rolloff", "spec_flatness",
        "spectral_tilt_db_per_khz", "zcr",
        "band_0_1k_pct", "band_1_2k_pct", "band_2_4k_pct", "band_4_8k_pct",
        "f0_mean", "f0_median", "f0_std", "voiced_pct"
    ]
    dispersion = {}
    for spk in pilot_spks:
        sub = df_pilot[df_pilot["speaker_id"] == spk]
        spk_stat = {}
        for col in acoustic_cols:
            vals = sub[col].values
            q25, q50, q75 = np.percentile(vals, [25, 50, 75])
            spk_stat[col] = {
                "median": round(float(q50), 3),
                "iqr": round(float(q75 - q25), 3),
                "mean": round(float(np.mean(vals)), 3),
                "std": round(float(np.std(vals)), 3),
            }
        dispersion[spk] = spk_stat

    with open("out/diagnostics/acoustic_dispersion.json", "w", encoding="utf-8") as f:
        json.dump(dispersion, f, indent=2)

    print("\nSUCCESS: All diagnostics computed and saved to out/diagnostics/")

    print("\nSUCCESS: All diagnostics computed and saved to out/diagnostics/")


if __name__ == "__main__":
    main()
