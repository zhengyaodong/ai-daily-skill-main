# Repository Guidelines

## Project Structure & Module Organization
- `src/`: main Python application.
- `src/main.py`: orchestrates RSS fetch, AI analysis, HTML generation, optional image generation, and notifications.
- `src/config.py`: centralized environment-driven configuration.
- `src/docs/`: generated daily HTML pages and shared CSS (`css/styles.css`).
- `plugins/ai-daily/skills/ai-daily/`: skill package (`SKILL.md`, `scripts/fetch_news.py`, `references/`).
- `.github/workflows/`: CI/CD automation (`daily.yml` for scheduled generation, `release.yml` for tagged releases).

## Build, Test, and Development Commands
- `python -m venv .venv; .\.venv\Scripts\Activate.ps1`: create and activate virtual env (PowerShell).
- `pip install -r requirements.txt`: install runtime dependencies.
- `python src/main.py`: run the full daily generation pipeline locally.
- `python plugins/ai-daily/skills/ai-daily/scripts/fetch_news.py --date-range`: verify RSS source availability.
- `python src/test_email.py`: validate SMTP connectivity and mail sending behavior.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation; keep functions small and single-purpose.
- Use `snake_case` for modules/functions/variables and `UPPER_SNAKE_CASE` for config constants.
- Prefer type hints for new/changed functions and concise docstrings for non-obvious logic.
- Keep generated artifacts under `docs/`; do not hardcode secrets in source.

## Testing Guidelines
- Current repository uses script-based validation instead of a formal test framework.
- Add new tests as `test_*.py` files under `src/` when introducing behavior changes.
- Before opening a PR, run at least:
  - `python src/main.py`
  - `python src/test_email.py` (if notification code is touched)

## Commit & Pull Request Guidelines
- Git history currently contains very terse messages (for example, `commit`), so there is no strict enforced pattern yet.
- Use clear, imperative commit messages going forward (example: `feat: add fallback for empty RSS date`).
- PRs should include: purpose, key changes, test commands run, and sample output paths (for example `docs/2026-01-18.html`).
- Link related issues and include screenshots when HTML/CSS output changes.

## Security & Configuration Tips
- Copy `.env.example` to `.env` and set required keys (`K2_API_KEY` or compatible API settings, SMTP vars).
- Never commit real credentials; use GitHub Actions secrets for CI workflows.
