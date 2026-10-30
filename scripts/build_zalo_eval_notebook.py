#!/usr/bin/env python3
"""Build dedicated Kaggle inference-only kernel for Zalo baseline evaluation (Giai đoạn 2).

Packages src/ and dev_zalo.csv into an immutable standalone notebook:
deploy_zalo_eval/eval_zalo_baseline.ipynb
and sets up deploy_zalo_eval/kernel-metadata.json.
"""

from __future__ import annotations
import base64
import json
from pathlib import Path
import zlib


def build_zalo_eval_notebook(
    out_dir: Path = Path("deploy_zalo_eval"),
    manifest_path: Path = Path("data/manifests_zalo/dev_zalo.csv"),
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    nb_path = out_dir / "eval_zalo_baseline.ipynb"
    meta_path = out_dir / "kernel-metadata.json"

    # 1. Package src/ payload
    pkg = {}
    for p in sorted(Path("src").rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        pkg[p.as_posix()] = p.read_text(encoding="utf-8")

    compressed_src = zlib.compress(json.dumps(pkg).encode("utf-8"), level=9)
    b64_src_payload = base64.b64encode(compressed_src).decode("ascii")

    # 2. Package dev_zalo.csv payload
    manifest_bytes = manifest_path.read_bytes()
    compressed_manifest = zlib.compress(manifest_bytes, level=9)
    b64_manifest_payload = base64.b64encode(compressed_manifest).decode("ascii")

    # 3. Create kernel-metadata.json
    metadata = {
        "id": "nguyenthanhtai1959/vietrue-zalo-baseline-evaluation",
        "title": "Vietrue Zalo Baseline Evaluation",
        "code_file": "eval_zalo_baseline.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "true",
        "enable_tpu": "false",
        "enable_internet": "true",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [
            "nguyenthanhtai1959/vietrue-ssl-training",
            "nguyenthanhtai1959/vietrue-model-training"
        ]
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    cells = [
        # Cell 0: Markdown Giới thiệu
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# ViTrueVoice — Đánh Giá Baseline Checkpoint B Trên Kênh Zalo Dual-Profile (Inference-Only)\n",
                "\n",
                "Notebook này thực thi quy trình chấm điểm độc lập (inference-only) trên toàn bộ **11.450 mẫu Dev Zalo** bằng Checkpoint B (`best_model_B.pt`).\n",
                "\n",
                "### 5 Cổng Kiểm Soát Chất Lượng Bắt Buộc:\n",
                "1. **Cổng 1 — Khóa Artifacts & Hash**: Mount 2 kernel source; SHA-256 Checkpoint B (`a921c339…`) và `dev_zalo.csv` (`730937e8…`) khớp 100%.\n",
                "2. **Cổng 2 — Giải nén Chọn Lọc (Bijective Selective Unzip)**: Giải nén đủ 6.786 file gốc từ `vitruevoice_data_processed.zip`; 0 file thiếu, 0 file ghi đè.\n",
                "3. **Cổng 3 — Khóa Mô hình (strict=True)**: Nạp 295/295 keys Checkpoint B; đặt `model.eval()`, `torch.inference_mode()`; tuyệt đối không train.\n",
                "4. **Cổng 4 — Suy luận Toàn Bộ 11.450 Mẫu (Zero Silent Skip)**: Chấm đủ 11.450 mẫu 5 codec (AAC: 2.332, Opus: 2.332, Clean: 2.332, AMR: 2.227, G.711: 2.227); fail-fast nếu thiếu bất kỳ mẫu nào.\n",
                "5. **Cổng 5 — Báo cáo & Kiểm định Hai Lớp**: Tính EER, minDCF, FRR@0, FAR@0 và Cluster Bootstrap 95% CI theo `base_utt`; bắt buộc mỗi codec có đủ cả bona fide lẫn spoof mới công nhận baseline."
            ]
        },

        # Cell 1: Kiểm tra môi trường GPU & Nạp trước HuggingFace cache
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 1. Kiểm tra môi trường GPU & Nạp trước cấu hình HuggingFace\n",
                "import os\n",
                "import sys\n",
                "import time\n",
                "import shutil\n",
                "import hashlib\n",
                "import zipfile\n",
                "import subprocess\n",
                "import json\n",
                "import zlib\n",
                "import base64\n",
                "from pathlib import Path\n",
                "\n",
                "import torch\n",
                "import torchaudio\n",
                "import soundfile as sf\n",
                "import numpy as np\n",
                "import pandas as pd\n",
                "from transformers import AutoConfig, Wav2Vec2Model\n",
                "from huggingface_hub import hf_hub_download\n",
                "\n",
                "print('=' * 60)\n",
                "print('⚙️ MÔI TRƯỜNG THỰC THI KAGGLE GPU')\n",
                "print('=' * 60)\n",
                "print(f'• Python: {sys.version}')\n",
                "print(f'• PyTorch: {torch.__version__} | CUDA: {torch.cuda.is_available()}')\n",
                "if torch.cuda.is_available():\n",
                "    print(f'• GPU: {torch.cuda.get_device_name(0)}')\n",
                "    print(f'• VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB')\n",
                "else:\n",
                "    raise SystemError('❌ Kernel yêu cầu GPU nhưng không tìm thấy CUDA device!')\n",
                "\n",
                "EXPECTED_HF_REVISION = '69e9000591623e5a4fc2f502407860bcdc0de0b2'\n",
                "print(f'🌐 Pre-warm cấu hình Wav2Vec2 tại commit bất biến: {EXPECTED_HF_REVISION}...')\n",
                "t0 = time.time()\n",
                "hf_cfg = AutoConfig.from_pretrained('nguyenvulebinh/wav2vec2-base-vietnamese-250h', revision=EXPECTED_HF_REVISION)\n",
                "print(f'✅ Đã tải và khóa cấu hình HuggingFace thành công ({time.time() - t0:.2f}s)')\n"
            ]
        },

        # Cell 2: Bung mã nguồn src/ và manifest dev_zalo.csv từ payload nhúng
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 2. Bung mã nguồn src/ và dev_zalo.csv từ payload bất biến\n",
                "working_dir = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path('.')\n",
                "\n",
                f"b64_src = '{b64_src_payload}'\n",
                "src_files = json.loads(zlib.decompress(base64.b64decode(b64_src.encode('ascii'))).decode('utf-8'))\n",
                "for fpath_str, content in src_files.items():\n",
                "    dest = working_dir / fpath_str\n",
                "    dest.parent.mkdir(parents=True, exist_ok=True)\n",
                "    dest.write_text(content, encoding='utf-8')\n",
                "print(f'✅ Đã bung {len(src_files)} tệp mã nguồn src/ vào {working_dir}')\n",
                "\n",
                f"b64_manifest = '{b64_manifest_payload}'\n",
                "manifest_raw = zlib.decompress(base64.b64decode(b64_manifest.encode('ascii')))\n",
                "manifest_dest = working_dir / 'dev_zalo.csv'\n",
                "manifest_dest.write_bytes(manifest_raw)\n",
                "\n",
                "EXPECTED_MANIFEST_SHA = '730937e8fe982b51c899753cd2a9aff198ff545d8d0b9fd41a9511025884f77e'\n",
                "actual_manifest_sha = hashlib.sha256(manifest_dest.read_bytes()).hexdigest()\n",
                "print(f'📄 Manifest: {manifest_dest}')\n",
                "print(f'   - SHA-256 thực tế:  {actual_manifest_sha}')\n",
                "print(f'   - SHA-256 kỳ vọng:  {EXPECTED_MANIFEST_SHA}')\n",
                "assert actual_manifest_sha == EXPECTED_MANIFEST_SHA, '❌ Sai lệch SHA-256 dev_zalo.csv!'\n",
                "\n",
                "df_dev = pd.read_csv(manifest_dest)\n",
                "print(f'📊 Phân bổ Dev Zalo: {len(df_dev)} dòng')\n",
                "assert len(df_dev) == 11450, f'❌ Số dòng không phải 11450: {len(df_dev)}'\n",
                "assert sum(df_dev['label'] == 'bonafide') == 10490, '❌ Sai số lượng bonafide (kỳ vọng 10490)'\n",
                "assert sum(df_dev['label'] == 'spoof') == 960, '❌ Sai số lượng spoof (kỳ vọng 960)'\n",
                "assert not df_dev['speaker_id'].str.startswith('SPK_').any(), '❌ Phát hiện SPK_xxxx trong Dev Zalo!'\n",
                "assert 'VieNeu-TTS' not in df_dev['tts_generator'].values, '❌ Phát hiện VieNeu-TTS trong Dev Zalo!'\n",
                "\n",
                "if str(working_dir.resolve()) not in sys.path:\n",
                "    sys.path.insert(0, str(working_dir.resolve()))\n",
                "from src.models.ssl_aasist import SSLAASIST\n",
                "from src.preprocessing.audio_loader import load_audio\n",
                "from src.training.dataset import fit_length\n",
                "from src.evaluation.metrics import compute_eer, compute_min_dcf\n",
                "print('✅ Nạp thành công các module từ src/')\n"
            ]
        },

        # Cell 3: Cổng 1 — Xác minh Nguồn Kernel & Checkpoint B SHA-256
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 3. CỔNG 1 — Xác minh Nguồn Kernel & Checkpoint B SHA-256\n",
                "def compute_sha256(path: Path) -> str:\n",
                "    h = hashlib.sha256()\n",
                "    with open(path, 'rb') as f:\n",
                "        for chunk in iter(lambda: f.read(1024 * 1024), b''):\n",
                "            h.update(chunk)\n",
                "    return h.hexdigest()\n",
                "\n",
                "EXPECTED_CKPT_SHA = 'a921c3397946335c9543528993eafde80ac0d42decf431101635806b5c56bd9f'\n",
                "\n",
                "# Tìm Checkpoint B\n",
                "ckpt_candidates = (\n",
                "    list(Path('/kaggle/input').rglob('*best_model_B*.pt')) +\n",
                "    list(Path('/kaggle/input').rglob('*run_B*best_model*.pt')) +\n",
                "    list(Path('/kaggle/input').rglob('*best_model*.pt')) +\n",
                "    [\n",
                "        Path('/kaggle/input/vietrue-ssl-training/best_model_B.pt'),\n",
                "        Path('/kaggle/input/vietrue-ssl-training/run_B/best_model.pt'),\n",
                "        Path('out/kaggle_ssl_out/best_model_B.pt'),\n",
                "    ]\n",
                ")\n",
                "ckpt_path = None\n",
                "for c in ckpt_candidates:\n",
                "    if c.exists() and c.is_file() and c.stat().st_size > 10000000:\n",
                "        if compute_sha256(c) == EXPECTED_CKPT_SHA:\n",
                "            ckpt_path = c\n",
                "            break\n",
                "assert ckpt_path is not None, f'❌ Không tìm thấy Checkpoint B khớp SHA-256!'\n",
                "print(f'📦 Checkpoint B: {ckpt_path}')\n",
                "print(f'   - SHA-256: {compute_sha256(ckpt_path)}')\n",
                "\n",
                "# Tìm file ZIP dữ liệu processed\n",
                "zip_candidates = (\n",
                "    list(Path('/kaggle/input').rglob('*vitruevoice*.zip')) +\n",
                "    list(Path('/kaggle/input').rglob('*.zip')) +\n",
                "    [\n",
                "        Path('/kaggle/input/vietrue-model-training/vitruevoice_data_processed.zip'),\n",
                "    ]\n",
                ")\n",
                "zip_path = None\n",
                "for z in zip_candidates:\n",
                "    if z.exists() and z.is_file() and z.stat().st_size > 1000000:\n",
                "        zip_path = z\n",
                "        break\n",
                "assert zip_path is not None, f'❌ Không tìm thấy file ZIP dữ liệu âm thanh!'\n",
                "print(f'📦 Data ZIP: {zip_path} ({zip_path.stat().st_size / (1024**2):.1f} MB)')\n",
                "print('🏁 CỔNG 1: HOÀN TOÀN ĐẠT CHUẨN!')\n"
            ]
        },

        # Cell 4: Cổng 2 — Giải Nén Chọn Lọc (Bijective Selective Unzip)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 4. CỔNG 2 — Giải nén chọn lọc đúng các tệp audio gốc cần thiết\n",
                "t_unzip_start = time.perf_counter()\n",
                "\n",
                "# Thu thập toàn bộ đường dẫn audio gốc trong ZIP cần thiết:\n",
                "# Clean, G.711, AMR: dùng trực tiếp đường dẫn audio_path\n",
                "# AAC, Opus: dùng file master clean của cùng base_utt\n",
                "clean_rows = df_dev[df_dev['codec'] == 'clean_16khz']\n",
                "base_to_clean_path = dict(zip(clean_rows['base_utt'], clean_rows['audio_path']))\n",
                "\n",
                "required_rel_paths = set()\n",
                "for _, row in df_dev.iterrows():\n",
                "    c = row['codec']\n",
                "    if c in ['clean_16khz', 'g711_alaw', 'amr_nb']:\n",
                "        required_rel_paths.add(row['audio_path'].replace('\\\\', '/').lstrip('/'))\n",
                "    else:\n",
                "        # Proxy AAC/Opus lấy từ clean master\n",
                "        master_p = base_to_clean_path[row['base_utt']].replace('\\\\', '/').lstrip('/')\n",
                "        required_rel_paths.add(master_p)\n",
                "\n",
                "print(f'🎯 Tổng số tệp audio gốc cần trích xuất từ ZIP: {len(required_rel_paths)}')\n",
                "\n",
                "with zipfile.ZipFile(zip_path, 'r') as zf:\n",
                "    namelist_set = set(zf.namelist())\n",
                "    extract_targets = []\n",
                "    missing_in_zip = []\n",
                "    \n",
                "    for rel_p in required_rel_paths:\n",
                "        candidates_zip = [rel_p, f'data/{rel_p}', rel_p.replace('data/', '')]\n",
                "        found_entry = None\n",
                "        for cand in candidates_zip:\n",
                "            if cand in namelist_set:\n",
                "                found_entry = cand\n",
                "                break\n",
                "        if found_entry is None:\n",
                "            missing_in_zip.append(rel_p)\n",
                "        else:\n",
                "            dest_target = (working_dir / rel_p).resolve()\n",
                "            extract_targets.append((found_entry, dest_target))\n",
                "\n",
                "    print(f'   - Đã ánh xạ trong ZIP: {len(extract_targets)} / {len(required_rel_paths)} tệp')\n",
                "    if missing_in_zip:\n",
                "        print(f'❌ Thiếu {len(missing_in_zip)} tệp trong ZIP! Mẫu đầu: {missing_in_zip[:5]}')\n",
                "        raise FileNotFoundError(f'Thiếu {len(missing_in_zip)} tệp trong ZIP!')\n",
                "        \n",
                "    print('🚀 Đang thực hiện Selective Unzip...')\n",
                "    for zip_entry, dest_target in extract_targets:\n",
                "        dest_target.parent.mkdir(parents=True, exist_ok=True)\n",
                "        if not dest_target.exists():\n",
                "            with zf.open(zip_entry) as src, open(dest_target, 'wb') as dst:\n",
                "                shutil.copyfileobj(src, dst)\n",
                "\n",
                "print(f'✅ Giải nén chọn lọc hoàn tất trong {time.perf_counter() - t_unzip_start:.1f}s!')\n",
                "\n",
                "# Kiểm tra 100% tệp gốc tồn tại\n",
                "missing_files = [p for p in required_rel_paths if not (working_dir / p).is_file()]\n",
                "print(f'🔍 Kiểm tra đĩa: {len(required_rel_paths) - len(missing_files)} / {len(required_rel_paths)} tồn tại')\n",
                "assert len(missing_files) == 0, f'❌ Vẫn còn {len(missing_files)} tệp không tìm thấy sau khi giải nén!'\n",
                "print('🏁 CỔNG 2: HOÀN TOÀN ĐẠT CHUẨN!')\n"
            ]
        },

        # Cell 5: Cổng 3 — Nạp Checkpoint B strict=True & Khóa eval mode
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 5. CỔNG 3 — Nạp Checkpoint B strict=True & Khóa eval mode\n",
                "device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\n",
                "print(f'🤖 Đang nạp Checkpoint B: {ckpt_path} lên {device}...')\n",
                "ckpt_dict = torch.load(ckpt_path, map_location=device, weights_only=False)\n",
                "\n",
                "model_kwargs = dict(ckpt_dict.get('model_kwargs', {}))\n",
                "model_kwargs['ssl_config'] = hf_cfg\n",
                "model = SSLAASIST(**model_kwargs)\n",
                "\n",
                "state_dict = ckpt_dict['model'] if 'model' in ckpt_dict else ckpt_dict['model_state_dict']\n",
                "load_result = model.load_state_dict(state_dict, strict=True)\n",
                "print(f'✅ Khớp 295/295 keys thành công: {load_result}')\n",
                "\n",
                "model.to(device)\n",
                "model.eval()\n",
                "for param in model.parameters():\n",
                "    param.requires_grad = False\n",
                "\n",
                "assert not model.training, '❌ Mô hình chưa ở trạng thái eval()!'\n",
                "print('🏁 CỔNG 3: HOÀN TOÀN ĐẠT CHUẨN (strict=True, eval-only)!')\n"
            ]
        },

        # Cell 6: Cổng 4 — Suy luận 11.450 mẫu Zalo (Fail-Fast, Zero Silent Skip)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 6. CỔNG 4 — Suy luận toàn bộ 11.450 mẫu Zalo (Fail-Fast, Zero Silent Skip)\n",
                "def transcode_aac_adts_stream(raw_wav_bytes: bytes) -> bytes:\n",
                "    cmd_enc = ['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0', '-ar', '48000', '-ac', '1', '-c:a', 'aac', '-b:a', '76k', '-f', 'adts', 'pipe:1']\n",
                "    proc_enc = subprocess.run(cmd_enc, input=raw_wav_bytes, capture_output=True, check=True)\n",
                "    cmd_dec = ['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0', '-f', 'wav', '-ar', '16000', '-ac', '1', 'pipe:1']\n",
                "    proc_dec = subprocess.run(cmd_dec, input=proc_enc.stdout, capture_output=True, check=True)\n",
                "    return proc_dec.stdout\n",
                "\n",
                "def transcode_opus_ogg_stream(raw_wav_bytes: bytes) -> bytes:\n",
                "    cmd_enc = ['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0', '-c:a', 'libopus', '-b:a', '24k', '-f', 'ogg', 'pipe:1']\n",
                "    proc_enc = subprocess.run(cmd_enc, input=raw_wav_bytes, capture_output=True, check=True)\n",
                "    cmd_dec = ['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0', '-f', 'wav', '-ar', '16000', '-ac', '1', 'pipe:1']\n",
                "    proc_dec = subprocess.run(cmd_dec, input=proc_enc.stdout, capture_output=True, check=True)\n",
                "    return proc_dec.stdout\n",
                "\n",
                "# Pre-load clean audio bytes in memory for fast proxy transcoding\n",
                "print('⚡ Đang nạp sẵn master clean bytes vào RAM để tối ưu tốc độ transcode...')\n",
                "clean_bytes_map = {}\n",
                "for base_utt, rel_p in base_to_clean_path.items():\n",
                "    abs_p = working_dir / rel_p.replace('\\\\', '/').lstrip('/')\n",
                "    clean_bytes_map[base_utt] = abs_p.read_bytes()\n",
                "print(f'✅ Đã nạp {len(clean_bytes_map)} clean masters vào RAM.')\n",
                "\n",
                "rng = np.random.default_rng(0)\n",
                "scored_records = []\n",
                "t_infer_start = time.perf_counter()\n",
                "\n",
                "print(f'🚀 Bắt đầu suy luận tuần tự trên đúng {len(df_dev)} mẫu Dev Zalo...')\n",
                "with torch.inference_mode():\n",
                "    for idx, row in df_dev.iterrows():\n",
                "        codec = row['codec']\n",
                "        base_utt = row['base_utt']\n",
                "        label_int = 1 if str(row['label']).lower() in ['bonafide', '1'] else 0\n",
                "        \n",
                "        wav_16k = None\n",
                "        if codec in ['clean_16khz', 'g711_alaw', 'amr_nb']:\n",
                "            p = working_dir / row['audio_path'].replace('\\\\', '/').lstrip('/')\n",
                "            if not p.is_file():\n",
                "                raise FileNotFoundError(f'❌ Dòng {idx}: Thiếu tệp audio {p}!')\n",
                "            wav_16k = load_audio(p, target_sr=16000)\n",
                "        elif codec == 'aac_zalo_76k':\n",
                "            c_bytes = clean_bytes_map[base_utt]\n",
                "            proxy_bytes = transcode_aac_adts_stream(c_bytes)\n",
                "            wav_16k = load_audio(proxy_bytes, target_sr=16000)\n",
                "        elif codec == 'opus_zalo_24k':\n",
                "            c_bytes = clean_bytes_map[base_utt]\n",
                "            proxy_bytes = transcode_opus_ogg_stream(c_bytes)\n",
                "            wav_16k = load_audio(proxy_bytes, target_sr=16000)\n",
                "            \n",
                "        if wav_16k is None:\n",
                "            raise RuntimeError(f'❌ Dòng {idx} ({row[\"utt_id\"]}): Giải mã âm thanh thất bại!')\n",
                "            \n",
                "        t = fit_length(wav_16k, 64000, train=False, rng=rng)\n",
                "        tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)\n",
                "        score = model.score(tensor).item()\n",
                "        if np.isnan(score) or np.isinf(score):\n",
                "            raise ValueError(f'❌ Dòng {idx}: Điểm số suy luận bị NaN/Inf!')\n",
                "            \n",
                "        rec = dict(row)\n",
                "        rec['score'] = score\n",
                "        rec['label_int'] = label_int\n",
                "        scored_records.append(rec)\n",
                "        \n",
                "        if (idx + 1) % 1000 == 0 or (idx + 1) == len(df_dev):\n",
                "            elapsed = time.perf_counter() - t_infer_start\n",
                "            rate = (idx + 1) / elapsed\n",
                "            print(f'   - Đã chấm {idx + 1}/{len(df_dev)} mẫu ({rate:.1f} mẫu/s, trôi qua {elapsed:.1f}s)...')\n",
                "\n",
                "scored_df = pd.DataFrame(scored_records)\n",
                "assert len(scored_df) == 11450, f'❌ Số lượng mẫu đã chấm không đủ 11450: {len(scored_df)}'\n",
                "out_scores_path = working_dir / 'dev_zalo_scores.csv'\n",
                "scored_df.to_csv(out_scores_path, index=False)\n",
                "print(f'✅ Đã lưu bảng điểm đầy đủ 11.450 mẫu vào {out_scores_path}')\n",
                "print('🏁 CỔNG 4: HOÀN TOÀN ĐẠT CHUẨN!')\n"
            ]
        },

        # Cell 7: Cổng 5 — Báo cáo & Kiểm định Metrics Hai Lớp (Cluster Bootstrap CI)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 7. CỔNG 5 — Báo cáo & Kiểm định Metrics Hai Lớp\n",
                "def cluster_bootstrap_ci(subset: pd.DataFrame, n_boot: int = 1000, seed: int = 42) -> dict:\n",
                "    clusters, cluster_inv = np.unique(subset['base_utt'].values, return_inverse=True)\n",
                "    n_c = len(clusters)\n",
                "    if n_c < 5 or subset['label_int'].nunique() < 2:\n",
                "        return {}\n",
                "    cluster_indices = [np.where(cluster_inv == i)[0] for i in range(n_c)]\n",
                "    y_true_all = subset['label_int'].to_numpy(dtype=int)\n",
                "    y_score_all = subset['score'].to_numpy(dtype=float)\n",
                "    rng = np.random.default_rng(seed)\n",
                "    boot_eers, boot_frrs, boot_fars = [], [], []\n",
                "    for _ in range(n_boot):\n",
                "        sampled_c = rng.choice(n_c, size=n_c, replace=True)\n",
                "        idx = np.concatenate([cluster_indices[c] for c in sampled_c])\n",
                "        y_true = y_true_all[idx]\n",
                "        y_score = y_score_all[idx]\n",
                "        if len(np.unique(y_true)) < 2:\n",
                "            continue\n",
                "        try:\n",
                "            e, _ = compute_eer(y_score, y_true)\n",
                "            boot_eers.append(e * 100.0)\n",
                "        except Exception:\n",
                "            pass\n",
                "        n_b = np.sum(y_true == 1)\n",
                "        n_s = np.sum(y_true == 0)\n",
                "        if n_b > 0:\n",
                "            boot_frrs.append(float(np.sum((y_true == 1) & (y_score < 0.0)) / n_b * 100.0))\n",
                "        if n_s > 0:\n",
                "            boot_fars.append(float(np.sum((y_true == 0) & (y_score >= 0.0)) / n_s * 100.0))\n",
                "    def ci(arr):\n",
                "        if len(arr) == 0:\n",
                "            return (float('nan'), float('nan'))\n",
                "        return (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))\n",
                "    return {'eer_ci': ci(boot_eers), 'frr_ci': ci(boot_frrs), 'far_ci': ci(boot_fars)}\n",
                "\n",
                "metric_rows = []\n",
                "for c_name in ['aac_zalo_76k', 'opus_zalo_24k', 'clean_16khz', 'g711_alaw', 'amr_nb']:\n",
                "    c_df = scored_df[scored_df['codec'] == c_name]\n",
                "    y_true = c_df['label_int'].to_numpy().astype(int)\n",
                "    y_score = c_df['score'].to_numpy().astype(float)\n",
                "    n_bona = int(np.sum(y_true == 1))\n",
                "    n_spoof = int(np.sum(y_true == 0))\n",
                "    has_both = (n_bona > 0 and n_spoof > 0)\n",
                "    assert has_both, f'❌ Codec {c_name} thiếu một trong hai lớp (bona={n_bona}, spoof={n_spoof})!'\n",
                "    \n",
                "    eer, eer_thr = compute_eer(y_score, y_true)\n",
                "    min_dcf = compute_min_dcf(y_score, y_true)\n",
                "    frr_0 = float(np.sum((y_true == 1) & (y_score < 0.0)) / n_bona * 100.0)\n",
                "    far_0 = float(np.sum((y_true == 0) & (y_score >= 0.0)) / n_spoof * 100.0)\n",
                "    \n",
                "    ci_res = cluster_bootstrap_ci(c_df, n_boot=1000)\n",
                "    eer_ci = ci_res.get('eer_ci', (float('nan'), float('nan')))\n",
                "    frr_ci = ci_res.get('frr_ci', (float('nan'), float('nan')))\n",
                "    far_ci = ci_res.get('far_ci', (float('nan'), float('nan')))\n",
                "    \n",
                "    metric_rows.append({\n",
                "        'codec': c_name,\n",
                "        'n_total': len(c_df),\n",
                "        'n_bonafide': n_bona,\n",
                "        'n_spoof': n_spoof,\n",
                "        'is_valid': True,\n",
                "        'eer_pct': eer * 100.0,\n",
                "        'eer_ci_95': f'[{eer_ci[0]:.2f}, {eer_ci[1]:.2f}]',\n",
                "        'eer_threshold': eer_thr,\n",
                "        'min_dcf': min_dcf,\n",
                "        'frr_theta_0': frr_0,\n",
                "        'frr_ci_95': f'[{frr_ci[0]:.2f}, {frr_ci[1]:.2f}]',\n",
                "        'far_theta_0': far_0,\n",
                "        'far_ci_95': f'[{far_ci[0]:.2f}, {far_ci[1]:.2f}]',\n",
                "    })\n",
                "\n",
                "metrics_df = pd.DataFrame(metric_rows)\n",
                "out_metrics_path = working_dir / 'zalo_baseline_metrics.csv'\n",
                "metrics_df.to_csv(out_metrics_path, index=False)\n",
                "print('=' * 80)\n",
                "print('📊 BÁO CÁO BASELINE CHECKPOINT B TRÊN TẬP DEV ZALO ĐẦY ĐỦ (11.450 MẪU)')\n",
                "print('=' * 80)\n",
                "print(metrics_df[['codec', 'n_bonafide', 'n_spoof', 'eer_pct', 'eer_ci_95', 'frr_theta_0', 'far_theta_0', 'min_dcf']].to_string(index=False))\n",
                "\n",
                "# Paired Deltas so với clean\n",
                "clean_map = scored_df[scored_df['codec'] == 'clean_16khz'].set_index('base_utt')['score'].to_dict()\n",
                "delta_rows = []\n",
                "for p_codec in ['aac_zalo_76k', 'opus_zalo_24k', 'g711_alaw', 'amr_nb']:\n",
                "    sub = scored_df[scored_df['codec'] == p_codec].copy()\n",
                "    sub['clean_score'] = sub['base_utt'].map(clean_map)\n",
                "    sub = sub.dropna(subset=['clean_score'])\n",
                "    diff = sub['score'] - sub['clean_score']\n",
                "    delta_rows.append({\n",
                "        'codec': p_codec,\n",
                "        'n_paired': len(diff),\n",
                "        'mean_delta': float(diff.mean()),\n",
                "        'std_delta': float(diff.std()),\n",
                "        'median_delta': float(diff.median()),\n",
                "        'min_delta': float(diff.min()),\n",
                "        'max_delta': float(diff.max()),\n",
                "    })\n",
                "delta_df = pd.DataFrame(delta_rows)\n",
                "out_delta_path = working_dir / 'zalo_paired_deltas.csv'\n",
                "delta_df.to_csv(out_delta_path, index=False)\n",
                "print()\n",
                "print('📊 ĐỘ LỆCH ĐIỂM SỐ GHÉP CẶP (PAIRED DELTAS vs CLEAN):')\n",
                "print(delta_df.to_string(index=False))\n",
                "print()\n",
                "print('🏁 CỔNG 5: BASELINE ĐƯỢC CÔNG NHẬN HỢP LỆ VỚI ĐỦ CẢ HAI LỚP TRÊN 5 CODEC!')\n",
                "\n",
                "# Dọn dẹp tệp âm thanh tạm thời trên disk để output Kaggle gọn nhẹ\n",
                "data_dir = working_dir / 'data'\n",
                "if data_dir.exists():\n",
                "    shutil.rmtree(data_dir, ignore_errors=True)\n"
            ]
        }
    ]

    notebook_data = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(notebook_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Đã tạo thành công kernel notebook: {nb_path} ({nb_path.stat().st_size} bytes)")
    print(f"✅ Đã tạo thành công metadata: {meta_path}")
    return nb_path


if __name__ == "__main__":
    build_zalo_eval_notebook()
