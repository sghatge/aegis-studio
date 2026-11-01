# Aegis Studio — purpose, setup, usage and publishing

## 1. Purpose

Aegis Studio is a **local-first personal CRM campaign workspace**. It helps you inspect synthetic or trusted campaign reports, compare performance, review basic deployment risks, organise actions and retrieve document passages. It is a portfolio prototype: it is not an autonomous AI agent or a production-secure SaaS product. Ask Aegis uses deterministic keyword matching and does not call an external AI model.

There are two experiences:

- **Interactive demo**: open `docs/index.html` in a browser. It uses six built-in synthetic campaigns, has market/year/type filters, a sample note search and a small checklist saved in browser local storage when available. No upload or server is needed. Browser sandbox restrictions can prevent checklist persistence. The hosted demo has no service worker, so loading it while offline is not guaranteed.
- **Full app**: runs locally using Python and Reflex. It supports projects, uploaded campaign reports and documents, SQLite persistence, QA, checklists, actions and Excel exports. Its checklist is stored in the local SQLite workspace—not the demo’s browser storage.

## 2. Set up the full app (Windows)

1. Extract the ZIP and open PowerShell inside the `aegis-studio` folder.
2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), for example `winget install --id astral-sh.uv -e`. Restart PowerShell if needed.
3. Run:

```powershell
uv sync --extra dev
uv run reflex run
```

4. Open `http://localhost:3000`. Initial startup may download Python and frontend dependencies. Ports 3000 and 8000 need to be available. Python 3.10–3.12 is specified.

Stop the app with Ctrl+C. The default database is `workspace/aegis.sqlite3`; see `README.md` for backup and migration from Fable.

## 3. Use the full app

1. **Project:** use Default or create a new project. Switch with its Open button.
2. **Data:** click **Load sample** or select a CSV/XLSX and click **Upload campaign**. The latest upload is selected; you can switch or delete datasets. Required columns are `campaign,date,market,type,sent,delivered,opens,clicks,conversions,bounces`. See `data/sample_campaigns.csv` and `README.md` for definitions.
3. **Explore:** choose a market, set dates and quality thresholds and click Apply. The sample’s South and Coast 2025 campaigns exceed the 5% bounce review threshold. Click **Try sample 2025 vs 2024** to see an aligned calendar comparison. All numbers are synthetic; no cause or statistical significance is inferred.
4. **Evidence:** choose a trusted document and click **Add document**. Ask Aegis searches campaign names and extracted document passages by keywords. It is not semantic search or an LLM. Scanned PDF files may not contain searchable text.
5. **Quality and operations:** paste HTML or URLs to check basic structural and tracking risks. Upload an anonymised audience CSV for simple checks. Mark checklist items and assign actions; these are saved in SQLite.
6. **Export:** click **Export Excel** for the currently selected dataset, dates and market. The year-on-year comparison itself is displayed in the app but is not in the workbook.

Do not use sensitive data or expose the app to the internet. It has no authentication, access control, encryption or audit logging. Checks do not verify live links, consent or deployment readiness; human review is necessary.

## 4. Publish on GitHub

GitHub was not connected, so **nothing has been published for you**. Install Git and sign in to GitHub, then:

1. Create an empty public repository named `aegis-studio` (do not add a README or license during creation).
2. In PowerShell inside the extracted project folder, replace `YOUR_USERNAME` below and run:

```powershell
git init
git add .
git status
git commit -m "Build Aegis Studio"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/aegis-studio.git
git push -u origin main
```

Check `git status` for sensitive files before committing. Authenticate when prompted. Decide on a license before inviting reuse. If the repository name already exists, choose a different name and update the URLs.

3. To publish the **static demo**, open repository **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/docs`, and save. Wait for GitHub to show the published URL. GitHub Pages does not run the full Python app.
4. Edit `LINKEDIN_POST.md`, replace its link placeholder with your verified repository or demo URL, and post it yourself.

See `PUBLISHING.md` for more details and `TESTING.md` for the exact tests and known limitations.
