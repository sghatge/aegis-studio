# Publish Aegis on GitHub

These are the steps used to publish this repository and its GitHub Pages demo. Review the project before publishing your own copy.

## Create the repository

1. Sign in to GitHub, create a **public** repository named `aegis-studio`. Do not initialize it with a README, .gitignore or license if uploading using Git below.
2. Extract this project and open PowerShell inside `aegis-studio`. Run:

```powershell
git init
git add .
git status
git commit -m "Build Aegis Studio"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/aegis-studio.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Authenticate with GitHub as prompted. If Git asks for your name and email, configure them with `git config --global user.name` and `git config --global user.email` first. Use a GitHub no-reply address if you want to keep your email private.

The `.gitignore` excludes local databases, generated Reflex files, uploaded files, environment files and caches. Before pushing, inspect `git status` and the files to ensure no private data, API keys or sensitive material are included. The project is released under the MIT License (see `LICENSE`).

## Publish the interactive showcase with GitHub Pages

1. In your repository, open **Settings → Pages**.
2. Under **Build and deployment**, select **Deploy from a branch**, choose `main` and `/docs`, then save.
3. When GitHub finishes publishing, visit `https://YOUR_USERNAME.github.io/aegis-studio/` (or use the address shown in Settings → Pages).

The Pages site is only the interactive static showcase using synthetic data. It does **not** host the Python/Reflex application or persist campaign data. The complete app runs locally as described in README.md. GitHub Pages availability can depend on account/repository settings.

## LinkedIn

Open `LINKEDIN_POST.md`, replace the placeholder with your repository or verified Pages URL, review the wording, then copy it into LinkedIn. The draft does not claim that Aegis uses an LLM or is production-ready. LinkedIn posting has not been performed automatically.

## CI

`.github/workflows/tests.yml` runs the Python tests on GitHub Actions after push and pull requests. The workflow installs Python 3.12 and runs `uv sync --extra dev` then `uv run pytest -q`; `pyproject.toml` sets `pythonpath = ["."]` so the `aegis` package is importable without an editable install.
