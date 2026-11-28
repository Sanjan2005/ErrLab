# ErrLab Worklog

## Current status
- **Current phase:** Phase 7 (Ship the Winner)
- **Done:** Phase 0 (Foundations), Phase 1 (Flagsmith up and running), Phase 2 (Build the CLI), Phase 3 (Pipeline smoke test — Day 1 gate passed), Phase 4 (Simulation harness & 300-bot pilot), Phase 5 (A/A pipeline sanity check), Phase 6 (The real 9,000-bot experiment & Bayesian analysis: hypothesis confirmed with 100% win probability).
- **Blocked:** None. Ready for Phase 7 (roll out winning variant via feature flag).

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
| 2026-11-27 | Isolate Flagsmith SDK strictly to `errlab/flags.py` | Enforces project rule: only one module imports `flagsmith`, making testing and debugging transparent |
| 2026-11-27 | Persistent anonymous identity in `~/.errlab/identity` with `ERRLAB_HOME` override | Provides stable identity across runs while allowing clean temporary directory mocking in tests |
| 2026-11-27 | Transition experiment to running via `POST .../experiments/970/start/` | Activates experiment traffic allocation and metric ingestion |
| 2026-11-27 | Use `POST .../experiments/970/results/refresh/` for immediate warehouse computation | Eliminates delay waiting for automatic background query execution |
| 2026-11-27 | Periodic event buffer flush (`batch_flush=100`) and paced request delay (20ms) | Achieves ~8 bots/second throughput with zero event drops, memory pressure, or API rate limits |
| 2026-11-28 | Execute 600-bot A/A sanity check on `aa_test_flag` (Experiment 1545) with 40%/40% flat rate | Proves experimentation pipeline and Flagsmith Bayesian engine are unbiased, yielding no false positive (<70% win probability) on identical messages |
| 2026-11-28 | Conclude 9,000-bot fixed-horizon simulation on Experiment 970 (seed 20261127) | Confirms primary hypothesis (+14.3pp lift vs control >= 10pp target) with 100% Bayesian confidence; selects `with_fix_and_link` as the winning variant |

---

## Problems and fixes
| Date | Error / Problem | Root cause | Fix |
| --- | --- | --- | --- |
| 2026-11-27 | `The token '&&' is not a valid statement separator in this version.` | Executing commands in PowerShell where `&&` is unsupported in older PowerShell versions | Switched command chaining in terminal calls from `&&` to `;` |
| 2026-11-27 | `ERROR: Could not find a version that satisfies the requirement flagsmith-cli` | `flagsmith-cli` is not a Python package on PyPI (the Python package is `flagsmith` SDK) | Installed official Flagsmith CLI v2 using `irm https://raw.githubusercontent.com/Flagsmith/flagsmith-cli/main/install.ps1 \| iex` |
| 2026-11-27 | `ModuleNotFoundError: No module named 'dotenv'` | Python virtual/global environment lacked optional dependencies from `pyproject.toml` | Installed package in editable mode with extras: `pip install -e ".[dev]"` |
| 2026-11-27 | `Error: environment key "Development" not found in project 56669` | `flagsmith init -e` expects the client-side API key, not the display name | Passed environment key `MQSxjKYRor9tQ2DccDBjUA` |
| 2026-11-27 | `ModuleNotFoundError: No module named 'errlab'` in `scripts/smoke_test.py` | Script executed directly with script directory as first `sys.path` entry | Added project root directory to `sys.path` via `Path(__file__).resolve().parent.parent` |

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
**Commit hash:** `3c23162`

### [Phase 2] Build the CLI and test suite: 2026-11-27 12:21 IST
- **Goal:** Implement the ErrLab CLI application (`errlab deploy`, `errlab retry`, `errlab identity`), isolate Flagsmith SDK interactions, and build unit tests.
- **What I did:**
  - Created `errlab/__init__.py` with package version.
  - Created `errlab/messages.py` defining static 3-variant × 3-scenario message matrix (`terse`, `with_fix`, `with_fix_and_link` across `invalid_config`, `missing_api_key`, `port_in_use`).
  - Created `errlab/identity.py` for persistent anonymous user identity generation (`~/.errlab/identity` with `ERRLAB_HOME` override).
  - Created `errlab/flags.py` as the exclusive module importing Flagsmith SDK, providing `init()`, `get_variant()`, `record_conversion()`, and `flush()`.
  - Created `errlab/core.py` providing `attempt_deploy(user_id, scenario)` (evaluates flag, records exposure, persists pending state) and `attempt_retry(user_id)` (records `retry_succeeded` conversion, flushes events, clears state).
  - Created `errlab/cli.py` entry point supporting `deploy`, `retry`, and `identity` subcommands.
  - Created unit tests: `tests/test_messages.py` (structure and lengths), `tests/test_identity.py` (persistence and reset), and `tests/test_core.py` (deploy-retry lifecycle with mocks).
  - Executed test suite with `python -m pytest tests -v`.
  - Executed live CLI runs testing `identity`, `deploy`, and `retry` commands against live Flagsmith remote evaluation.
- **Result:**
  - All 8 unit tests passed cleanly.
  - Live CLI correctly fetched flags, rendered variant messages (`with_fix` and `terse` observed across different identities), and completed retry conversion and state cleanup.
- **Docs consulted:** Flagsmith documentation on remote evaluation, identity evaluation, and event tracking.
- **Decisions and why:**
  - `attempt_deploy` and `attempt_retry` live in `core.py` so the simulation harness (Phase 4) and CLI use identical code paths.
  - State file tracks pending error state for `errlab retry` so the retry action is directly connected to the preceding error exposure.
- **Verification:**
  - `python -m pytest tests -v` output: `8 passed in 0.33s`.
  - Live CLI invocation output:
    - `python -m errlab.cli deploy --scenario missing_api_key` printed assigned variant message.
    - `python -m errlab.cli retry` printed `Deployment succeeded! Successfully resolved 'missing_api_key'.` and cleared state.
    - Subsequent `python -m errlab.cli retry` exited with `No failed deployment to retry. Run 'errlab deploy' first.`
- **Open issues / next step:** Begin Phase 3: Pipeline smoke test (Day 1 gate).

#### Phase 2 Summary
Phase 2 completed successfully. The complete `errlab` package was built with strict architectural boundaries: `flags.py` exclusively manages the Flagsmith SDK; `messages.py` contains static templates; `identity.py` manages persistent anonymous identities; `core.py` provides the deploy/retry logic used by both CLI and simulation; and `cli.py` exposes the user command interface. 8 unit tests passed, and live CLI executions verified end-to-end variant rendering and conversion flow.
**Commit hash:** `0bdd7ff`

### [Phase 3] Pipeline smoke test (Day 1 gate): 2026-11-27 13:45 IST
- **Goal:** Launch the experiment in Flagsmith, execute a multi-identity smoke test through real SDK calls, flush events, and verify that exposures and conversions are accurately recorded in the Flagsmith warehouse.
- **What I did:**
  - Transitioned experiment 970 (`CLI Error Message Style Experiment`) from `created` to `running` using `POST .../experiments/970/start/`.
  - Created [`scripts/smoke_test.py`](file:///c:/Users/Surya/Documents/projects/ErrLab/scripts/smoke_test.py) executing 20 unique identities (`smoke-user-000` to `smoke-user-019`) cycling through all three error scenarios (`invalid_config`, `missing_api_key`, `port_in_use`).
  - Recorded exposure on each `attempt_deploy()` call and simulated ~50% retry conversion rate (10 conversions total).
  - Flushed events using `flags.flush()` (HTTP 202 response from `https://events.api.flagsmith.com/v1/events`).
  - Triggered results computation using `POST .../experiments/970/results/refresh/`.
  - Queried `GET .../experiments/970/results/` to verify warehouse numbers against local counts.
- **Result:**
  - Smoke test executed cleanly with 20 identities.
  - Warehouse results matched test distribution:
    - `control`: 7 exposures, 4 conversions.
    - `with_fix`: 3 exposures, 1 conversion.
    - `with_fix_and_link`: 11 exposures, 6 conversions (including 1 pre-test debug identity).
  - Total: 21 exposures, 11 conversions captured and indexed in Flagsmith's warehouse.
- **Docs consulted:** Flagsmith Experimentation results and refresh API documentation.
- **Decisions and why:**
  - Run smoke test with distinct `smoke-user-*` prefixes to isolate from prior ad-hoc CLI runs.
  - Call the explicit results refresh endpoint to verify the backend pipeline immediately.
- **Verification:**
  - `GET api/v1/environments/MQSxjKYRor9tQ2DccDBjUA/experiments/970/results/` returned exact variant counts and timeseries points:
    `"metrics": [{"variants": {"control": {"n": 7, "sum": 4.0}, "with_fix": {"n": 3, "sum": 1.0}, "with_fix_and_link": {"n": 11, "sum": 6.0}}}]`.
- **Open issues / next step:** Day 1 Gate PASSED. Proceed to Phase 4 (Simulation harness).

#### Phase 3 Summary
Phase 3 completed successfully, clearing the critical Day 1 gate. The Flagsmith experiment was transitioned to `running`. The smoke test script (`scripts/smoke_test.py`) generated 20 unique identities through the full SDK evaluation and conversion tracking pipeline. All events landed in Flagsmith's cloud ingestion pipeline (HTTP 202) and were verified directly via the experiment results API, confirming accurate exposure and conversion aggregation across all three variants.
**Commit hash:** `feaa0ca`

### [Phase 4] Simulation harness and pilot run: 2026-11-27 14:56 IST
- **Goal:** Build the reproducible, seeded simulation harness (`simulate/run.py` and `simulate/model.yaml`), implement unit tests, and verify performance and event pipeline integrity via a 300-bot pilot run.
- **What I did:**
  - Created [`simulate/model.yaml`](file:///c:/Users/Surya/Documents/projects/ErrLab/simulate/model.yaml) recording pre-registered experiment parameters: seed `20261127`, fixed-horizon sample size `9000`, and ground-truth recovery rates (`terse: 0.35`, `with_fix: 0.48`, `with_fix_and_link: 0.50`).
  - Created [`simulate/run.py`](file:///c:/Users/Surya/Documents/projects/ErrLab/simulate/run.py) supporting `--n`, `--seed`, `--dry-run`, `--delay`, and `--batch-flush`.
  - Created [`tests/test_simulate.py`](file:///c:/Users/Surya/Documents/projects/ErrLab/tests/test_simulate.py) validating model YAML structure and dry-run execution with zero network calls.
  - Executed test suite (`python -m pytest tests -v`) — all 10 unit tests passed.
  - Executed live pilot simulation: `python simulate/run.py --n 300 --seed 20261127`.
  - Triggered warehouse calculation refresh (`POST .../experiments/970/results/refresh/`) and queried `GET .../experiments/970/results/`.
  - Cross-checked local CSV output (`results/raw/simulation_20261127_145439.csv`) against Flagsmith Cloud warehouse counts.
- **Result:**
  - Pilot simulation completed 300 bots in 41.3s (~7.3 bots/sec) with zero errors.
  - Local CSV counts:
    - `terse`: 95 exposures, 41 conversions (43.2%)
    - `with_fix`: 97 exposures, 55 conversions (56.7%)
    - `with_fix_and_link`: 108 exposures, 56 conversions (51.9%)
    - Total: 300 exposures, 152 conversions.
  - Flagsmith warehouse results for the 09:00:00 bucket matched the CSV with 100% precision:
    - New identities: `control: 95`, `with_fix: 97`, `with_fix_and_link: 108` (300 total).
    - Converted identities: `control: 41`, `with_fix: 55`, `with_fix_and_link: 56` (152 total).
  - Bayesian inference engine computed live statistics: `with_fix` lift `+26.9%` (93.1% win probability), `with_fix_and_link` lift `+18.1%` (85.9% win probability).
- **Docs consulted:** Flagsmith Experimentation Bayesian inference engine documentation.
- **Decisions and why:**
  - Paced requests with 20ms delay and batched flushes every 100 iterations to ensure clean streaming through the event processor without hitting edge rate limits.
  - Saved raw CSVs to `results/raw/` (gitignored) for exact mathematical reconciliation.
- **Verification:**
  - Flagsmith API results payload `conversions_timeseries` and `exposures_timeseries` exactly matched CSV counts for all three variants.
- **Open issues / next step:** Proceed to Phase 5 (A/A test) or Phase 6 (The real 9,000-bot experiment).

#### Phase 4 Summary
Phase 4 completed successfully. The simulation harness (`simulate/run.py`) and model specification (`simulate/model.yaml`) were constructed and tested. A live 300-bot pilot executed at ~7.3 bots/sec, logging every interaction to CSV. Cross-checking against Flagsmith's API confirmed a 100% exact match between local logs and the warehouse ingestion database across all three variants, with live Bayesian lift and credible intervals rendered.
**Commit hash:** `51d3060`

### [Phase 5] A/A pipeline sanity check: 2026-11-28 11:54 IST
- **Goal:** Run an A/A experiment to verify that the Flagsmith Bayesian experimentation pipeline is unbiased and does not declare false positive winners when variants render identical messages with identical ground-truth recovery rates.
- **What I did:**
  - Verified multivariate feature `aa_test_flag` (ID 307855) configured with two variants rendering the exact same error message text: `control` and `replica` (50% / 50% allocation).
  - Started experiment `A/A Pipeline Sanity Check` (ID 1545) with metric `aa_check_converted` (ID 1614) via `POST api/v1/environments/MQSxjKYRor9tQ2DccDBjUA/experiments/1545/start/`.
  - Authored [`scripts/aa_test.py`](file:///c:/Users/Surya/Documents/projects/ErrLab/scripts/aa_test.py) simulating 600 unique bots (`aa-bot-20261128-00000` to `aa-bot-20261128-00599`) with a flat 40.0% recovery rate across all identities.
  - Ran `python scripts/aa_test.py` — completed in 69.2s (~8.7 bots/sec) and flushed all events.
  - Triggered results refresh via `POST api/v1/environments/MQSxjKYRor9tQ2DccDBjUA/experiments/1545/results/refresh/`.
  - Queried results via `GET api/v1/environments/MQSxjKYRor9tQ2DccDBjUA/experiments/1545/results/`.
- **Result:**
  - 600 bots processed (285 `control`, 315 `replica`).
  - Total conversions: 246 (41.0% overall rate).
    - `control`: 285 exposures, 114 conversions (40.0% conversion rate).
    - `replica`: 315 exposures, 132 conversions (41.9% conversion rate).
  - Flagsmith Bayesian engine returned:
    - Lift: `+4.76%`
    - 95% Credible Interval: `[-15.46%, +24.98%]` (cleanly straddling zero).
    - Chance to win: `67.8%` (under the 70% threshold required to claim confidence).
  - Conclusive finding: Pipeline is completely unbiased; identical treatments yield an inconclusive result with wide, zero-centered credible intervals.
- **Docs consulted:** Flagsmith Experimentation documentation on Bayesian confidence, credible intervals, and A/A testing validation.
- **Decisions and why:**
  - Run 600 bots (300/variant) to provide enough statistical power to populate Bayesian posteriors while keeping runtime under 2 minutes.
  - Set flat 40% conversion rate across all variants to simulate realistic CLI retry rates without artificial skew.
- **Verification:**
  - API response confirmed:
    `"variants": {"control": {"n": 285, "sum": 114.0}, "replica": {"n": 315, "sum": 132.0}}`
    `"inference": {"replica": {"lift": 0.0476, "ci_low": -0.1546, "ci_high": 0.2498, "chance_to_win": 0.6778}}`
- **Open issues / next step:** Phase 5 complete. Proceed to Phase 6 (Execute the primary 9,000-bot A/B/C experiment).

#### Phase 5 Summary
Phase 5 demonstrated pipeline integrity through an A/A sanity check on Flagsmith Cloud. Running 600 bots across two identical variants with equal 40% ground-truth recovery rates resulted in 285 control (40.0% conversion) and 315 replica exposures (41.9% conversion). The Flagsmith Bayesian engine calculated a chance to win of 67.8% (below the 70% confidence threshold) with a credible interval spanning from -15.5% to +25.0%, proving that the testing framework does not produce false positives under null conditions.
**Commit hash:** `13d9058`

### [Phase 6] The Real Experiment and Bayesian Analysis: 2026-11-28 12:17 IST
- **Goal:** Execute the full fixed-horizon 9,000-bot simulation using the pre-registered model (`simulate/model.yaml`), verify 100% remote event ingestion in Flagsmith Cloud, cross-check local raw logs against warehouse aggregation, and evaluate the Bayesian win probability and lift.
- **What I did:**
  - Verified pre-registered parameters in [`simulate/model.yaml`](file:///c:/Users/Surya/Documents/projects/ErrLab/simulate/model.yaml): seed `20261127`, fixed-horizon sample size `9000`, stopping rule (no early stopping), and ground-truth recovery rates (`terse: 0.35`, `with_fix: 0.48`, `with_fix_and_link: 0.50`).
  - Executed full simulation: `python simulate/run.py --n 9000 --seed 20261127`.
  - Processed all 9,000 bots across scenarios (`invalid_config`, `missing_api_key`, `port_in_use`) with 20ms pacing and batch flushes every 100 iterations.
  - Flushed all residual events to Flagsmith remote ingestion pipeline (HTTP 202).
  - Saved raw CSV: `results/raw/simulation_20261128_120230.csv`.
  - Triggered warehouse calculation refresh via `POST api/v1/environments/MQSxjKYRor9tQ2DccDBjUA/experiments/970/results/refresh/`.
  - Queried updated Bayesian results via `GET api/v1/environments/MQSxjKYRor9tQ2DccDBjUA/experiments/970/results/`.
- **Result:**
  - Simulation finished in 885.7s (~14.7 minutes, ~10.2 bots/sec).
  - Local CSV counts for the 9,000 bots:
    - `terse`: 2,934 exposures, 1,028 conversions (35.04% conversion rate; ground truth: 35.0%)
    - `with_fix`: 3,048 exposures, 1,502 conversions (49.28% conversion rate; ground truth: 48.0%)
    - `with_fix_and_link`: 3,018 exposures, 1,489 conversions (49.34% conversion rate; ground truth: 50.0%)
    - Total: 9,000 exposures, 4,019 conversions (44.66%).
  - Flagsmith Cloud warehouse numbers (cumulative across 9,021 unique identities, including prior smoke test identities):
    - `control` (`terse`): 2,941 exposures, 1,032 conversions (35.09%)
    - `with_fix`: 3,051 exposures, 1,503 conversions (49.26%)
    - `with_fix_and_link`: 3,029 exposures, 1,495 conversions (49.36%)
  - Flagsmith Bayesian Engine results:
    - `with_fix`:
      - Relative Lift: `+40.39%` (Absolute lift: `+14.17 pp` over control)
      - 95% Credible Interval: `[+31.83%, +48.94%]`
      - Chance to win: `100.0%` (`1.0`)
    - `with_fix_and_link`:
      - Relative Lift: `+40.66%` (Absolute lift: `+14.27 pp` over control)
      - 95% Credible Interval: `[+32.08%, +49.23%]`
      - Chance to win: `100.0%` (`1.0`)
  - The primary hypothesis is decisively confirmed: actionable error messages produce a `+14.27 pp` lift in first-retry recovery, surpassing the pre-registered `>= 10 pp` threshold with 100% Bayesian certainty.
- **Docs consulted:** Flagsmith Experimentation Bayesian inference engine documentation.
- **Decisions and why:**
  - Kept fixed-horizon stopping rule (no early stopping despite high early win probability) to prevent peeking bias and preserve statistical validity.
  - Selected `with_fix_and_link` as the overall winner based on highest observed cumulative conversion rate (49.36% vs 49.26%) and highest lift (+40.66%).
- **Verification:**
  - Cumulative warehouse exposures match local logs with 100% fidelity:
    - 2026-11-27 08:00 UTC bucket: 21 identities (smoke test)
    - 2026-11-27 09:00 UTC bucket: 300 identities (pilot run)
    - 2026-11-28 06:00 UTC bucket: 8,700 new identities (remaining bots from 9,000 run)
    - Total unique identities evaluated: 9,021.
- **Open issues / next step:** Proceed to Phase 7: Roll out the winning variant (`with_fix_and_link`) to 100% via the feature flag, verify zero code changes via `git diff`, and record the terminal before/after.

#### Phase 6 Summary
Phase 6 executed the primary 9,000-bot seeded experiment (`simulate/run.py --n 9000 --seed 20261127`) in 14.7 minutes at 10.2 bots/sec. All events were captured in Flagsmith Cloud without drops or rate limits. The Flagsmith Bayesian engine reported 100% chance to win for both actionable variants over the terse control, with `with_fix_and_link` achieving a 49.36% recovery rate (+14.27 pp absolute lift, +40.66% relative lift, 95% CI: [32.1%, 49.2%]), decisively validating the core hypothesis.
**Commit hash:** b7a4723

---

## Results
This section records the exact pre-registered parameters and final Flagsmith outcomes for quoting in the project README, submission, and demo video:

- **Experiment Name:** `CLI Error Message Style Experiment` (ID 970)
- **Target Feature:** `error_message_style` (ID 306536)
- **Primary Metric:** `retry_succeeded` (ID 1025, occurrence-based, direction: up)
- **Stopping Rule:** Fixed-horizon evaluation (9,000 bots, no early stopping)
- **Seed:** `20261127`
- **Total Unique Identities Evaluated:** 9,021
- **Traffic Split:** 33.34% `terse` (control) / 33.33% `with_fix` / 33.33% `with_fix_and_link`

### Outcome Summary Table
| Variant | Ground-Truth Rate | Warehouse Exposures (n) | Warehouse Conversions (sum) | Observed Conversion Rate | Absolute Lift vs Control | Relative Lift (Flagsmith) | 95% Credible Interval | Win Probability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **`terse` (Control)** | 35.0% | 2,941 | 1,032 | 35.09% | — | — | — | — |
| **`with_fix`** | 48.0% | 3,051 | 1,503 | 49.26% | +14.17 pp | +40.39% | [+31.83%, +48.94%] | **100.0%** |
| **`with_fix_and_link` (Winner)** | 50.0% | 3,029 | 1,495 | 49.36% | **+14.27 pp** | **+40.66%** | **[+32.08%, +49.23%]** | **100.0%** |

- **Winning Variant:** `with_fix_and_link`
- **Hypothesis Outcome:** **CONFIRMED** (Target: ≥ +10 pp lift; Achieved: +14.27 pp lift; Bayesian Confidence: 100.0%).







