#!/usr/bin/env python3
"""Tạo notebook train_kaggle.ipynb đóng gói toàn bộ mã nguồn src/ và scripts/
để chạy huấn luyện 3 nhánh (A, B0, B) và đối chứng H1/H2 trên Kaggle GPU."""

import base64
import json
import zlib
from pathlib import Path


def build_notebook(out_path: Path = Path("train_kaggle.ipynb")) -> None:
    # 1. Đóng gói mã nguồn src/ và scripts/ vào payload b64
    pkg = {}
    for p in sorted(list(Path("src").rglob("*.py")) + list(Path("scripts").rglob("*.py"))):
        if "__pycache__" in str(p) or "build_train_kaggle" in str(p) or "update_train" in str(p):
            continue
        pkg[p.as_posix()] = p.read_text(encoding="utf-8")

    compressed = zlib.compress(json.dumps(pkg).encode("utf-8"))
    b64_payload = base64.b64encode(compressed).decode("ascii")

    cells = [
        # Cell 0: Markdown Title & Experimental Abstract
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# ViTrueVoice — Pipeline Huấn Luyện SSL-AASIST & Đánh Giá Đối Chứng H1/H2 Trên Kaggle GPU\n",
                "\n",
                "**Mục tiêu thí nghiệm (Must #2 - W5)**:\n",
                "1. **Chạy thử nhanh (Smoke Test)**: 100 mẫu, 1 epoch để xác nhận đường ống, tải mô hình và đường dẫn âm thanh.\n",
                "2. **Huấn luyện 3 nhánh thí nghiệm chính thức**:\n",
                "   - **Nhánh A (Không tăng cường)**: `mode=\"clean\"` (10.699 mẫu), không transform, Phase 1 = 4 epochs, Phase 2 = 60 epochs (nhân 3 để cân bằng optimizer steps).\n",
                "   - **Nhánh B0 (Chỉ nén Codec, không RawBoost)**: `mode=\"augmented\"` (31.327 mẫu), không transform, Phase 1 = 4 epochs, Phase 2 = 20 epochs.\n",
                "   - **Nhánh B (ViTrueVoice Đầy đủ: Codec + RawBoost)**: `mode=\"augmented\"` (31.327 mẫu), `make_rawboost()`, Phase 1 = 4 epochs, Phase 2 = 20 epochs.\n",
                "3. **Đánh giá tự động trên Test In-domain và Test OOD** qua `scripts/eval_ssl_aasist.py`.\n",
                "4. **Kiểm chứng giả thuyết khoa học** qua `scripts/compare_h1.py`:\n",
                "   - **H1**: Giảm $\\ge 30\\%$ EER tương đối trên kênh nén (G.711 A-law, AMR-NB) so với Mô hình A.\n",
                "   - **H2**: EER $\\le 15\\%$ trên công cụ TTS chưa từng thấy (`VieNeu-TTS`).\n",
                "   - **Phân rã biến**: So sánh B0 vs B để bóc tách chính xác đóng góp của RawBoost (đọc `delta_rel_pct` và `ci_overlap`).\n"
            ]
        },
        # Cell 1: Environment & GPU Check
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 1. Cài đặt phụ thuộc & Kiểm tra GPU\n",
                "import subprocess\n",
                "import sys\n",
                "import torch\n",
                "\n",
                "print('📦 Đang kiểm tra & cài đặt thư viện phụ thuộc...')\n",
                "subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'soundfile', 'librosa', 'transformers'], check=False)\n",
                "\n",
                "print('=' * 60)\n",
                "print(f'PyTorch Version : {torch.__version__}')\n",
                "print(f'CUDA Available  : {torch.cuda.is_available()}')\n",
                "if torch.cuda.is_available():\n",
                "    print(f'GPU Device      : {torch.cuda.get_device_name(0)}')\n",
                "    print(f'VRAM            : {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB')\n",
                "else:\n",
                "    print('⚠️ CẢNH BÁO: Không có GPU! Huấn luyện SSL-AASIST trên CPU sẽ rất chậm.')\n",
                "print('=' * 60)\n"
            ]
        },
        # Cell 2: Codebase Deployer
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 2. Khởi tạo mã nguồn ViTrueVoice trên Kaggle container\n",
                "import base64\n",
                "import zlib\n",
                "import json\n",
                "import sys\n",
                "from pathlib import Path\n",
                "\n",
                f"PKG_B64 = '{b64_payload}'\n",
                "\n",
                "pkg_data = json.loads(zlib.decompress(base64.b64decode(PKG_B64.encode('ascii'))).decode('utf-8'))\n",
                "working_dir = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path('.')\n",
                "\n",
                "for rel_path, content in pkg_data.items():\n",
                "    file_path = working_dir / rel_path\n",
                "    file_path.parent.mkdir(parents=True, exist_ok=True)\n",
                "    file_path.write_text(content, encoding='utf-8')\n",
                "\n",
                "if str(working_dir) not in sys.path:\n",
                "    sys.path.insert(0, str(working_dir))\n",
                "\n",
                "print(f'✅ Đã khởi tạo thành công {len(pkg_data)} files mã nguồn tại: {working_dir}')\n"
            ]
        },
        # Cell 3: Data Discovery & Audio Path Verification
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 3. Định vị dữ liệu âm thanh, tệp Manifest và Kiểm tra đường dẫn âm thanh\n",
                "import zipfile\n",
                "import pandas as pd\n",
                "from pathlib import Path\n",
                "\n",
                "working_dir = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path('.')\n",
                "\n",
                "# Kiểm tra nếu dữ liệu đã tồn tại sẵn\n",
                "candidates = [\n",
                "    working_dir / 'data',\n",
                "    Path('/kaggle/input/vietrue-model-training/data'),\n",
                "    Path('/kaggle/input/vitruevoice-data-processed/data'),\n",
                "    Path('/kaggle/input/vietruevoice-processed/data'),\n",
                "    Path('./data'),\n",
                "]\n",
                "\n",
                "data_dir = None\n",
                "for c in candidates:\n",
                "    if c.exists() and (c / 'manifests' / 'train.csv').exists():\n",
                "        data_dir = c\n",
                "        break\n",
                "\n",
                "if not data_dir:\n",
                "    # Tìm file ZIP đã nén từ kernel sinh dữ liệu vietrue-model-training\n",
                "    zip_candidates = (\n",
                "        list(Path('/kaggle/input').rglob('*vitruevoice*.zip')) +\n",
                "        list(working_dir.glob('*vitruevoice*.zip')) +\n",
                "        list(Path('out').glob('*vitruevoice*.zip'))\n",
                "    )\n",
                "    if zip_candidates:\n",
                "        zip_path = zip_candidates[0]\n",
                "        print(f'📦 Tìm thấy file nén dữ liệu: {zip_path}. Đang giải nén...')\n",
                "        with zipfile.ZipFile(zip_path, 'r') as zf:\n",
                "            zf.extractall(working_dir)\n",
                "        data_dir = working_dir / 'data'\n",
                "        print(f'✅ Đã giải nén vào {data_dir}')\n",
                "\n",
                "if data_dir and (data_dir / 'manifests' / 'train.csv').exists():\n",
                "    manifest_dir = data_dir / 'manifests'\n",
                "    audio_root = working_dir\n",
                "else:\n",
                "    # Fallback kiểm tra thư mục manifests trực tiếp\n",
                "    manifest_dir = Path('data/manifests') if Path('data/manifests/train.csv').exists() else Path('out')\n",
                "    audio_root = Path('.')\n",
                "\n",
                "print(f'📂 Manifest Directory: {manifest_dir}')\n",
                "print(f'🎵 Audio Root        : {audio_root}')\n",
                "assert (manifest_dir / 'train.csv').exists(), f'❌ Không tìm thấy train.csv tại {manifest_dir}!'\n",
                "assert (manifest_dir / 'dev.csv').exists(), f'❌ Không tìm thấy dev.csv tại {manifest_dir}!'\n",
                "assert (manifest_dir / 'test_indomain.csv').exists(), f'❌ Không tìm thấy test_indomain.csv tại {manifest_dir}!'\n",
                "\n",
                "# Kiểm tra xác thực đường dẫn file âm thanh mẫu thực tế\n",
                "train_sample_df = pd.read_csv(manifest_dir / 'train.csv', nrows=5)\n",
                "sample_rel_path = train_sample_df['audio_path'].iloc[0]\n",
                "sample_full_path = audio_root / sample_rel_path\n",
                "print(f'🔍 Kiểm tra file âm thanh mẫu: {sample_full_path}')\n",
                "assert sample_full_path.exists(), f'❌ Không tìm thấy file âm thanh mẫu tại {sample_full_path}!'\n",
                "print('✅ Đường dẫn âm thanh mẫu hoàn toàn hợp lệ!')\n"
            ]
        },
        # Cell 4: Shared Subprocess Runner with Proper PYTHONPATH and Unbuffered Logging
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 4. Hàm thực thi subprocess dùng chung (kế thừa PYTHONPATH và log realtime)\n",
                "import os\n",
                "import subprocess\n",
                "import sys\n",
                "from pathlib import Path\n",
                "\n",
                "WORK = Path('/kaggle/working').resolve() if Path('/kaggle/working').exists() else Path('.').resolve()\n",
                "ENV = {\n",
                "    **os.environ,\n",
                "    'PYTHONPATH': f\"{WORK}:{os.environ.get('PYTHONPATH', '')}\",\n",
                "    'PYTHONUNBUFFERED': '1',\n",
                "}\n",
                "\n",
                "def run(cmd, name):\n",
                "    \"\"\"Chạy lệnh từ thư mục gốc dự án, có PYTHONPATH, log hiện theo thời gian thực.\"\"\"\n",
                "    print(f'\\n{\"=\"*75}\\n🚀 {name}\\nLệnh: {\" \".join(map(str, cmd))}\\n{\"=\"*75}', flush=True)\n",
                "    res = subprocess.run([str(c) for c in cmd], cwd=WORK, env=ENV)\n",
                "    assert res.returncode == 0, f'❌ {name} thất bại (mã {res.returncode})'\n",
                "\n",
                "print('✅ Đã khởi tạo hàm run() với PYTHONPATH =', ENV['PYTHONPATH'])\n"
            ]
        },
        # Cell 5: Smoke Test (Quick 1-epoch dry-run on 100 samples)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 5. Kiểm thử nhanh (Smoke Test) xác nhận toàn bộ đường ống trước khi chạy chính thức\n",
                "# Chạy 100 mẫu, Phase 1 = 1 epoch, Phase 2 = 0 epoch\n",
                "run([\n",
                "    sys.executable, '-u', 'scripts/train.py',\n",
                "    '--branch', 'A',\n",
                "    '--manifest-dir', str(manifest_dir),\n",
                "    '--audio-root', str(audio_root),\n",
                "    '--out-dir', 'out/smoke_test',\n",
                "    '--batch-size', '16',\n",
                "    '--limit', '100',\n",
                "    '--phase1-epochs', '1',\n",
                "    '--phase2-epochs', '0',\n",
                "], 'Smoke Test (100 mẫu, 1 epoch)')\n"
            ]
        },
        # Cell 6: Train Branch A (Full)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 6. Huấn luyện Mô hình A (Không tăng cường - Baseline SSL-AASIST)\n",
                "# mode='clean' (10.699 mẫu sạch), transform=None, Phase 1 = 4 ep, Phase 2 = 60 ep\n",
                "run([\n",
                "    sys.executable, '-u', 'scripts/train.py',\n",
                "    '--branch', 'A',\n",
                "    '--manifest-dir', str(manifest_dir),\n",
                "    '--audio-root', str(audio_root),\n",
                "    '--out-dir', 'out/run_A',\n",
                "    '--batch-size', '16',\n",
                "], 'Huấn luyện Nhánh A (Clean Baseline)')\n"
            ]
        },
        # Cell 7: Train Branch B0 (Full)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 7. Huấn luyện Mô hình B0 (Chỉ nén Codec, không RawBoost)\n",
                "# mode='augmented' (31.327 mẫu), transform=None, Phase 1 = 4 ep, Phase 2 = 20 ep\n",
                "run([\n",
                "    sys.executable, '-u', 'scripts/train.py',\n",
                "    '--branch', 'B0',\n",
                "    '--manifest-dir', str(manifest_dir),\n",
                "    '--audio-root', str(audio_root),\n",
                "    '--out-dir', 'out/run_B0',\n",
                "    '--batch-size', '16',\n",
                "], 'Huấn luyện Nhánh B0 (Codec only)')\n"
            ]
        },
        # Cell 8: Train Branch B (Full)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 8. Huấn luyện Mô hình B (ViTrueVoice Đầy Đủ: Codec + RawBoost Online)\n",
                "# mode='augmented' (31.327 mẫu), transform=make_rawboost(), Phase 1 = 4 ep, Phase 2 = 20 ep\n",
                "run([\n",
                "    sys.executable, '-u', 'scripts/train.py',\n",
                "    '--branch', 'B',\n",
                "    '--manifest-dir', str(manifest_dir),\n",
                "    '--audio-root', str(audio_root),\n",
                "    '--out-dir', 'out/run_B',\n",
                "    '--batch-size', '16',\n",
                "], 'Huấn luyện Nhánh B (ViTrueVoice Đầy Đủ)')\n"
            ]
        },
        # Cell 9: Automated Evaluation on Test Sets
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 9. Đánh giá tự động các mô hình trên Test Sets (In-domain & OOD)\n",
                "manifest_args = [f'in_domain={manifest_dir}/test_indomain.csv']\n",
                "if (manifest_dir / 'test_ood.csv').exists():\n",
                "    manifest_args.append(f'ood={manifest_dir}/test_ood.csv')\n",
                "    print('ℹ️ Đã phát hiện và bổ sung test_ood.csv vào danh sách đánh giá.')\n",
                "else:\n",
                "    print('⚠️ Lưu ý: Chưa phát hiện test_ood.csv, đánh giá H2 sẽ dựa trên test_indomain.csv.')\n",
                "\n",
                "for branch in ['A', 'B0', 'B']:\n",
                "    ckpt = f'out/run_{branch}/best_model.pt'\n",
                "    if Path(ckpt).exists():\n",
                "        run([\n",
                "            sys.executable, '-u', 'scripts/eval_ssl_aasist.py',\n",
                "            '--ckpt', ckpt,\n",
                "            '--manifest', *manifest_args,\n",
                "            '--audio-root', str(audio_root),\n",
                "            '--role', 'eval',\n",
                "            '--out', f'out/eval_metrics_{branch}.csv',\n",
                "            '--scores-out', f'out/scores_{branch}.csv',\n",
                "        ], f'Chấm điểm mô hình {branch}')\n",
                "    else:\n",
                "        print(f'⚠️ Checkpoint không tồn tại: {ckpt}')\n"
            ]
        },
        # Cell 10: Hypothesis Verification (H1 and H2)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 10. Kiểm chứng giả thuyết khoa học H1 & H2\n",
                "# 10a. Đối chứng chính thức H1 & H2 giữa Mô hình A (Không tăng cường) và B (ViTrueVoice)\n",
                "if Path('out/eval_metrics_A.csv').exists() and Path('out/eval_metrics_B.csv').exists():\n",
                "    run([\n",
                "        sys.executable, '-u', 'scripts/compare_h1.py',\n",
                "        '--a', 'out/eval_metrics_A.csv',\n",
                "        '--b', 'out/eval_metrics_B.csv',\n",
                "        '--out-dir', 'out/comparison_A_B',\n",
                "    ], 'H1/H2 A vs B')\n",
                "\n",
                "# 10b. Đối chứng bóc tách đóng góp của RawBoost (B0 vs B)\n",
                "# Lưu ý: Đọc delta_rel_pct và ci_overlap để đo lường RawBoost, không trích verdict H1 từ cặp này.\n",
                "if Path('out/eval_metrics_B0.csv').exists() and Path('out/eval_metrics_B.csv').exists():\n",
                "    run([\n",
                "        sys.executable, '-u', 'scripts/compare_h1.py',\n",
                "        '--a', 'out/eval_metrics_B0.csv',\n",
                "        '--b', 'out/eval_metrics_B.csv',\n",
                "        '--out-dir', 'out/comparison_B0_B',\n",
                "    ], 'B0 vs B (Phân rã RawBoost: đọc delta_rel_pct & ci_overlap)')\n"
            ]
        },
        # Cell 11: Display Markdown Summary
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 11. Hiển thị báo cáo tóm tắt Markdown trên Notebook\n",
                "from IPython.display import display, Markdown\n",
                "\n",
                "rep_ab = Path('out/comparison_A_B/h1_h2_summary.md')\n",
                "if rep_ab.exists():\n",
                "    print('=' * 80)\n",
                "    print('📌 KẾT QUẢ ĐỐI CHỨNG GIẢ THUYẾT H1 & H2 (MÔ HÌNH A vs MÔ HÌNH B):')\n",
                "    print('=' * 80)\n",
                "    display(Markdown(rep_ab.read_text(encoding='utf-8')))\n",
                "\n",
                "rep_b0b = Path('out/comparison_B0_B/h1_h2_summary.md')\n",
                "if rep_b0b.exists():\n",
                "    print('\\n' + '=' * 80)\n",
                "    print('📌 PHÂN RÃ ĐÓNG GÓP RIÊNG BIỆT CỦA RAWBOOST (MÔ HÌNH B0 vs MÔ HÌNH B):')\n",
                "    print('=' * 80)\n",
                "    display(Markdown(rep_b0b.read_text(encoding='utf-8')))\n"
            ]
        },
        # Cell 12: Package outputs to working dir for easy Kaggle output download
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 12. Đóng gói kết quả đầu ra cho Kaggle Output\n",
                "import shutil\n",
                "from pathlib import Path\n",
                "\n",
                "working_dir = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path('.')\n",
                "out_dir = Path('out')\n",
                "\n",
                "# Copy các file báo cáo và metrics ra root working_dir để dễ tải\n",
                "for f in out_dir.rglob('*.csv'):\n",
                "    shutil.copy(f, working_dir / f.name)\n",
                "for f in out_dir.rglob('*.md'):\n",
                "    shutil.copy(f, working_dir / f.name)\n",
                "\n",
                "for branch in ['A', 'B0', 'B']:\n",
                "    ckpt = out_dir / f'run_{branch}' / 'best_model.pt'\n",
                "    if ckpt.exists():\n",
                "        shutil.copy(ckpt, working_dir / f'best_model_{branch}.pt')\n",
                "\n",
                "print('🎉 ĐÃ HOÀN TẤT TOÀN BỘ PIPELINE HUẤN LUYỆN VÀ ĐÁNH GIÁ ĐỐI CHỨNG!')\n",
                "print('Tải kết quả về máy local: python manage_kaggle.py output')\n"
            ]
        }
    ]

    notebook_content = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.12.4"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    out_path.write_text(json.dumps(notebook_content, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Đã tạo thành công notebook {out_path} ({len(cells)} cells, {len(pkg)} packaged files)!")


if __name__ == "__main__":
    build_notebook()
