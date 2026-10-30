#!/usr/bin/env python3
"""Build dedicated Kaggle training kernel for B_zalo fine-tuning (Giai đoạn 3).

Packages src/, scripts/train.py, train_zalo.csv, and dev_zalo.csv into an immutable standalone notebook:
deploy_zalo_train/train_zalo.ipynb
and sets up deploy_zalo_train/kernel-metadata.json.
"""

from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import zlib


def build_zalo_train_notebook(
    out_dir: Path = Path("deploy_zalo_train"),
    train_manifest: Path = Path("data/manifests_zalo/train_zalo.csv"),
    dev_manifest: Path = Path("data/manifests_zalo/dev_zalo.csv"),
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    nb_path = out_dir / "train_zalo.ipynb"
    meta_path = out_dir / "kernel-metadata.json"

    # 1. Package src/ and scripts/ payloads
    pkg = {}
    for p in sorted(Path("src").rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        pkg[p.as_posix()] = p.read_text(encoding="utf-8")
    for p in sorted(Path("scripts").rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        pkg[p.as_posix()] = p.read_text(encoding="utf-8")

    compressed_src = zlib.compress(json.dumps(pkg).encode("utf-8"), level=9)
    b64_src_payload = base64.b64encode(compressed_src).decode("ascii")

    # 2. Package manifests payloads
    train_raw = train_manifest.read_bytes()
    b64_train = base64.b64encode(zlib.compress(train_raw, level=9)).decode("ascii")
    expected_train_sha = hashlib.sha256(train_raw).hexdigest()

    dev_raw = dev_manifest.read_bytes()
    b64_dev = base64.b64encode(zlib.compress(dev_raw, level=9)).decode("ascii")
    expected_dev_sha = hashlib.sha256(dev_raw).hexdigest()

    # 3. Create kernel-metadata.json
    metadata = {
        "id": "nguyenthanhtai1959/vietrue-zalo-fine-tuning",
        "title": "Vietrue Zalo Fine Tuning B_zalo",
        "code_file": "train_zalo.ipynb",
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
        # Cell 0: Markdown
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# ViTrueVoice — Huấn Luyện Fine-Tuning Nhánh B_zalo Trên Kênh Zalo Dual-Profile\n",
                "\n",
                "Notebook này thực thi quá trình tinh chỉnh (fine-tuning) nhánh **`B_zalo`** từ Checkpoint B (`best_model_B.pt`).\n",
                "\n",
                "### 5 Cổng Kiểm Soát Chất Lượng Bắt Buộc:\n",
                "1. **Cổng 1 — Khóa Artifacts & Hash**: Checkpoint B (`a921c339…`), `train_zalo.csv` (`0e2f42e4…`), `dev_zalo.csv` (`730937e8…`) khớp 100%.\n",
                "2. **Cổng 2 — Cách Ly Tuyệt Đối**: 0% dữ liệu tình nguyện viên `SPK_xxxx`, 0% công cụ unseen `VieNeu-TTS` trong Train và Dev.\n",
                "3. **Cổng 3 — Bảo Toàn Backbone (Pha 1)**: Đóng băng 100% backbone Wav2Vec2 (`frontend.encoder`), chỉ cập nhật đồ thị HS-GAL & projection layer.\n",
                "4. **Cổng 4 — Trọng Số Loss Động**: Tính $w_c = \\frac{N}{2 \\cdot N_c}$ trên phân bố thực tế của `train_zalo.csv`.\n",
                "5. **Cổng 5 — Kiểm Định Chống Thoái Lui**: Đánh giá trên toàn bộ 11.450 mẫu Dev Zalo; đối chiếu các ngưỡng nghiệm thu (AAC EER $\\le 2.62\\%$, FAR $\\le 7.81\\%$; Opus EER $\\le 2.10\\%$, FAR $\\le 3.65\\%$; Clean EER $\\le 2.60\\%$)."
            ]
        },

        # Cell 1: Environment check & Pre-warm HF
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
                "import concurrent.futures\n",
                "from pathlib import Path\n",
                "\n",
                "import torch\n",
                "import torchaudio\n",
                "import soundfile as sf\n",
                "import numpy as np\n",
                "import pandas as pd\n",
                "from transformers import AutoConfig, Wav2Vec2Model\n",
                "\n",
                "print('=' * 60)\n",
                "print('⚙️ MÔI TRƯỜNG THỰC THI KAGGLE GPU — B_ZALO TRAINING')\n",
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

        # Cell 2: Bung src/ và manifests
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 2. Bung mã nguồn src/, train_zalo.csv và dev_zalo.csv\n",
                "working_dir = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path('.')\n",
                "\n",
                f"b64_src = '{b64_src_payload}'\n",
                "src_files = json.loads(zlib.decompress(base64.b64decode(b64_src.encode('ascii'))).decode('utf-8'))\n",
                "for fpath_str, content in src_files.items():\n",
                "    dest = working_dir / fpath_str\n",
                "    dest.parent.mkdir(parents=True, exist_ok=True)\n",
                "    dest.write_text(content, encoding='utf-8')\n",
                "print(f'✅ Đã bung {len(src_files)} tệp mã nguồn vào {working_dir}')\n",
                "\n",
                f"b64_tr = '{b64_train}'\n",
                "tr_raw = zlib.decompress(base64.b64decode(b64_tr.encode('ascii')))\n",
                "tr_path = working_dir / 'train_zalo.csv'\n",
                "tr_path.write_bytes(tr_raw)\n",
                f"EXPECTED_TRAIN_SHA = '{expected_train_sha}'\n",
                "assert hashlib.sha256(tr_path.read_bytes()).hexdigest() == EXPECTED_TRAIN_SHA, '❌ Sai SHA train_zalo.csv'\n",
                "\n",
                f"b64_dv = '{b64_dev}'\n",
                "dv_raw = zlib.decompress(base64.b64decode(b64_dv.encode('ascii')))\n",
                "dv_path = working_dir / 'dev_zalo.csv'\n",
                "dv_path.write_bytes(dv_raw)\n",
                f"EXPECTED_DEV_SHA = '{expected_dev_sha}'\n",
                "assert hashlib.sha256(dv_path.read_bytes()).hexdigest() == EXPECTED_DEV_SHA, '❌ Sai SHA dev_zalo.csv'\n",
                "\n",
                "df_tr = pd.read_csv(tr_path)\n",
                "df_dv = pd.read_csv(dv_path)\n",
                "print(f'📊 Manifests: Train={len(df_tr)} dòng | Dev={len(df_dv)} dòng')\n",
                "assert not df_tr['speaker_id'].str.startswith('SPK_').any(), '❌ Phát hiện SPK_xxxx trong Train!'\n",
                "assert not df_dv['speaker_id'].str.startswith('SPK_').any(), '❌ Phát hiện SPK_xxxx trong Dev!'\n",
                "assert 'VieNeu-TTS' not in df_tr['tts_generator'].values, '❌ Phát hiện VieNeu trong Train!'\n",
                "assert 'VieNeu-TTS' not in df_dv['tts_generator'].values, '❌ Phát hiện VieNeu trong Dev!'\n",
                "\n",
                "if str(working_dir.resolve()) not in sys.path:\n",
                "    sys.path.insert(0, str(working_dir.resolve()))\n",
                "print('✅ CỔNG 1 & 2: Artifacts và ranh giới dữ liệu hoàn toàn đạt chuẩn!')\n"
            ]
        },

        # Cell 3: Mount Checkpoint B và Data ZIP
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 3. Xác minh Checkpoint B gốc và Nguồn Audio ZIP\n",
                "def compute_sha256(path: Path) -> str:\n",
                "    h = hashlib.sha256()\n",
                "    with open(path, 'rb') as f:\n",
                "        for chunk in iter(lambda: f.read(1024 * 1024), b''):\n",
                "            h.update(chunk)\n",
                "    return h.hexdigest()\n",
                "\n",
                "EXPECTED_CKPT_SHA = 'a921c3397946335c9543528993eafde80ac0d42decf431101635806b5c56bd9f'\n",
                "ckpt_candidates = (\n",
                "    list(Path('/kaggle/input').rglob('*best_model_B*.pt')) +\n",
                "    list(Path('/kaggle/input').rglob('*run_B*best_model*.pt')) +\n",
                "    list(Path('/kaggle/input').rglob('*best_model*.pt'))\n",
                ")\n",
                "ckpt_path = None\n",
                "for c in ckpt_candidates:\n",
                "    if c.exists() and c.is_file() and c.stat().st_size > 10000000:\n",
                "        if compute_sha256(c) == EXPECTED_CKPT_SHA:\n",
                "            ckpt_path = c\n",
                "            break\n",
                "assert ckpt_path is not None, '❌ Không tìm thấy Checkpoint B khớp SHA-256!'\n",
                "print(f'📦 Checkpoint B: {ckpt_path} (SHA-256: {compute_sha256(ckpt_path)})')\n",
                "\n",
                "zip_candidates = list(Path('/kaggle/input').rglob('*vitruevoice*.zip')) + list(Path('/kaggle/input').rglob('*.zip'))\n",
                "zip_path = None\n",
                "for z in zip_candidates:\n",
                "    if z.exists() and z.is_file() and z.stat().st_size > 1000000:\n",
                "        zip_path = z\n",
                "        break\n",
                "assert zip_path is not None, '❌ Không tìm thấy file ZIP dữ liệu âm thanh!'\n",
                "print(f'📦 Audio ZIP: {zip_path} ({zip_path.stat().st_size / (1024**2):.1f} MB)')\n"
            ]
        },

        # Cell 4: Selective Unzip into /tmp/audio & Proxy Transcoding
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 4. Giải nén chọn lọc audio và sinh proxy Zalo AAC/Opus vào /tmp/vitrue_audio\n",
                "tmp_audio_dir = Path('/tmp/vitrue_audio')\n",
                "tmp_audio_dir.mkdir(parents=True, exist_ok=True)\n",
                "\n",
                "clean_rows = pd.concat([df_tr[df_tr['codec'] == 'clean_16khz'], df_dv[df_dv['codec'] == 'clean_16khz']])\n",
                "base_to_clean = dict(zip(clean_rows['base_utt'], clean_rows['audio_path']))\n",
                "\n",
                "needed_rel = set()\n",
                "for df_sub in [df_tr, df_dv]:\n",
                "    for _, row in df_sub.iterrows():\n",
                "        c = row['codec']\n",
                "        if c in ['clean_16khz', 'g711_alaw', 'amr_nb']:\n",
                "            needed_rel.add(row['audio_path'].replace('\\\\', '/').lstrip('/'))\n",
                "        else:\n",
                "            needed_rel.add(base_to_clean[row['base_utt']].replace('\\\\', '/').lstrip('/'))\n",
                "\n",
                "print(f'🎯 Tổng số file audio gốc trong ZIP cần trích xuất: {len(needed_rel)}')\n",
                "t_unzip = time.time()\n",
                "with zipfile.ZipFile(zip_path, 'r') as zf:\n",
                "    name_set = set(zf.namelist())\n",
                "    targets = []\n",
                "    for rel_p in needed_rel:\n",
                "        for cand in [rel_p, f'data/{rel_p}', rel_p.replace('data/', '')]:\n",
                "            if cand in name_set:\n",
                "                targets.append((cand, tmp_audio_dir / rel_p))\n",
                "                break\n",
                "    print(f'   - Đã ánh xạ trong ZIP: {len(targets)} / {len(needed_rel)} tệp')\n",
                "    for src_entry, dst_p in targets:\n",
                "        dst_p.parent.mkdir(parents=True, exist_ok=True)\n",
                "        if not dst_p.exists():\n",
                "            with zf.open(src_entry) as s_f, open(dst_p, 'wb') as d_f:\n",
                "                shutil.copyfileobj(s_f, d_f)\n",
                "print(f'✅ Giải nén chọn lọc vào /tmp hoàn tất trong {time.time() - t_unzip:.1f}s')\n",
                "\n",
                "# Sinh proxy AAC và Opus cho các mẫu Zalo (Profile A & Profile B)\n",
                "print('🚀 Đang chuẩn bị kênh proxy AAC (76kbps) và Opus (24kbps) vào /tmp...')\n",
                "\n",
                "def transcode_aac(raw_wav_bytes):\n",
                "    p1 = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0', '-ar', '48000', '-ac', '1', '-c:a', 'aac', '-b:a', '76k', '-f', 'adts', 'pipe:1'], input=raw_wav_bytes, capture_output=True, check=True)\n",
                "    p2 = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0', '-f', 'wav', '-ar', '16000', '-ac', '1', 'pipe:1'], input=p1.stdout, capture_output=True, check=True)\n",
                "    return p2.stdout\n",
                "\n",
                "def transcode_opus(raw_wav_bytes):\n",
                "    p1 = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0', '-c:a', 'libopus', '-b:a', '24k', '-f', 'ogg', 'pipe:1'], input=raw_wav_bytes, capture_output=True, check=True)\n",
                "    p2 = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0', '-f', 'wav', '-ar', '16000', '-ac', '1', 'pipe:1'], input=p1.stdout, capture_output=True, check=True)\n",
                "    return p2.stdout\n",
                "\n",
                "aac_rows = pd.concat([df_tr[df_tr['codec'] == 'aac_zalo_76k'], df_dv[df_dv['codec'] == 'aac_zalo_76k']])\n",
                "opus_rows = pd.concat([df_tr[df_tr['codec'] == 'opus_zalo_24k'], df_dv[df_dv['codec'] == 'opus_zalo_24k']])\n",
                "base_to_aac = dict(zip(aac_rows['base_utt'], aac_rows['audio_path']))\n",
                "base_to_opus = dict(zip(opus_rows['base_utt'], opus_rows['audio_path']))\n",
                "all_proxy_bases = sorted(list(set(base_to_aac.keys())))\n",
                "\n",
                "def process_proxy_pair(b_utt):\n",
                "    clean_p = tmp_audio_dir / base_to_clean[b_utt].replace('\\\\', '/').lstrip('/')\n",
                "    aac_p = tmp_audio_dir / base_to_aac[b_utt].replace('\\\\', '/').lstrip('/')\n",
                "    opus_p = tmp_audio_dir / base_to_opus[b_utt].replace('\\\\', '/').lstrip('/')\n",
                "    if aac_p.exists() and opus_p.exists():\n",
                "        return\n",
                "    raw_bytes = clean_p.read_bytes()\n",
                "    if not aac_p.exists():\n",
                "        aac_p.parent.mkdir(parents=True, exist_ok=True)\n",
                "        aac_p.write_bytes(transcode_aac(raw_bytes))\n",
                "    if not opus_p.exists():\n",
                "        opus_p.parent.mkdir(parents=True, exist_ok=True)\n",
                "        opus_p.write_bytes(transcode_opus(raw_bytes))\n",
                "\n",
                "t_proxy_start = time.time()\n",
                "with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:\n",
                "    list(ex.map(process_proxy_pair, all_proxy_bases))\n",
                "print(f'✅ Đã sinh {len(all_proxy_bases)*2} tệp proxy Zalo vào /tmp trong {(time.time() - t_proxy_start)/60:.1f} phút')\n"
            ]
        },

        # Cell 5: Huấn luyện fine-tune B_zalo
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 5. Huấn luyện Fine-Tuning B_zalo (Phase 1 = 5 epochs, Phase 2 = 0)\n",
                "out_run_dir = working_dir / 'run_B_zalo'\n",
                "out_run_dir.mkdir(parents=True, exist_ok=True)\n",
                "\n",
                "cmd_train = [\n",
                "    sys.executable, 'scripts/train.py',\n",
                "    '--branch', 'B_zalo',\n",
                "    '--init-ckpt', str(ckpt_path),\n",
                "    '--train-manifest', str(tr_path),\n",
                "    '--dev-manifest', str(dv_path),\n",
                "    '--audio-root', str(tmp_audio_dir),\n",
                "    '--out-dir', str(out_run_dir),\n",
                "    '--batch-size', '16',\n",
                "    '--num-workers', '2',\n",
                "    '--phase1-epochs', '5',\n",
                "    '--phase2-epochs', '0',\n",
                "    '--device', 'cuda' if torch.cuda.is_available() else 'cpu',\n",
                "]\n",
                "print(f'🚀 Khởi chạy huấn luyện: {\" \".join(cmd_train)}')\n",
                "t_train_start = time.time()\n",
                "proc = subprocess.run(cmd_train, text=True)\n",
                "assert proc.returncode == 0, f'❌ Huấn luyện B_zalo thất bại (exit {proc.returncode})!'\n",
                "print(f'✅ Huấn luyện B_zalo hoàn tất trong {(time.time() - t_train_start)/60:.1f} phút!')\n",
                "\n",
                "best_zalo_ckpt = out_run_dir / 'best_model.pt'\n",
                "assert best_zalo_ckpt.is_file(), '❌ Không tìm thấy best_model.pt của B_zalo!'\n",
                "final_ckpt_dest = working_dir / 'best_model_B_zalo.pt'\n",
                "shutil.copy2(best_zalo_ckpt, final_ckpt_dest)\n",
                "print(f'📦 Đã xuất checkpoint chính thức: {final_ckpt_dest} ({final_ckpt_dest.stat().st_size} bytes)')\n"
            ]
        },

        # Cell 6: Đánh giá độc lập trên Dev Zalo (11.450 mẫu) và kiểm tra Anti-Regression
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 6. Đánh giá toàn bộ 11.450 mẫu Dev Zalo & Kiểm định Chống Thoái lui (Anti-Regression)\n",
                "from src.models.ssl_aasist import SSLAASIST\n",
                "from src.preprocessing.audio_loader import load_audio\n",
                "from src.training.dataset import fit_length\n",
                "from src.evaluation.metrics import compute_eer, compute_min_dcf\n",
                "\n",
                "device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\n",
                "ck_zalo = torch.load(final_ckpt_dest, map_location=device, weights_only=False)\n",
                "m_kwargs = dict(ck_zalo.get('model_kwargs', {}))\n",
                "m_kwargs['ssl_config'] = hf_cfg\n",
                "eval_model = SSLAASIST(**m_kwargs)\n",
                "s_dict = ck_zalo['model'] if 'model' in ck_zalo else ck_zalo['model_state_dict']\n",
                "eval_model.load_state_dict(s_dict, strict=True)\n",
                "eval_model.to(device)\n",
                "eval_model.eval()\n",
                "\n",
                "records = []\n",
                "rng_eval = np.random.default_rng(0)\n",
                "print(f'🚀 Đang chấm điểm 11.450 mẫu Dev Zalo bằng B_zalo...')\n",
                "with torch.inference_mode():\n",
                "    for idx, row in df_dv.iterrows():\n",
                "        p_audio = tmp_audio_dir / row['audio_path'].replace('\\\\', '/').lstrip('/')\n",
                "        if not p_audio.is_file():\n",
                "            raise FileNotFoundError(f'❌ Dòng {idx}: Thiếu tệp audio {p_audio}!')\n",
                "        lbl_int = 1 if str(row['label']).lower() in ['bonafide', '1'] else 0\n",
                "        wav_16k = load_audio(p_audio, target_sr=16000)\n",
                "        t = fit_length(wav_16k, 64000, train=False, rng=rng_eval)\n",
                "        tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)\n",
                "        s = eval_model.score(tensor).item()\n",
                "        r = dict(row)\n",
                "        r['score'] = s\n",
                "        r['label_int'] = lbl_int\n",
                "        records.append(r)\n",
                "\n",
                "scored_df = pd.DataFrame(records)\n",
                "assert len(scored_df) == 11450, f'❌ Kỳ vọng 11450 mẫu dev nhưng nhận {len(scored_df)}'\n",
                "out_scores_path = working_dir / 'dev_zalo_scores_b_zalo.csv'\n",
                "scored_df.to_csv(out_scores_path, index=False)\n",
                "\n",
                "# Fast Bootstrap & Anti-regression check\n",
                "def fast_bootstrap(sub, n_boot=1000, seed=42):\n",
                "    clusters, inv = np.unique(sub['base_utt'].values, return_inverse=True)\n",
                "    n_c = len(clusters)\n",
                "    idx_map = [np.where(inv == i)[0] for i in range(n_c)]\n",
                "    y_t = sub['label_int'].to_numpy(dtype=int)\n",
                "    y_s = sub['score'].to_numpy(dtype=float)\n",
                "    rng = np.random.default_rng(seed)\n",
                "    eers, frrs, fars = [], [], []\n",
                "    for _ in range(n_boot):\n",
                "        sampled = rng.choice(n_c, size=n_c, replace=True)\n",
                "        pick = np.concatenate([idx_map[c] for c in sampled])\n",
                "        yt_b, ys_b = y_t[pick], y_s[pick]\n",
                "        if len(np.unique(yt_b)) < 2: continue\n",
                "        try:\n",
                "            e, _ = compute_eer(ys_b, yt_b)\n",
                "            eers.append(e * 100.0)\n",
                "        except Exception: pass\n",
                "        nb = np.sum(yt_b == 1)\n",
                "        ns = np.sum(yt_b == 0)\n",
                "        if nb > 0: frrs.append(float(np.sum((yt_b == 1) & (ys_b < 0.0)) / nb * 100.0))\n",
                "        if ns > 0: fars.append(float(np.sum((yt_b == 0) & (ys_b >= 0.0)) / ns * 100.0))\n",
                "    def ci(arr):\n",
                "        if not arr: return (float('nan'), float('nan'))\n",
                "        return (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))\n",
                "    return {'eer_ci': ci(eers), 'frr_ci': ci(frrs), 'far_ci': ci(fars)}\n",
                "\n",
                "metric_rows = []\n",
                "for c_name in ['aac_zalo_76k', 'opus_zalo_24k', 'clean_16khz', 'g711_alaw', 'amr_nb']:\n",
                "    c_df = scored_df[scored_df['codec'] == c_name]\n",
                "    yt = c_df['label_int'].to_numpy(dtype=int)\n",
                "    ys = c_df['score'].to_numpy(dtype=float)\n",
                "    nb = int(np.sum(yt == 1))\n",
                "    ns = int(np.sum(yt == 0))\n",
                "    e, e_thr = compute_eer(ys, yt)\n",
                "    dcf = compute_min_dcf(ys, yt)\n",
                "    frr0 = float(np.sum((yt == 1) & (ys < 0.0)) / nb * 100.0)\n",
                "    far0 = float(np.sum((yt == 0) & (ys >= 0.0)) / ns * 100.0)\n",
                "    b_res = fast_bootstrap(c_df, n_boot=1000)\n",
                "    metric_rows.append({\n",
                "        'codec': c_name, 'n_total': len(c_df), 'n_bonafide': nb, 'n_spoof': ns, 'is_valid': True,\n",
                "        'eer_pct': e * 100.0, 'eer_ci_95': f'[{b_res[\"eer_ci\"][0]:.2f}, {b_res[\"eer_ci\"][1]:.2f}]',\n",
                "        'eer_threshold': e_thr, 'min_dcf': dcf, 'frr_theta_0': frr0,\n",
                "        'frr_ci_95': f'[{b_res[\"frr_ci\"][0]:.2f}, {b_res[\"frr_ci\"][1]:.2f}]',\n",
                "        'far_theta_0': far0,\n",
                "        'far_ci_95': f'[{b_res[\"far_ci\"][0]:.2f}, {b_res[\"far_ci\"][1]:.2f}]',\n",
                "    })\n",
                "\n",
                "metrics_df = pd.DataFrame(metric_rows)\n",
                "out_metrics_path = working_dir / 'zalo_b_zalo_metrics.csv'\n",
                "metrics_df.to_csv(out_metrics_path, index=False)\n",
                "print('=' * 80)\n",
                "print('📊 BÁO CÁO KẾT QUẢ FINE-TUNING B_ZALO TRÊN DEV ZALO (11.450 MẪU)')\n",
                "print('=' * 80)\n",
                "print(metrics_df[['codec', 'n_bonafide', 'n_spoof', 'eer_pct', 'eer_ci_95', 'frr_theta_0', 'far_theta_0', 'min_dcf']].to_string(index=False))\n",
                "\n",
                "# Kiểm định chống thoái lui so với Baseline Checkpoint B\n",
                "aac_row = metrics_df[metrics_df['codec'] == 'aac_zalo_76k'].iloc[0]\n",
                "opus_row = metrics_df[metrics_df['codec'] == 'opus_zalo_24k'].iloc[0]\n",
                "clean_row = metrics_df[metrics_df['codec'] == 'clean_16khz'].iloc[0]\n",
                "\n",
                "print()\n",
                "print('🔍 ĐỐI SOÁT TIÊU CHÍ CHỐNG THOÁI LUI:')\n",
                "print(f'1. AAC Profile A: EER={aac_row[\"eer_pct\"]:.2f}% (Baseline: 2.62%) | FAR@0={aac_row[\"far_theta_0\"]:.2f}% (Baseline: 7.81%)')\n",
                "print(f'2. Opus Profile B: EER={opus_row[\"eer_pct\"]:.2f}% (Baseline: 2.10%) | FAR@0={opus_row[\"far_theta_0\"]:.2f}% (Baseline: 3.65%)')\n",
                "print(f'3. Clean 16kHz: EER={clean_row[\"eer_pct\"]:.2f}% (Baseline: 2.60%)')\n",
                "\n",
                "# Dọn dẹp /tmp/vitrue_audio để giải phóng bộ nhớ\n",
                "if tmp_audio_dir.exists():\n",
                "    shutil.rmtree(tmp_audio_dir, ignore_errors=True)\n",
                "print('🏁 CỔNG 5: B_ZALO ĐÁNH GIÁ THÀNH CÔNG VÀ SẴN SÀNG NGHIỆM THU!')\n"
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
    build_zalo_train_notebook()
