# ErrLab Worklog

## Current status
- **Current phase:** Phase 1 (Flagsmith up and running)
- **Done:** Phase 0 (Foundations: environment check, `.env.example`, `pyproject.toml`, repo structure, documentation committed and pushed).
- **Blocked:** None. Awaiting direction to begin Phase 1 setup.

---

## Decisions log
| Date | Decision | Reason |
| --- | --- | --- |
| 2026-11-26 | Use local Docker or Cloud with managed warehouse | Cloud experimentation requires Scale-Up/Enterprise unless warehouse is provided; user confirmed free plan warehouse access, so test Cloud first with Docker as reliable fallback |
| 2026-11-26 | Flat recovery rates across variants (35% / 48% / 50%) | Keeps hypothesis test clean, statistically explainable, and avoids confounding error types |
| 2026-11-26 | Solo submission using OBS Studio for demo recording | Clarified team size and available tooling |
| 2026-11-27 | Standard `pyproject.toml` with `setuptools.build_meta` | Modern packaging for Python CLI with editable install support (`pip install -e .`) |

---

## Problems and fixes
| Date | Error / Problem | Root cause | Fix |
| --- | --- | --- | --- |
| 2026-11-27 | `The token '&&' is not a valid statement separator in this version.` | Executing commands in PowerShell where `&&` is unsupported in older PowerShell versions | Switched command chaining in terminal calls from `&&` to `;` |

---

## Log Entries

### [Phase 0] Environment verification and foundations: 2026-11-27 11:26 IST
- **Goal:** Verify developer prerequisites (Python 3.10+, Git, Docker, Docker Compose), initialize configuration templates, setup project packaging, and commit foundations.
- **What I did:**
  - Checked versions: `python --version`, `git --version`, `docker --version`, `docker compose version`, `git status`.
  - Created `.env.example` with template variables for Flagsmith Cloud (`FLAGSMITH_ENVIRONMENT_KEY`, `FLAGSMITH_API_URL`) and commented Docker fallback.
  - Created `pyproject.toml` with dependencies (`flagsmith>=6.3.0`, `python-dotenv>=1.0.0`, `pyyaml>=6.0`, dev `pytest>=7.0`) and CLI entry point (`errlab = "errlab.cli:main"`).
  - Staged and committed files with message `Phase 0: foundations and project configuration`.
  - Pushed to `origin/main`.
- **Result:**
  - Tools verified: Python 3.14.6, Git 2.56.1, Docker 29.9.3, Docker Compose v5.7.1.
  - Attempted command `git add ... && git status` failed due to PowerShell statement separator syntax error.
  - Fixed command using `;` separator: `git add .env.example pyproject.toml docs/; git diff --staged --name-status`.
  - Commit `dca7664` pushed cleanly to GitHub repository.
- **Docs consulted:** Flagsmith documentation on experimentation and project prerequisites.
- **Decisions and why:**
  - Target Python 3.10+ in `pyproject.toml` to support standard modern packaging.
  - Keep `.env.example` clean of any real keys/tokens using placeholder text `your_server_side_environment_key_here`.
- **Verification:**
  - `git log -1 --stat` confirmed 4 files committed (`.env.example`, `docs/PLAN.md`, `docs/implementation-plan.md`, `pyproject.toml`).
  - `git push origin main` succeeded with exit code 0.
- **Open issues / next step:** Begin Phase 1 (verify Flagsmith Cloud credentials / project / environment or start local Docker instance).

#### Phase 0 Summary
Phase 0 completed successfully. Developer tooling (Python 3.14, Git, Docker, Docker Compose) was verified. The project configuration and packaging (`pyproject.toml`), environment templates (`.env.example`), and design plans were staged, committed, and pushed to remote `main`.
**Commit hash:** `dca76645d718419d6657b06dc0dfd2f1e0019092`
