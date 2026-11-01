# Validation and test guide

## What was checked for this release

- `python -m pytest -q`: **27 passed** in the build environment. These cover calculations, input validation, comparisons, rules, export, project isolation, SQLite migration and database-path compatibility. Real generated PDF, DOCX, PPTX and XLSX fixtures are converted; text size, unsupported extensions and malformed Office inputs are checked.
- Reflex compiled and the local application started.
- The opt-in Playwright Chromium app smoke test passed: project creation; valid/invalid campaign import; dataset deletion; sample analytics, market filter, threshold findings and prior-year comparison; Excel download and workbook contents; TXT and generated PDF upload and source retrieval; campaign-name keyword search; HTML and URL QA; audience duplicate detection; and checklist/action persistence after reload. It uses synthetic data in a disposable database.
- The Playwright Chromium standalone showcase smoke test passed for filtering, sample findings, keyword search, browser-local checklist persistence, capability tabs and absence of external HTTP requests during that run.

These are smoke tests, **not exhaustive**. They do not establish accessibility compliance, security, production readiness, cross-browser support, deployment correctness, OCR quality or real-world performance. Scanned PDFs may contain no extractable text. DOCX/PPTX/XLSX conversions are unit-tested with synthetic fixtures but not uploaded through the browser smoke test. Python 3.13 was used in the validation environment; the declared supported install range is Python 3.10–3.12, and a clean `uv sync` on Windows has not been verified here.

## Continuous integration

The GitHub Actions workflow reproduces the unit-test run on Python 3.12 (`uv sync --extra dev`, `uv run pytest -q`). This exact sequence was reproduced locally on Python 3.12 before publishing: **27 passed**.

Pre-publish browser checks (Linux, Chromium headless, 2 vCPU): `scripts/showcase_browser_check.py` passed, and `scripts/e2e_browser.py` passed 3/3 runs against `uv run reflex run --env prod`. Against the dev server (`--env dev`) on the same small machine, the end-to-end script intermittently hit 30-second UI timeouts at different steps with no server-side errors; prefer `--env prod` when re-running it on constrained hardware.

## Re-run unit tests

```powershell
uv sync --extra dev
uv run pytest -q
```

## Re-run browser smoke tests

Install the dev dependencies above and then Chromium:

```powershell
uv run playwright install chromium
uv run python scripts/showcase_browser_check.py
```

For the application test, open **two PowerShell windows** in the project folder. Use a fresh disposable database: the script creates projects and other data. Do not point it at real data.

Window 1:

```powershell
$env:AEGIS_DB_PATH = "$PWD\workspace\e2e-disposable.sqlite3"
uv run reflex run
```

After the app is running, in window 2:

```powershell
$env:AEGIS_E2E_URL = "http://localhost:3000"
uv run python scripts/e2e_browser.py
```

Stop the app with Ctrl+C, then delete `workspace/e2e-disposable.sqlite3` if desired. Linux may require system browser libraries (`uv run playwright install-deps chromium`, typically with administrator privileges). The test assumes the chosen ports are free and downloads and local file uploads are permitted. It does not run by default in GitHub Actions.
