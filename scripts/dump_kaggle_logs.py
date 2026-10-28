import json
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    api = KaggleApi()
    api.authenticate()
    kernel_id = 'nguyenthanhtai1959/vietrue-model-training'

    print("Fetching logs...")
    raw_logs = api.kernels_logs(kernel_id)
    if isinstance(raw_logs, str):
        try:
            log_entries = json.loads(raw_logs)
        except Exception:
            log_entries = None
    else:
        log_entries = raw_logs

    if isinstance(log_entries, list):
        stdout_lines = [e.get('data', '') for e in log_entries if e.get('stream_name') == 'stdout']
        stderr_lines = [e.get('data', '') for e in log_entries if e.get('stream_name') == 'stderr']
        
        full_stdout = "".join(stdout_lines)
        full_stderr = "".join(stderr_lines)
        
        Path("out").mkdir(exist_ok=True)
        with open("out/kaggle_stdout.log", "w", encoding="utf-8") as f:
            f.write(full_stdout)
        with open("out/kaggle_stderr.log", "w", encoding="utf-8") as f:
            f.write(full_stderr)
        
        print(f"Stdout length: {len(full_stdout)} chars, written to out/kaggle_stdout.log")
        print(f"Stderr length: {len(full_stderr)} chars, written to out/kaggle_stderr.log")
    else:
        print("Logs format unrecognized:", type(raw_logs))

if __name__ == '__main__':
    main()
