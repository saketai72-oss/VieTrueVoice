# REF_developer-reference — Developer reference tables

> Reference only. Rules live in `docs/GUIDE_developer.md`.

---

## Reference

### Naming Conventions

| Type | Rule | Do | Don't |
|------|------|----|-------|
| Functions | `camelCase` / `snake_case`, verb + noun | `preprocess_audio`, `calculate_eer` | `doStuff`, `thing` |
| Variables | intent first, avoid generic names | `waveform`, `sample_rate`, `labels` | `data`, `tmp` |
| Booleans | prefix `is_` / `has_` / `can_` / `should_` | `is_spoof`, `has_silence` | `flag`, `state` |
| Pytest functions | prefix `test_` + unit + scenario | `test_preprocess_crop_long_audio` | `test1`, `my_test` |
| Audio files | `SPK_XXXX_sampleYY.wav` | `SPK_0001_utt01.wav` | `John_Doe.wav` |
| Model checkpoints | `best_model.pt`, `checkpoint_epochN.pt` | `best_model.pt` | `model_final_v2_new.pt` |

### Commands

| Command | Purpose |
|---------|---------|
| `pytest tests/ -v` | Run full test suite |
| `python manage_kaggle.py push` | Push code to Kaggle GPU |
| `python manage_kaggle.py status` | Check Kaggle GPU kernel status |
| `python manage_kaggle.py output` | Download model checkpoints to `./out/` |
| `python scripts/eval_eer.py` | Run EER evaluation across test manifests |
| `python scripts/benchmark_latency.py` | Benchmark 30-run median inference latency |

### Version

| Item | Detail |
|------|--------|
| Current version | `0.1.0` |
| Source of truth | `src/__init__.py` |

---

*v0.1.0 — 2026-10-16*
