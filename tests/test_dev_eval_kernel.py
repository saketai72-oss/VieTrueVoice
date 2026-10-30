"""Kiểm thử tính hợp lệ của Kernel đánh giá độc lập deploy_dev_eval."""

import json
from pathlib import Path
import pytest


def test_kernel_metadata_validity():
    meta_path = Path("deploy_dev_eval/kernel-metadata.json")
    assert meta_path.exists(), "Tệp deploy_dev_eval/kernel-metadata.json không tồn tại!"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta.get("id") == "nguyenthanhtai1959/vietrue-dev-evaluation-full"
    assert meta.get("code_file") == "eval_dev.ipynb"
    assert meta.get("kernel_type") == "notebook"
    assert meta.get("enable_gpu") == "true"
    assert meta.get("enable_internet") == "true"

    sources = meta.get("kernel_sources", [])
    assert "nguyenthanhtai1959/vietrue-ssl-training" in sources
    assert "nguyenthanhtai1959/vietrue-model-training" in sources
    assert len(meta.get("dataset_sources", [])) == 0, "Không được dùng dataset_sources cho kernel!"


def test_eval_dev_notebook_structure():
    nb_path = Path("deploy_dev_eval/eval_dev.ipynb")
    assert nb_path.exists(), "Tệp deploy_dev_eval/eval_dev.ipynb không tồn tại!"

    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    assert len(cells) == 10, f"Số lượng cells không đúng: {len(cells)}"

    all_source = "".join(["".join(c.get("source", [])) for c in cells])

    # Kiểm tra các cổng nghiệm thu đã khóa
    assert "a921c3397946335c9543528993eafde80ac0d42decf431101635806b5c56bd9f" in all_source, "Thiếu Checkpoint B SHA-256"
    assert "dfe82c215199590fc5a90134d37f2f775307218344216ca776d47f5b4f4b1f16" in all_source, "Thiếu Dev Manifest SHA-256"
    assert "strict=True" in all_source, "Thiếu kiểm tra strict=True khi nạp checkpoint"
    assert "namelist" in all_source and "set(raw_namelist)" in all_source, "Thiếu kiểm tra trùng lặp nội bộ ZIP"
    assert "target_to_zip_entry" in all_source, "Thiếu kiểm tra bijective mapping selective unzip"
    assert "boot_eers_2s" in all_source, "Thiếu logic Bootstrap 2 tầng (Speaker -> Utterance)"
    assert "spk_0001_scores" in all_source, "Thiếu mã định vị 5 điểm số SPK_0001"

    # Kiểm tra 3 điều kiện khóa tái lập mới
    assert "69e9000591623e5a4fc2f502407860bcdc0de0b2" in all_source, "Thiếu immutable commit revision của Wav2Vec2"
    assert "c9aef06eaf0c2c4200132c84456db8e2a556a51d6684096f44ee3d32df9dbec5" in all_source, "Thiếu SHA-256 của config.json"
    assert "c9388d1947e34550845ae473dcaaa02c615586f1c7f59f7627b13e94be99456c" in all_source, "Thiếu hash tham chiếu payload src/"
    assert "warmup_loader" in all_source and "torch.cuda.synchronize()" in all_source, "Thiếu warmup và đồng bộ CUDA benchmark"
    assert "model_kwargs['ssl_config'] = hf_cfg" in all_source, "Thiếu tiêm ssl_config offline vào model_kwargs"
    assert "load_wave" in all_source, "Thiếu hàm chuẩn hóa resampling load_wave(..., sr=16000) trong notebook!"


def test_audio_resampling_parity(tmp_path):
    """Kiểm tra tính nhất quán (parity) giữa load_wave và ViTrueVoiceDataset trên các sample rates khác nhau."""
    import numpy as np
    import soundfile as sf
    import pandas as pd
    from src.training.dataset import load_wave, fit_length, ViTrueVoiceDataset

    # 1. Tạo các file audio mẫu ở các tần số khác nhau
    dur_s = 1.5
    t_8k = np.linspace(0, dur_s, int(8000 * dur_s), endpoint=False)
    sig_8k = (0.5 * np.sin(2 * np.pi * 440 * t_8k)).astype(np.float32)
    p_8k = tmp_path / "test_8k.wav"
    sf.write(p_8k, sig_8k, 8000)

    t_16k = np.linspace(0, dur_s, int(16000 * dur_s), endpoint=False)
    sig_16k = (0.5 * np.sin(2 * np.pi * 440 * t_16k)).astype(np.float32)
    p_16k = tmp_path / "test_16k.wav"
    sf.write(p_16k, sig_16k, 16000)

    t_24k = np.linspace(0, dur_s, int(24000 * dur_s), endpoint=False)
    sig_24k = (0.5 * np.sin(2 * np.pi * 440 * t_24k)).astype(np.float32)
    p_24k = tmp_path / "test_24k.wav"
    sf.write(p_24k, sig_24k, 24000)

    sig_stereo = np.column_stack([sig_16k, sig_16k * 0.8])
    p_stereo = tmp_path / "test_stereo.wav"
    sf.write(p_stereo, sig_stereo, 16000)

    manifest_df = pd.DataFrame([
        {"utt_id": "u_8k", "speaker_id": "s1", "audio_path": "test_8k.wav", "label": "bonafide", "codec": "g711_alaw", "split": "dev"},
        {"utt_id": "u_16k", "speaker_id": "s1", "audio_path": "test_16k.wav", "label": "bonafide", "codec": "clean_16khz", "split": "dev"},
        {"utt_id": "u_24k", "speaker_id": "s2", "audio_path": "test_24k.wav", "label": "spoof", "codec": "clean_16khz", "split": "dev"},
        {"utt_id": "u_stereo", "speaker_id": "s1", "audio_path": "test_stereo.wav", "label": "bonafide", "codec": "clean_16khz", "split": "dev"},
    ])
    manifest_csv = tmp_path / "manifest.csv"
    manifest_df.to_csv(manifest_csv, index=False)

    ds = ViTrueVoiceDataset(manifest_csv, audio_root=tmp_path, mode="eval", train=False)

    # 2. Đối chiếu từng item giữa ViTrueVoiceDataset và loader chuẩn dùng load_wave
    for idx, row in manifest_df.iterrows():
        item_ds = ds[idx]
        wav_direct = load_wave(tmp_path / row["audio_path"], sr=16000)
        wav_fit = fit_length(wav_direct, 64000, train=False, rng=np.random.default_rng(0))

        # Kiểm tra độ dài, kiểu dữ liệu và tính hữu hạn
        assert wav_fit.shape == (64000,), f"Shape không đúng: {wav_fit.shape}"
        assert wav_fit.dtype == np.float32
        assert np.isfinite(wav_fit).all()

        # Kiểm tra parity tuyệt đối với dataset
        np.testing.assert_allclose(item_ds["wave"].numpy(), wav_fit, atol=1e-5,
                                   err_msg=f"Không khớp tensor giữa ViTrueVoiceDataset và load_wave cho {row['audio_path']}")

