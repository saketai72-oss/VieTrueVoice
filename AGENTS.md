# Agent — ViTrueVoice (v0.1.0) — 2026-10-16

> **Strict Rule**: Read this file at every session start.

## Project Setup
- **Project Name**: ViTrueVoice (Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát)
- **Version**: 0.1.0 — semantic versioning
- **Status**: Active
- **Tech Stack**: Python 3.12, PyTorch 2.6 (CUDA), torchaudio, librosa, soundfile, Transformers, FastAPI, Gradio, Python-Telegram-Bot, pytest
- **Context Anchors**: [PLAN.md](PLAN.md), [README.md](README.md), [howtorun.md](howtorun.md)

## Documentation Priority
- `docs/` is the source of truth for behavior, architecture, and implementation rules.
- `AGENTS.md` holds only: session-critical rules, quick-reference checklists, metadata.
- Do not duplicate detailed explanations here — link to `docs/` instead.
- **Scope unclear?** Open `docs/ARCH_documentation-governance.md` first — task→load mapping is there.

## Documentation Governance
- **Implementation Standards**: `docs/GUIDE_developer.md` — how we write code, refactor, and test.
- **Architecture & System Specs**: `docs/ARCH_technical-specs.md` — system pipeline, Kaggle hybrid, biometrics privacy.
- **Preprocessing Logic**: `docs/LOGIC_preprocessing.md` — 16kHz mono, silence trimming, repeat padding, RawBoost, Codec.
- **Models & Training Logic**: `docs/LOGIC_models.md` — AASIST, SSL-AASIST, Weighted CE [0.1, 0.9], 2-phase training.
- **API & Benchmark Standards**: `docs/STANDARDS_api-benchmarks.md` — FastAPI endpoints, Gradio/Bot UI, SHA-256 logs.
- **Rule**: Never consolidate these files without explicit intent. Keep concerns isolated to prevent accidental regressions.

## Intentional Quirks (STUBBORN_FACTs)
> STUBBORN_FACT: Repeat padding is used instead of zero padding when length < 64,000 — to maintain spectral-temporal continuity for AASIST / Wav2Vec 2.0.
> STUBBORN_FACT: Weighted Cross-Entropy Loss uses weights [0.1, 0.9] (Spoof: 0.1, Bona fide: 0.9) — to counteract dataset imbalance (Spoof >= 2,000 vs Bona fide >= 1,000) and penalize false alarms on real users.
> STUBBORN_FACT: Audio logs in benchmarks/latency_log.json must use SHA-256 hashes instead of filenames or user IDs — to comply with biometrics privacy regulations (Law 91/2025/QH15 & Decree 356/2025/NĐ-CP).
> STUBBORN_FACT: Audio inputs in API/Bot are processed in-memory (RAM stream) and temporary files are destroyed immediately — to strictly prevent biological voice leakage.
> STUBBORN_FACT: Fixed input length is 64,000 samples (4.0s at 16kHz) — required by AASIST / Wav2Vec2 front-end.
> STUBBORN_FACT: All AI-generated Git commits MUST start with prefix `[AI]` — mandatory traceability rule.

## AI Technical Governance (CRITICAL)
- **Discussion Precedence (CRITICAL)**: Strictly forbidden to create, modify, or delete any code/files until the plan is fully discussed and finalized with the user.

## TDD Decision Rule
- **Use TDD** for: signal preprocessing, dataset splitting, loss calculation, evaluation metrics, model forward pass, API endpoints. Write pytest before code.
- **Skip TDD** for: docs, markdown notes, formatting, cosmetic edits.

## Goal-Driven Execution
Verify → trace → build → confirm. Never guess → build → fix → repeat.
Before multi-step tasks, state a brief plan: `[Step] → verify: [check]`.

## Response Style (CRITICAL)
- Answer only what's asked. No intro, recap, outro, filler, or padding.
- Markdown only when it helps (tables, code blocks).
- Unsure → ask **one** question. No assumptions.

### Writing Rules
Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries (sure/certainly/of course/happy to), hedging. Fragments OK. Short synonyms. Technical terms exact. Code blocks unchanged. Errors quoted exact.

Pattern: `[thing] [action] [reason]. [next step].`

### Auto-Clarity
Revert to full sentences for: security warnings, irreversible action confirmations, multi-step sequences where fragment order risks misread. Resume terse after.

## Common Mistakes
| Mistake | Prevention |
|---------|------------|
| Refactoring working code without being asked | Only refactor on explicit request |
| Committing AI code without `[AI]` prefix | Prefix all AI commit messages with `[AI]` |
| Storing raw voice files or PII in repo | Strict `.gitignore` on audio files + SHA-256 logging only |
| Zero padding short audio clips | Always use repeat padding (`np.tile`) to 64,000 samples |
| Equal weights in Cross-Entropy Loss | Always use `weights = [0.1, 0.9]` for `[Spoof, Bona fide]` |
| Duplicating a rule across multiple files | One file owns each rule — link, don't copy |
| Skipping the registry when adding a doc | Register in `docs/ARCH_documentation-governance.md` before use |

## Pre-Commit Protocol
1. **Test**: Run `pytest tests/ -v`. All tests must pass.
2. **Docs**: Update relevant `docs/LOGIC_*.md` or `docs/ARCH_*.md` if logic changed (via explicit doc sweep).
3. **Clean**: Remove debug print statements, delete scratch files.
4. **Git**: Prefix commit message with `[AI]`. Do not push without user consent.

## Milestones
- [x] v0.1.0: Project scaffolding, requirements, CI workflow green, audio processor with TDD tests.
- [ ] v0.2.0: Must #1 (W4) — Dataset preparation, ASR quality filter, Speaker-Disjoint split script.
- [ ] v0.3.0: Must #2 (W5) — Baseline AASIST and SSL-AASIST training pipeline on Kaggle GPU.
- [ ] v0.4.0: Must #3 (W6) — Real-time inference API (FastAPI), Gradio Web Demo, Telegram Bot (latency <= 3s).
- [ ] v1.0.0: Pilot & Nghiệm thu (W7-W8) — Docker packaging, CI/CD, security hardening, final benchmarks report.

## Commands
- `pytest tests/ -v`: run unit tests suite.
- `python manage_kaggle.py push`: push training code to Kaggle GPU.
- `python manage_kaggle.py status`: check Kaggle kernel execution status.
- `python manage_kaggle.py output`: download trained weights (`best_model.pt`) to `./out/`.
- `uvicorn src.app.server:app --reload`: launch FastAPI development server.

---

*v0.1.0 — 2026-10-16*
