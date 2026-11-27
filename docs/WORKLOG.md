# ErrLab Worklog

## Current status
- **Current phase:** Phase 2 (Build the CLI)
- **Done:** Phase 0 (Foundations), Phase 1 (Flagsmith up and running: flag created with keyed variants, metric registered, draft experiment configured, server-side key minted to `.env`, Python SDK verified).
- **Blocked:** None. Ready to build CLI modules.

---

## Decisions log
| Date | Decision | Reason |
| --- | --- | --- |
| 2026-11-26 | Use local Docker or Cloud with managed warehouse | Cloud experimentation requires Scale-Up/Enterprise unless warehouse is provided; user confirmed free plan warehouse access, so test Cloud first with Docker as reliable fallback |
| 2026-11-26 | Flat recovery rates across variants (35% / 48% / 50%) | Keeps hypothesis test clean, statistically explainable, and avoids confounding error types |
| 2026-11-26 | Solo submission using OBS Studio for demo recording | Clarified team size and available tooling |
| 2026-11-27 | Standard `pyproject.toml` with `setuptools.build_meta` | Modern packaging for Python CLI with editable install support (`pip install -e .`) |
| 2026-11-27 | Install Flagsmith CLI v2 binary via official PowerShell script | `flagsmith-cli` is not a pip distribution; official v2 binary installed to `~/.local/bin/flagsmith.exe` |
| 2026-11-27 | Use verified SDK 6.7.0 signatures: `flush_events()`, `get_experiment_flag()`, `track_event(event=...)` | Live inspection of installed SDK confirmed method names (`event_processor` is private `_event_processor`; public flush is `flush_events()`) |

---

## Problems and fixes
| Date | Error / Problem | Root cause | Fix |
| --- | --- | --- | --- |
| 2026-11-27 | `The token '&&' is not a valid statement separator in this version.` | Executing commands in PowerShell where `&&` is unsupported in older PowerShell versions | Switched command chaining in terminal calls from `&&` to `;` |
| 2026-11-27 | `ERROR: Could not find a version that satisfies the requirement flagsmith-cli` | `flagsmith-cli` is not a Python package on PyPI (the Python package is `flagsmith` SDK) | Installed official Flagsmith CLI v2 using `irm https://raw.githubusercontent.com/Flagsmith/flagsmith-cli/main/install.ps1 \| iex` |
| 2026-11-27 | `ModuleNotFoundError: No module named 'dotenv'` | Python virtual/global environment lacked optional dependencies from `pyproject.toml` | Installed package in editable mode with extras: `pip install -e ".[dev]"` |
| 2026-11-27 | `Error: environment key "Development" not found in project 56669` | `flagsmith init -e` expects the client-side API key, not the display name | Passed environment key `MQSxjKYRor9tQ2DccDBjUA` |

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

### [Phase 1] Flagsmith CLI installation and login: 2026-11-27 11:34 IST
- **Goal:** Install Flagsmith CLI v2 and authenticate session against Flagsmith Cloud.
- **What I did:**
  - Checked existing Flagsmith Python SDK (confirmed v6.7.0 installed).
  - Attempted `pip install flagsmith-cli` (failed; package not on PyPI).
  - Installed official Flagsmith CLI v2 via PowerShell installer: `irm https://raw.githubusercontent.com/Flagsmith/flagsmith-cli/main/install.ps1 | iex`.
  - Verified installation at `C:\Users\Surya\.local\bin\flagsmith.exe` (v2.0.0).
  - Checked auth status (`flagsmith auth status` reported not logged in).
  - Initiated `flagsmith login --no-browser` to obtain OAuth authorization URL.
- **Result:** Flagsmith CLI v2.0.0 installed successfully. Background login process listening for OAuth callback.
- **Docs consulted:** Flagsmith CLI v2 installation docs (GitHub releases and install.ps1).
- **Decisions and why:** Use Flagsmith CLI v2 binary for managing flags, variants, and environments directly.
- **Verification:** `flagsmith --version` returned `flagsmith version v2.0.0`.
- **Open issues / next step:** Complete browser authentication, run `flagsmith init`, create multivariate flag `error_message_style` and metric `retry_succeeded`.

### [Phase 1] Flagsmith environment, flag, metric, and experiment configuration: 2026-11-27 11:44 IST
- **Goal:** Connect project `ErrLab`, create multivariate flag `error_message_style` with keyed variants, create metric `retry_succeeded`, configure draft experiment, mint server-side environment key, and verify Python SDK connectivity.
- **What I did:**
  - Authenticated via browser OAuth callback in CLI task (`✓ Logged in to https://api.flagsmith.com as t.sanjan018@gmail.com`).
  - Identified organisation `SuryaSanjan` (ID 42245), project `ErrLab` (ID 56669), and environment `Development` (Key `MQSxjKYRor9tQ2DccDBjUA`).
  - Bound repository using `flagsmith init -p ErrLab -e MQSxjKYRor9tQ2DccDBjUA` (generated `flagsmith.json`).
  - Created multivariate flag `error_message_style` (ID 306536) with default/control value `"terse"`.
  - Added keyed variants: `with_fix` (ID 37728, weight 33.33%) and `with_fix_and_link` (ID 37729, weight 33.33%).
  - Verified flag bucketing across multiple test identities via `flagsmith evaluate --identity ...`.
  - Minted server-side environment key `errlab-backend` and securely saved it to `.env` (`[REDACTED]`).
  - Created experiment metric `retry_succeeded` (ID 1025, aggregation: `occurrence`, direction: `up`, event: `retry_succeeded`).
  - Created draft experiment `CLI Error Message Style Experiment` (ID 970) linking feature 306536 and metric 1025.
  - Installed Python dependencies via `pip install -e ".[dev]"`.
  - Inspected exact Flagsmith Python SDK 6.7.0 signatures: `get_experiment_flag(self, feature_name: str, identifier: str)`, `track_event(self, event: str, identifier: str | None = None)`, and `flush_events(self) -> None`.
  - Verified remote SDK evaluation with server-side key via live Python test.
- **Result:**
  - Feature, variants, metric, and draft experiment are completely provisioned in Flagsmith Cloud.
  - SDK connects and resolves identities successfully against remote Flagsmith environment.
- **Docs consulted:** Flagsmith Experiments API specifications, Flagsmith CLI v2 reference, and installed SDK source/signatures.
- **Decisions and why:**
  - Control variant is represented by the feature's default value `"terse"`, with the two experimental treatments `with_fix` and `with_fix_and_link` given 33.33% each (control automatically receives the remaining 33.34%).
  - Minted server-side key for remote evaluation directly into `.env` to prevent printing secrets to output logs.
- **Verification:**
  - `flagsmith evaluate` confirmed all 3 variants (`control`/`terse`, `with_fix`, `with_fix_and_link`) resolve across identities.
  - Flagsmith API returned experiment ID 970 in status `"created"`.
  - Python test script successfully evaluated flags using the server-side environment key.
- **Open issues / next step:** Proceed to Phase 2 (Build the CLI package).

#### Phase 1 Summary
Phase 1 completed successfully. Project `ErrLab` was linked, and the multivariate feature `error_message_style` was created with `terse` (control), `with_fix`, and `with_fix_and_link`. Metric `retry_succeeded` and draft experiment `CLI Error Message Style Experiment` were registered. A server-side environment key was generated and stored in `.env`. Python SDK dependencies and method signatures (`flush_events`, `get_experiment_flag`, `track_event`) were verified against the live environment.


