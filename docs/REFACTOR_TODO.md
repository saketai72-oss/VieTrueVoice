# Refactor TODO — ViTrueVoice

> Working note for current refactoring tasks. Canonical rules: `docs/GUIDE_developer.md`.

---

## ✅ Completed (v0.1.0)
- [x] Initialized project structure and GitHub Actions CI.
- [x] Implemented 16kHz mono audio preprocessing, silence trimming, and repeat padding with TDD tests in `tests/test_preprocessing.py`.
- [x] Bootstrapped Living Docs architecture (`AGENTS.md`, `docs/ARCH_documentation-governance.md`, `docs/GUIDE_developer.md`, `docs/ARCH_technical-specs.md`, etc.).

---

## 🚀 Active Goals (v0.2.0 - Must #1)
Objective: Build data generation pipelines and speaker-disjoint splitting scripts.

- [ ] **1. Speaker-Disjoint Split Script (`scripts/split_dataset.py`)**
  - [ ] Write unit test in `tests/test_split.py` to ensure zero speaker overlap between Train, Dev, and Test sets.
  - [ ] Implement 70% Train, 15% Dev, 15% Test split saving to `data/manifests/`.
- [ ] **2. ASR Quality Filter Script (`scripts/filter_asr_wer.py`)**
  - [ ] Filter synthesized audio with PhoWhisper / Wav2Vec2 WER threshold.
- [ ] **3. Spoof Generation Helper (`scripts/generate_spoof.py`)**
  - [ ] Integrate F5-TTS and VieNeu-TTS synthesis commands.

---

## 🧊 Backlog (v0.3.0 - Must #2 & v0.4.0 - Must #3)
- [ ] Implement Baseline AASIST and SSL-AASIST modules in `src/models/`.
- [ ] Build 2-phase training loop in `src/training/` and Kaggle job entry point `train.py`.
- [ ] FastAPI `/api/v1/predict` endpoint and Gradio web interface.
- [ ] Latency benchmark script (30 runs median <= 3s).

---

## Safety & Verification
1. Zero-Loss Refactor Protocol: No behavioral changes allowed without explicit request.
2. Run `pytest tests/ -v` before every commit.
3. Every AI commit prefixed with `[AI]`.

---

*v0.1.0 — 2026-10-16*
