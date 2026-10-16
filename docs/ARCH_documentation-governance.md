# ARCH_documentation-governance — Registry & Loading Guide

---

## Registry & Loading Guide

> **If a file is not here, register it before using it.**

| File | Contains | Must NOT contain | Load when |
|------|----------|-----------------|-----------|
| `AGENTS.md` | Session-critical rules, quick-reference, project metadata | Detailed implementation, full doc content | **Always** |
| `docs/GUIDE_developer.md` | Implementation standards, naming rules, patterns, versioning, pre-commit | Feature-specific logic, data structures | Technical work |
| `docs/ARCH_documentation-governance.md` | System's source of truth for doc management | Implementation content | Managing docs |
| `docs/ARCH_technical-specs.md` | Core architecture, audio pipelines, system boundaries, biometrics ethics | Formatting rules, UI tokens | Structural / data work |
| `docs/LOGIC_preprocessing.md` | Signal normalization (16kHz Mono), RMS silence trimming, 64k padding/crop, RawBoost, Codec simulation | Generic coding standards | Audio preprocessing tasks |
| `docs/LOGIC_models.md` | Baseline AASIST, SSL-AASIST (Wav2Vec2 + HS-GAL), Weighted CE loss [0.1, 0.9], 2-phase training | Preprocessing signal math | Model architecture & training |
| `docs/STANDARDS_api-benchmarks.md` | FastAPI schemas, Gradio UI, Telegram bot, SHA-256 latency logs, eval_metrics.csv | Model graph algorithms | API & benchmark work |
| `docs/REF_developer-reference.md` | Naming examples, lookup tables, commands, reference tables | Implementation content | Checking conventions / lookup |
| `docs/REF_template.md` | Blank template for creating new doc files | Rules, implementation content | Creating a new doc file |
| `docs/REFACTOR_TODO.md` | Current refactor work plan and targets | Canonical rules | Refactor planning |

### Task → Load mapping

| Task | Load |
|------|------|
| General development | `AGENTS.md` |
| Feature / Logic changes (Audio Preprocessing) | `AGENTS.md` + `docs/GUIDE_developer.md` + `docs/LOGIC_preprocessing.md` |
| Feature / Logic changes (Models & Training) | `AGENTS.md` + `docs/GUIDE_developer.md` + `docs/LOGIC_models.md` |
| Architecture / Data changes | `AGENTS.md` + `docs/ARCH_technical-specs.md` |
| Interface / Output / API changes | `AGENTS.md` + `docs/STANDARDS_api-benchmarks.md` |
| Reference lookup | `docs/REF_developer-reference.md` |
| Refactor planning | `docs/REFACTOR_TODO.md` |
| Documentation management | `docs/ARCH_documentation-governance.md` |

---

## Canonical Ownership

Use one file as the source of truth for each rule group.

| Area | Canonical file |
|------|----------------|
| Session-critical rules & metadata | `AGENTS.md` |
| Implementation standards & TDD | `docs/GUIDE_developer.md` |
| Docs registry / load mapping | `docs/ARCH_documentation-governance.md` |
| System architecture, biometrics ethics, Kaggle hybrid | `docs/ARCH_technical-specs.md` |
| Signal preprocessing, silence trimming, RawBoost, Codec | `docs/LOGIC_preprocessing.md` |
| Model architectures (AASIST, SSL-AASIST), loss, training | `docs/LOGIC_models.md` |
| API specs, Gradio/Bot UI, evaluation metrics, latency logs | `docs/STANDARDS_api-benchmarks.md` |

---

## Docs Naming Convention

| Prefix | Scope |
|--------|-------|
| `GUIDE_` | Implementation rules and standards |
| `ARCH_` | System architecture, data flow, structure |
| `LOGIC_` | Feature behavior, algorithms, business rules |
| `STANDARDS_` | Interface specs, output formats, visuals |
| `REF_` | Reference tables, constants, lookup data |
| `INCIDENT_` | Incident post-mortems, regression logs |

**Fixed names (no prefix, must not rename):** `AGENTS.md`

**Fallback rule:** If a file is not in the registry → read prefix → load only if task matches → flag to user that registry needs updating.

---

## Maintenance Rules

**One rule above all: content exists in ONE file only. No duplication.**
**Compact, not incomplete: remove empty sections, never remove rules, edge cases, or reference rows.**

### Adding a new doc
1. Pick prefix from naming convention table.
2. Register in the Registry table above (mandatory).

### Moving content
1. Copy to destination → verify complete → delete from source → update any references.

### Editing existing files
- `AGENTS.md`: session-critical rules and metadata only.
- `GUIDE_*`: coding standards + basic UI. No deep visual rules.
- `STANDARDS_*`: visual/interaction/API only. No coding standards.
- Registry table: update immediately when any file is added, renamed, or removed.

---

*v0.1.0 — 2026-10-16*
