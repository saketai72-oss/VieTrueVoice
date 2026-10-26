"""Prepare blind listening package and baseline manual measurement templates.

Selects 6 bona fide and 6 spoof samples (3-5s), applies AMR-NB compression simulation,
randomizes order s01..s12, and produces private ground-truth key with SHA-256 hashes.
"""

import os
import sys
import random
import hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import soundfile as sf
import torch

from src.preprocessing.codec_simulator import CodecSimulator


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def prepare_blind_test(
    output_dir: str = "benchmarks/blind_test_audio",
    key_csv_path: str = "benchmarks/blind_key_private.csv",
    manual_trials_template: str = "benchmarks/manual_verification_trials.csv",
    human_responses_template: str = "benchmarks/human_blind_responses.csv",
    seed: int = 42,
):
    random.seed(seed)
    np.random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(key_csv_path), exist_ok=True)

    simulator = CodecSimulator(sr=16000)

    # 1. Candidate selection: 6 bonafide across speakers
    bonafide_candidates = [
        ("data/raw/SPK_0001/SPK_0001_01.wav", "SPK_0001"),
        ("data/raw/SPK_0004/SPK_0004_01.wav", "SPK_0004"),
        ("data/raw/SPK_0005/SPK_0005_01.wav", "SPK_0005"),
        ("data/raw/SPK_0006/SPK_0006_01.wav", "SPK_0006"),
        ("data/raw/SPK_0007/SPK_0007_01.wav", "SPK_0007"),
        ("data/raw/SPK_0007/SPK_0007_02.wav", "SPK_0007"),
    ]

    # 2. Candidate selection: 6 spoof across F5-TTS and VieNeu-TTS
    spoof_candidates = [
        ("out/data/spoof_f5tts/SPK_0001/SPK_0001_prompt_000.wav", "SPK_0001", "F5-TTS"),
        ("out/data/spoof_f5tts/SPK_0004/SPK_0004_prompt_000.wav", "SPK_0004", "F5-TTS"),
        ("out/data/spoof_f5tts/SPK_0006/SPK_0006_prompt_000.wav", "SPK_0006", "F5-TTS"),
        ("out/data/spoof_vieneu/SPK_0005/SPK_0005_prompt_000.wav", "SPK_0005", "VieNeu-TTS"),
        ("out/data/spoof_vieneu/SPK_0007/SPK_0007_prompt_000.wav", "SPK_0007", "VieNeu-TTS"),
        ("out/data/spoof_vieneu/SPK_0007/SPK_0007_prompt_001.wav", "SPK_0007", "VieNeu-TTS"),
    ]

    items = []
    for path, spk in bonafide_candidates:
        items.append({
            "source_path": path,
            "speaker_id": spk,
            "true_label": "bonafide",
            "generator": "natural_voice",
        })

    for path, spk, gen in spoof_candidates:
        items.append({
            "source_path": path,
            "speaker_id": spk,
            "true_label": "spoof",
            "generator": gen,
        })

    # Shuffle 12 items randomly
    random.shuffle(items)

    key_rows = []
    print(f"Generating 12 blind test audio files in {output_dir}...")
    for idx, item in enumerate(items, start=1):
        sample_id = f"s{idx:02d}"
        target_path = os.path.join(output_dir, f"{sample_id}.wav")

        # Load audio
        data, sr = sf.read(item["source_path"])
        if data.ndim > 1:
            data = data.mean(axis=1)

        # Ensure length between 3.0s (48k) and 5.0s (80k)
        target_sr = 16000
        if sr != target_sr:
            # Resample if needed
            from scipy import signal
            data = signal.resample(data, int(len(data) * target_sr / sr))
            sr = target_sr

        # Crop to max 4.0s (64,000 samples) if longer, or pad if shorter than 3.0s
        if len(data) > 64000:
            data = data[:64000]
        elif len(data) < 48000:
            # repeat pad
            reps = int(np.ceil(48000 / len(data)))
            data = np.tile(data, reps)[:48000]

        # Apply AMR-NB compression simulation
        tensor_audio = torch.from_numpy(data.astype(np.float32)).unsqueeze(0)
        compressed = simulator.simulate_amr(tensor_audio).squeeze(0).numpy()

        # Prevent clipping
        max_val = np.max(np.abs(compressed)) + 1e-8
        if max_val > 1.0:
            compressed = compressed / max_val

        # Save compressed 16kHz WAV
        sf.write(target_path, compressed, target_sr, subtype="PCM_16")

        sha256 = compute_sha256(target_path)
        duration_sec = round(len(compressed) / target_sr, 3)

        key_rows.append({
            "sample_id": sample_id,
            "true_label": item["true_label"],
            "generator": item["generator"],
            "speaker_id": item["speaker_id"],
            "codec": "amr_nb_12.2kbps",
            "duration_sec": duration_sec,
            "audio_sha256": sha256,
            "source_file": item["source_path"],
        })
        print(f"  [{sample_id}] -> {item['true_label']} ({item['generator']}, {duration_sec}s)")

    # Write blind_key_private.csv
    key_df = pd.DataFrame(key_rows)
    key_df.to_csv(key_csv_path, index=False, encoding="utf-8")
    print(f"\nSaved ground truth key to {key_csv_path}")

    # Generate template for manual verification trials if not exists
    if not os.path.exists(manual_trials_template):
        trial_rows = []
        # 12 trials for ear
        for idx in range(1, 13):
            sample_id = f"s{idx:02d}"
            trial_rows.append({
                "trial_id": f"T_EAR_{idx:02d}",
                "method": "ear",
                "sample_id": sample_id,
                "total_sec": "",
                "predicted_label": "",
                "is_correct": "",
                "notes": "",
                "timestamp": "",
            })
        # 12 trials for spectrogram
        for idx in range(1, 13):
            sample_id = f"s{idx:02d}"
            trial_rows.append({
                "trial_id": f"T_SPEC_{idx:02d}",
                "method": "spectrogram",
                "sample_id": sample_id,
                "total_sec": "",
                "predicted_label": "",
                "is_correct": "",
                "notes": "",
                "timestamp": "",
            })
        pd.DataFrame(trial_rows).to_csv(manual_trials_template, index=False, encoding="utf-8")
        print(f"Saved manual verification template to {manual_trials_template}")

    # Generate template for human blind responses if not exists
    if not os.path.exists(human_responses_template):
        sample_response_template = pd.DataFrame(columns=[
            "participant_id",
            "sample_id",
            "predicted_label",
            "timestamp",
        ])
        sample_response_template.to_csv(human_responses_template, index=False, encoding="utf-8")
        print(f"Saved human responses template to {human_responses_template}")

    print("\n[SUCCESS] Blind test package created successfully!")


if __name__ == "__main__":
    prepare_blind_test()
