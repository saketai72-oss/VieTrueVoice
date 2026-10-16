import os
import sys
import time
import json
from pathlib import Path

# Kiểm tra xem đang chạy trên Kaggle hay Local
IS_KAGGLE = os.path.exists("/kaggle")

if IS_KAGGLE:
    INPUT_DIR = Path("/kaggle/input")
    OUTPUT_DIR = Path("/kaggle/working")
    print("🚀 Đang chạy trên Kaggle Cloud Environment!")
else:
    INPUT_DIR = Path("./data")
    OUTPUT_DIR = Path("./out")
    print("💻 Đang chạy trên Local Machine!")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def check_system():
    print("=" * 50)
    print("Thông tin môi trường:")
    try:
        import torch
        print(f"PyTorch Version: {torch.__version__}")
        print(f"CUDA Available : {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU Device     : {torch.cuda.get_device_name(0)}")
            print(f"Device Count   : {torch.cuda.device_count()}")
        else:
            print("⚠️ Không tìm thấy GPU, đang chạy trên CPU.")
    except ImportError:
        print("PyTorch chưa được cài đặt trong môi trường hiện tại.")
    print("=" * 50)

def list_datasets():
    print("\n📂 Danh sách Dataset hiện có:")
    if INPUT_DIR.exists():
        items = list(INPUT_DIR.iterdir())
        if items:
            for item in items:
                print(f" - {item.name} ({'Thư mục' if item.is_dir() else 'Tập tin'})")
        else:
            print(" (Thư mục input trống)")
    else:
        print(f" (Thư mục {INPUT_DIR} chưa tồn tại)")

def main():
    check_system()
    list_datasets()
    
    print("\n🎯 Bắt đầu công việc huấn luyện (Training Job)...")
    # Viết code huấn luyện mô hình của bạn ở đây:
    # Ví dụ:
    # model = MyModel()
    # train(model, dataset)
    
    # Giả lập quá trình chạy và lưu kết quả
    for step in range(1, 4):
        print(f"Step {step}/3 đang xử lý...")
        time.sleep(1)
        
    result_file = OUTPUT_DIR / "training_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump({
            "status": "success",
            "message": "Huấn luyện hoàn tất thành công trên Kaggle GPU!",
            "timestamp": time.time()
        }, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Đã lưu kết quả tại: {result_file}")
    print("Mọi file trong /kaggle/working/ sẽ có thể tải về local bằng lệnh output.")

if __name__ == "__main__":
    main()
