# Roadmap after v0.7

These are proposed, not implemented. Each requires implementation, testing and security review.

## v0.7 follow-ups
- Import preview, stronger schema and date semantics, more comprehensive boundary and dataset tests, richer configurable checks.
- Persist per-project filter settings; compare configurable peer periods; include comparisons and settings in exports; robust backups and a general migration framework.

## v0.8 — Document intelligence
- Test PDF/DOCX/PPTX/XLSX conversion end to end, preserve page/slide identifiers, handle OCR as an explicit opt-in.
- Chunking, metadata filters and optional local semantic search with transparent citations and delete/reindex support.

## v0.9 — Optional AI and integrations
- Configurable local or external LLM behind an opt-in consent gate; provenance, privacy controls, prompt-injection safeguards and grounded-answer evaluation.
- Campaign system adapters using least-privilege credentials, retry and audit controls; dry-run-only operations until approved.
- Better URL tracking policies, segmentation rule specifications, rendering checks and configurable checklists.

## v1.0 — Production readiness
- Authentication, per-user/project authorization, encryption, secrets management, retention/deletion, audit trails and threat modelling.
- Automated browser and integration tests, cross-platform packaging, monitoring, deployment/rollback plan, accessibility and performance testing.
- CI, pinned reproducible dependencies, licensing, responsible data handling and operational documentation.
