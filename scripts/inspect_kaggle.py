import sys
import json
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    api = KaggleApi()
    api.authenticate()
    kernel_id = 'nguyenthanhtai1959/vietrue-model-training'

    all_files = []
    page_token = None
    page = 1
    while True:
        res = api.kernels_list_files(kernel_id, page_token=page_token, page_size=100)
        files = res.files or []
        all_files.extend(files)
        print(f"Page {page}: fetched {len(files)} files (total: {len(all_files)})", flush=True)
        page_token = res.next_page_token
        if not page_token:
            break
        page += 1

    print(f"\nTotal files in output: {len(all_files)}", flush=True)
    
    print("\nManifest & Result files in output:")
    for f in all_files:
        name = getattr(f, 'name', str(f))
        size = getattr(f, 'totalBytes', getattr(f, 'size', None))
        if not name.endswith('_done.json'):
            print(f"  {name} ({size} bytes)", flush=True)

    checkpoints = [f for f in all_files if getattr(f, 'name', str(f)).endswith('_done.json')]
    print(f"\nTotal speaker checkpoints (_done.json): {len(checkpoints)}", flush=True)
    spk_names = [getattr(f, 'name', str(f)).split('/')[-1].replace('_done.json', '') for f in checkpoints]
    vivos_spks = [s for s in spk_names if s.startswith('VIVOS')]
    cv_spks = [s for s in spk_names if s.startswith('CV_')]
    print(f"  VIVOS speakers: {len(vivos_spks)} / 65: {vivos_spks[:5]} ... {vivos_spks[-5:]}", flush=True)
    print(f"  Common Voice speakers: {len(cv_spks)} / 25: {cv_spks[:5]} ... {cv_spks[-5:]}", flush=True)

if __name__ == '__main__':
    main()
