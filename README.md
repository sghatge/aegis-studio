# Aegis Studio v0.7 — Personal Edition

**Campaign intelligence, under your control.**

[![Tests](https://github.com/sghatge/aegis-studio/actions/workflows/tests.yml/badge.svg)](https://github.com/sghatge/aegis-studio/actions/workflows/tests.yml)

**Live demo:** https://sghatge.github.io/aegis-studio/ (static, synthetic data, runs entirely in your browser)

A local-first, single-user portfolio prototype for campaign reporting and operations, with deterministic evidence retrieval and no external AI dependency. This release builds on the v0.6 reconstruction; sample data is synthetic. Start with [GETTING_STARTED.md](GETTING_STARTED.md) for the purpose, setup, usage and publishing steps. See `ROADMAP.md` for features that remain planned.

## Interactive showcase

Open [`docs/index.html`](docs/index.html) directly in a browser to explore synthetic campaigns with interactive filters, synthetic note search and a deployment checklist. It runs entirely in the browser, does not upload data and stores checklist ticks in browser local storage where available. The demo checklist is separate from the app database; sandboxed previews may block local storage. The hosted page has no service worker, so loading it while offline is not guaranteed. It is a static demonstration, separate from the Reflex application. See [PUBLISHING.md](PUBLISHING.md) for GitHub, GitHub Pages and LinkedIn instructions and [LINKEDIN_POST.md](LINKEDIN_POST.md) for the post draft.

## Quick start (Windows PowerShell)

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), e.g. `winget install --id astral-sh.uv -e`, then restart PowerShell. Extract the ZIP, `cd` into the extracted `aegis-studio` folder and run:

```powershell
uv sync --extra dev
uv run reflex run
```

Open http://localhost:3000. Initial startup may download frontend tooling and take a few minutes. Python 3.10–3.12 is required (3.13 is not yet supported); uv can provision it. Ports 3000 and 8000 are needed. Run tests with `uv run pytest -q`. Dependencies use version ranges, not a lockfile.

## Upgrading from Fable v0.6 or v0.7

1. Stop the old app. **Back up** `workspace/fable.sqlite3` and keep the copy outside the new project folder.
2. Extract this release to a new folder. Copy the old database to `workspace/fable.sqlite3` in the new folder. Aegis will use this legacy file automatically if `workspace/aegis.sqlite3` does not exist. You can instead set `AEGIS_DB_PATH` to a database copy. The legacy `FABLE_DB_PATH` environment variable is supported when the new variable is not set.
3. Start Aegis. A v0.6 database migrates legacy data into the **Default** project; a v0.7 database keeps its projects. Migration runs in a transaction, but restore the backup if anything goes wrong. No downgrade migration is supplied. If both default database files exist, Aegis selects `workspace/aegis.sqlite3`; set `AEGIS_DB_PATH` explicitly to choose another file.

## Workflow

1. Create a project or use **Default**. Project data includes datasets, documents, actions and the deployment checklist. Switch with **Open**. Deleting a project requires confirmation and permanently deletes all of its data; Default cannot be deleted. Projects are organizational partitions, not security boundaries.
2. Load the sample, or choose a CSV/XLSX file then click **Upload campaign**. Uploads are persisted; choose a dataset by ID in the list, or delete it. A new upload is selected automatically. Selection is session state; on reload the latest dataset is selected.
3. Use the market filter, then enter optional start/end dates, a bounce threshold and minimum delivered and click **Apply**. KPI cards show filtered rates with progress bars; bars are capped at 100% even when rates exceed that value. Use **Try sample 2025 vs 2024** for a quick date-range example. Filters affect the selected dataset, market/type/year summaries, findings, Ask Aegis campaign evidence and Excel export. Settings are session-only and persist when switching projects in that session. **Clear dates** removes the date range but retains threshold settings. Enter both dates to show the prior-year comparison.
4. Upload documents and retrieve matching passages with **Ask Aegis**. Add actions and use the checklist. Paste HTML or URLs for local QA, or upload an audience CSV for heuristics.
5. Export the six-sheet Excel report. It includes the filtered campaign dataset, summaries, KPIs and quality findings; the prior-year comparison, documents and actions are not included.

## Data contract and calculations

CSV UTF-8 or XLSX (first sheet), one campaign per row; headers case-insensitive and unique after normalization:

`campaign,date,market,type,sent,delivered,opens,clicks,conversions,bounces`

Use ISO dates such as `2025-01-15`; counts must be non-negative whole numbers. Duplicate campaign/date/market/type rows, unlikely count relationships, configurable bounce threshold exceedances and low delivered counts are flagged for review, not automatically rejected. Duplicate rows can be legitimate audience splits. Event counts may exceed unique counts. Null/missing dimensions, invalid dates and invalid counts are rejected.

- Open rate = opens / delivered; CTR = clicks / delivered; CTOR = clicks / opens.
- Conversion rate = conversions / delivered; bounce rate = bounces / sent.
- Rates use summed counts, not average campaign rates. Zero denominators are N/A.
- Year comparison uses **inclusive calendar dates** shifted one year earlier. Feb 29 endpoints clip to Feb 28 in a non-leap year; resulting periods may have different lengths. Rates are compared in percentage points, not percentage relative change. Missing data, changes in coverage and campaign mix can make comparisons misleading. A low delivered warning is not a significance test.
- Minimum-delivered and bounce thresholds are review heuristics; consent and causation are never inferred.

## Local persistence, privacy and safety

A new SQLite database lives at `workspace/aegis.sqlite3` relative to the launch directory. Set `AEGIS_DB_PATH` to choose a different path; `FABLE_DB_PATH` and the legacy `workspace/fable.sqlite3` are supported for upgrades as described above. Back up the file with the app stopped. Delete it with the app stopped to reset all data. It stores campaign file bytes and converted document text unencrypted. Audience CSVs are analysed in memory, not intentionally stored by application code. A 10 MB input check applies after upload is received, not at the network boundary. Exported spreadsheets escape formula-like text.

This is a local development app with **no authentication, authorization, encryption, audit logging, or isolation between users**. Use on a trusted machine with synthetic data; do not expose it publicly. Document parsers process untrusted files; only use trusted inputs. The app does not connect to campaign platforms, check real consent, visit URLs, send messages, or automate deployments. Human approval is essential.

## Documents and assistant

Text, Markdown, CSV and HTML are decoded as UTF-8. MarkItDown converts PDF, DOCX, PPTX and XLSX; scanned PDFs may need OCR. Converted text is capped at one million characters. Search matches query words in paragraphs and campaign names, and references document filename and paragraph number; it is not semantic search. **Ask Aegis is deterministic retrieval, not an LLM or autonomous AI agent.** It returns aggregate metrics, rule flags and matching source passages; it cannot determine causes or reliably answer general questions. No external AI API is called.

## Validation and limitations

Automated tests cover analytics, validation, date comparisons, zero denominators, QA rules, retrieval, export, project isolation, data migration, SQLite persistence and text conversion. Reflex compilation and local server startup were checked. A Chromium browser smoke test was run for the main app workflow; see `TESTING.md` for exact coverage and limitations. Cross-platform installation and production deployment have not been fully end-to-end tested.

## License

MIT. See [LICENSE](LICENSE).
