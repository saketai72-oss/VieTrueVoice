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
        # Cell 0: Markdown Title & Abstract
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# ViTrueVoice — Pipeline Huấn Luyện SSL-AASIST & Đánh Giá Đối Chứng H1/H2 Trên Kaggle GPU\n",
                "\n",
                "**Mục tiêu thí nghiệm (Must #2 - W5)**:\n",
                "1. **Huấn luyện 3 nhánh thí nghiệm**:\n",
                "   - **Nhánh A (Không tăng cường)**: `mode=\"clean\"` (10.699 mẫu), không transform, Phase 1 = 4 epochs, Phase 2 = 60 epochs (nhân 3 để cân bằng optimizer steps).\n",
                "   - **Nhánh B0 (Chỉ nén Codec, không RawBoost)**: `mode=\"augmented\"` (31.327 mẫu), không transform, Phase 1 = 4 epochs, Phase 2 = 20 epochs.\n",
                "   - **Nhánh B (ViTrueVoice Đầy đủ: Codec + RawBoost)**: `mode=\"augmented\"` (31.327 mẫu), `make_rawboost()`, Phase 1 = 4 epochs, Phase 2 = 20 epochs.\n",
                "2. **Đánh giá tự động trên Test In-domain và Test OOD** qua `scripts/eval_ssl_aasist.py`.\n",
                "3. **Kiểm chứng giả thuyết khoa học** qua `scripts/compare_h1.py`:\n",
                "   - **H1**: Giảm $\\ge 30\\%$ EER tương đối trên kênh nén (G.711 A-law, AMR-NB) so với Mô hình A.\n",
                "   - **H2**: EER $\\le 15\\%$ trên công cụ TTS chưa từng thấy (`VieNeu-TTS`).\n",
                "   - **Phân rã biến**: So sánh B0 vs B để bóc tách chính xác đóng góp của RawBoost.\n"
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
        # Cell 3: Data Discovery & Unpack
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 3. Định vị dữ liệu âm thanh và các tệp Manifest\n",
                "import zipfile\n",
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
                "    # Tìm file ZIP đã nén từ Phase 1\n",
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
                "print('✅ Đã xác thực đầy đủ các tệp manifest bắt buộc.')\n"
            ]
        },
        # Cell 4: Train Branch A
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 4. Huấn luyện Mô hình A (Không tăng cường - Baseline SSL-AASIST)\n",
                "# mode='clean' (10.699 mẫu sạch), transform=None, Phase 1 = 4 ep, Phase 2 = 60 ep\n",
                "import subprocess\n",
                "import sys\n",
                "\n",
                "cmd_A = [\n",
                "    sys.executable, 'scripts/train.py',\n",
                "    '--branch', 'A',\n",
                "    '--manifest-dir', str(manifest_dir),\n",
                "    '--audio-root', str(audio_root),\n",
                "    '--out-dir', 'out/run_A',\n",
                "    '--batch-size', '16',\n",
                "]\n",
                "print(f'🚀 Bắt đầu huấn luyện Nhánh A...\\nLệnh: {\" \".join(cmd_A)}')\n",
                "res = subprocess.run(cmd_A)\n",
                "assert res.returncode == 0, f'❌ Huấn luyện Nhánh A thất bại với mã lỗi {res.returncode}'\n",
                "print('✅ Huấn luyện Nhánh A hoàn tất!')\n"
            ]
        },
        # Cell 5: Train Branch B0
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 5. Huấn luyện Mô hình B0 (Chỉ nén Codec, không RawBoost)\n",
                "# mode='augmented' (31.327 mẫu), transform=None, Phase 1 = 4 ep, Phase 2 = 20 ep\n",
                "import subprocess\n",
                "import sys\n",
                "\n",
                "cmd_B0 = [\n",
                "    sys.executable, 'scripts/train.py',\n",
                "    '--branch', 'B0',\n",
                "    '--manifest-dir', str(manifest_dir),\n",
                "    '--audio-root', str(audio_root),\n",
                "    '--out-dir', 'out/run_B0',\n",
                "    '--batch-size', '16',\n",
                "]\n",
                "print(f'🚀 Bắt đầu huấn luyện Nhánh B0...\\nLệnh: {\" \".join(cmd_B0)}')\n",
                "res = subprocess.run(cmd_B0)\n",
                "assert res.returncode == 0, f'❌ Huấn luyện Nhánh B0 thất bại với mã lỗi {res.returncode}'\n",
                "print('✅ Huấn luyện Nhánh B0 hoàn tất!')\n"
            ]
        },
        # Cell 6: Train Branch B
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 6. Huấn luyện Mô hình B (ViTrueVoice Đầy Đủ: Codec + RawBoost Online)\n",
                "# mode='augmented' (31.327 mẫu), transform=make_rawboost(), Phase 1 = 4 ep, Phase 2 = 20 ep\n",
                "import subprocess\n",
                "import sys\n",
                "\n",
                "cmd_B = [\n",
                "    sys.executable, 'scripts/train.py',\n",
                "    '--branch', 'B',\n",
                "    '--manifest-dir', str(manifest_dir),\n",
                "    '--audio-root', str(audio_root),\n",
                "    '--out-dir', 'out/run_B',\n",
                "    '--batch-size', '16',\n",
                "]\n",
                "print(f'🚀 Bắt đầu huấn luyện Nhánh B...\\nLệnh: {\" \".join(cmd_B)}')\n",
                "res = subprocess.run(cmd_B)\n",
                "assert res.returncode == 0, f'❌ Huấn luyện Nhánh B thất bại với mã lỗi {res.returncode}'\n",
                "print('✅ Huấn luyện Nhánh B hoàn tất!')\n"
            ]
        },
        # Cell 7: Automated Evaluation on Test Sets
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 7. Đánh giá tự động các mô hình trên Test Sets (In-domain & OOD)\n",
                "import os\n",
                "import subprocess\n",
                "import sys\n",
                "\n",
                "manifest_args = [f'in_domain={manifest_dir}/test_indomain.csv']\n",
                "if (manifest_dir / 'test_ood.csv').exists():\n",
                "    manifest_args.append(f'ood={manifest_dir}/test_ood.csv')\n",
                "\n",
                "for branch in ['A', 'B0', 'B']:\n",
                "    ckpt = f'out/run_{branch}/best_model.pt'\n",
                "    if os.path.exists(ckpt):\n",
                "        print(f'\\n{\"=\"*60}\\n🔍 Đang chấm điểm Model {branch} ({ckpt})...\\n{\"=\"*60}')\n",
                "        cmd_eval = [\n",
                "            sys.executable, 'scripts/eval_ssl_aasist.py',\n",
                "            '--ckpt', ckpt,\n",
                "            '--manifest', *manifest_args,\n",
                "            '--audio-root', str(audio_root),\n",
                "            '--role', 'eval',\n",
                "            '--out', f'out/eval_metrics_{branch}.csv',\n",
                "            '--scores-out', f'out/scores_{branch}.csv',\n",
                "        ]\n",
                "        res = subprocess.run(cmd_eval)\n",
                "        assert res.returncode == 0, f'❌ Đánh giá Model {branch} thất bại'\n",
                "    else:\n",
                "        print(f'⚠️ Checkpoint không tồn tại: {ckpt}')\n"
            ]
        },
        # Cell 8: Hypothesis Verification (H1 and H2)
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 8. Kiểm chứng giả thuyết khoa học H1 & H2\n",
                "import os\n",
                "import subprocess\n",
                "import sys\n",
                "\n",
                "if os.path.exists('out/eval_metrics_A.csv') and os.path.exists('out/eval_metrics_B.csv'):\n",
                "    print('=' * 75)\n",
                "    print('📊 ĐỐI CHỨNG GIẢ THUYẾT H1 & H2 (MÔ HÌNH A vs MÔ HÌNH B):')\n",
                "    print('=' * 75)\n",
                "    cmd_h1 = [\n",
                "        sys.executable, 'scripts/compare_h1.py',\n",
                "        '--a', 'out/eval_metrics_A.csv',\n",
                "        '--b', 'out/eval_metrics_B.csv',\n",
                "        '--out-dir', 'out/comparison_A_B',\n",
                "    ]\n",
                "    subprocess.run(cmd_h1, check=True)\n",
                "\n",
                "if os.path.exists('out/eval_metrics_B0.csv') and os.path.exists('out/eval_metrics_B.csv'):\n",
                "    print('\\n' + '=' * 75)\n",
                "    print('📊 ĐỐI CHỨNG BÓC TÁCH ĐÓNG GÓP RAWBOOST (MÔ HÌNH B0 vs MÔ HÌNH B):')\n",
                "    print('=' * 75)\n",
                "    cmd_b0 = [\n",
                "        sys.executable, 'scripts/compare_h1.py',\n",
                "        '--a', 'out/eval_metrics_B0.csv',\n",
                "        '--b', 'out/eval_metrics_B.csv',\n",
                "        '--out-dir', 'out/comparison_B0_B',\n",
                "    ]\n",
                "    subprocess.run(cmd_b0, check=True)\n"
            ]
        },
        # Cell 9: Display Markdown Summary
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 9. Hiển thị báo cáo tóm tắt Markdown trên Notebook\n",
                "from pathlib import Path\n",
                "from IPython.display import display, Markdown\n",
                "\n",
                "rep = Path('out/comparison_A_B/h1_h2_summary.md')\n",
                "if rep.exists():\n",
                "    display(Markdown(rep.read_text(encoding='utf-8')))\n"
            ]
        },
        # Cell 10: Copy artifacts to working dir for easy Kaggle output download
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 10. Đóng gói kết quả đầu ra cho Kaggle Output\n",
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
                "print(f'Tải kết quả về máy local: python manage_kaggle.py output')\n"
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
