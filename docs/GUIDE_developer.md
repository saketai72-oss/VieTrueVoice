# GUIDE_developer — Implementation rules for ViTrueVoice

---

## Rules

> Hard constraints. AI must follow unconditionally.

| Rule | Detail |
|------|--------|
| No unsolicited refactor | Never refactor working code unless explicitly asked |
| Git operations | Prefix all AI commit messages with `[AI]`. Do not push without user consent |
| TDD | Write or update tests before implementation for anything affecting audio processing, data loaders, models, loss, evaluation, or API endpoints |
| PII / Biometrics Ethics | Never log, store, or output real names, phone numbers, or raw voice data. Use SPK_XXXX and SHA-256 |
| RAM-Only Inference | Read audio stream directly from RAM in API/Bot; delete temporary files immediately |

---

## Refactoring Standards

| Rule | Detail |
|------|--------|
| No unsolicited refactor | Never refactor working code unless explicitly asked — even if it violates standards below |

### When to Extract a Function

| Trigger | Action |
|---------|--------|
| Logic or template appears **2+ times** | Extract immediately — no exceptions |
| Function body exceeds **20 lines** | Extract inner logic into named helpers |
| Inline expression requires a comment to understand | Extract into a named function instead |
| Repeated signal transformation | Extract into a separate preprocessing helper |

### When to Split a File

| Trigger | Action |
|---------|--------|
| File exceeds **200 lines** | Review — split if multiple responsibilities |
| File exceeds **400 lines** | Split mandatory — one responsibility per file |
| File contains 2+ unrelated concept groups | Split regardless of line count |
| A function is reused across 2+ files | Move to a shared helper file |

### Module Structure Rules

| Rule | Detail |
|------|--------|
| One responsibility per file | A file does one thing: processes audio signals, defines a neural architecture, runs training loop, or computes metrics |
| Orchestrators stay thin | Entry-point files (`train.py`, `manage_kaggle.py`, `src/app/server.py`) contain orchestration only, not core business algorithms |
| Helpers are stateless | Helper functions must be pure — no side effects, no global state mutations |
| Shared helpers live in one place | If 2+ files need the same helper, extract to a shared module — never duplicated |
| Import direction is one-way | Preprocessing never imports from models. Models never import from app |

### Zero-Loss Refactor Protocol

Use for any file split, large refactor, or move:

1. **Audit** first.
2. **Create targets** before removing old code.
3. **Bridge** with re-exports or adapters.
4. **Verify** with typecheck and `pytest tests/ -v`.
5. **Cut** only after behavior is verified stable.
6. **Verify again** after cleanup.

Do not skip the bridge phase for large moves.

### Anti-Patterns (Banned)

| Pattern | Why it fails | Fix |
|---------|-------------|-----|
| Zero padding audio clips | Discontinuous frequency spectrum breaks AASIST / SincConv | Use repeat padding (`np.tile`) to 64,000 samples |
| Equal loss weights for imbalanced classes | High false alarms on genuine speakers | Use `weight=torch.FloatTensor([0.1, 0.9])` |
| Writing uploaded voice files to disk permanently | Violates privacy laws (Law 91/2025/QH15 & Decree 356/2025/NĐ-CP) | Process via `io.BytesIO` in RAM; wipe temp files immediately |
| Logging raw filenames in benchmark logs | Exposes volunteer/speaker identity | Hash audio payload with SHA-256 |
| Logic duplicated across files | Conflicts when one is updated | Extract to shared helper |

---

## Architectural Defaults

### 3-Layer Separation
- **Data/Signal Layer**: `src/preprocessing/` (raw signal -> normalized 16kHz mono 64k tensor).
- **Model/Representation Layer**: `src/models/` & `src/training/` (SSL Wav2Vec2 + AASIST HS-GAL graph back-end).
- **Service/Presentation Layer**: `src/app/` (FastAPI / Gradio / Telegram bot orchestrators).

### State & Storage Registry
- **Kaggle Input State**: `/kaggle/input/<dataset-name>` (Read-only source).
- **Kaggle Working State**: `/kaggle/working/best_model.pt` (Checkpoint storage).
- **Local Artifacts**: `./out/` (Downloaded weights and logs).
- **Benchmarks**: `benchmarks/eval_metrics.csv` and `benchmarks/latency_log.json`.

### Namespace & Collision Governance
- **Audio manifests**: `data/manifests/{train,dev,test_indomain,test_unseen}.csv` with columns `audio_path,label,speaker_id`.
- **Labels**: `0` = Spoof (Giả), `1` = Bona fide (Thật).

---

## Edge Cases

- **Audio file with pure silence**: Handled by falling back to zero array of length 64,000 to prevent division by zero in std normalization.
- **Audio duration < 0.2s**: Repeat padded until >= 64,000 samples.
- **Audio duration > 10s**: Inference uses sliding window / center crop (4.0s) and averages confidence scores.

---

*v0.1.0 — 2026-10-16*
