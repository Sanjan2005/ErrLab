# ErrLab — Complete Implementation Plan

## Summary

ErrLab is a small Python CLI (`errlab deploy`) that deliberately fails and shows flag-driven error messages. A Flagsmith A/B/C experiment measures which wording style (terse, with_fix, with_fix_and_link) best helps developers recover on the first retry. We'll start with **Flagsmith Cloud** (the user has registered and believes the managed warehouse is available on the free plan), falling back to **local Docker** only if Experimentation features are missing. We create the flag and metric with the Flagsmith CLI, build a minimal `errlab` package with all Flagsmith code isolated in `flags.py`, simulate ~9,000 seeded bot runs through the real SDK, capture results, ship the winner via the flag, and submit with a README and demo video. This is a **solo submission**. Total estimated build time: **~15 hours** across 3 days, well within the Nov 28 target (Nov 29 8 PM IST hard deadline).

---

## Phase Overview

| Phase | Goal | Est. Time | Day |
|---|---|---|---|
| 0 | Foundations: repo, tools, registrations | 30 min | Nov 26 |
| 1 | Flagsmith up and running (Cloud first, Docker fallback) | 1–1.5 h | Nov 26 |
| 2 | Build the CLI | 2 h | Nov 26 |
| 3 | Pipeline smoke test (Day 1 gate) | 1 h | Nov 26 |
| 4 | Simulation harness | 2.5 h | Nov 27 |
| 5 | A/A sanity check (optional) | 45 min | Nov 27 |
| 6 | Real experiment + analysis | 2 h | Nov 27 |
| 7 | Ship the winner | 1.5 h | Nov 28 |
| 8 | README, cleanup, security | 2 h | Nov 28 |
| 9 | Demo video + submission | 2 h | Nov 28 |
| **Total** | | **~15.5 h** | |

---

## 1. SDK Usage Reference (from live docs)

### 1a. Client initialisation

```python
from flagsmith import Flagsmith

flagsmith = Flagsmith(
    environment_key="YOUR_SERVER_SIDE_ENVIRONMENT_KEY",
    enable_events=True,  # Required for experimentation event collection
)
```

**Source:** docs.flagsmith.com/experimentation/run-an-experiment (Python tab) — "When initializing the Flagsmith client, make sure `enable_events=True` is set so that tracking data can flow back to your data store."

For self-hosted local, we also set the API URL:

```python
flagsmith = Flagsmith(
    environment_key="YOUR_SERVER_SIDE_ENVIRONMENT_KEY",
    enable_events=True,
    api_url="http://localhost:8000/api/v1/",
)
```

**Source:** docs.flagsmith.com/getting-started/run-locally-with-a-coding-agent — events on local go to `http://localhost:8000/api/v1/events/`.

### 1b. Evaluate the flag and record exposure

```python
flag = flagsmith.get_experiment_flag(
    feature_name="error_message_style",
    identifier="user-unique-id",
)
# flag.value contains the variant string (e.g. "terse", "with_fix", "with_fix_and_link")
```

**Source:** docs.flagsmith.com/experimentation/run-an-experiment — "`get_experiment_flag(feature_name, identifier, traits)` evaluates the flag and records the exposure in one call."

**Parameters:**
- `feature_name` (str): the flag key
- `identifier` (str): unique user/bot ID
- `traits` (dict, optional): user traits for targeting

Calling `get_experiment_flag` **automatically records an exposure event** — no separate call needed.

### 1c. Send the conversion event

```python
flagsmith.track_event(
    event_name="retry_succeeded",
    identifier="user-unique-id",
)
```

**Source:** docs.flagsmith.com/experimentation/run-an-experiment — "Records custom conversion metrics ... batched and pushed to the analytics data backend."

**Parameters:**
- `event_name` (str): must match the metric name created in Flagsmith
- `identifier` (str): same identifier used for exposure
- `value` (int/float, optional): numeric value (we don't need this)

### 1d. Flush events before exit

```python
flagsmith.event_processor.flush()
```

**Source:** docs.flagsmith.com/experimentation/run-an-experiment — "To manually force-flush pending queued events before your application closes down, invoke the internal event processor flush mechanism."

You can also configure the buffer size at init:

```python
from flagsmith.models import EventProcessorConfig

flagsmith = Flagsmith(
    environment_key="...",
    enable_events=True,
    event_processor_config=EventProcessorConfig(
        max_buffer_items=500,
    ),
)
```

> [!IMPORTANT]
> **Unclear signatures to verify at build time:**
> - The `api_url` parameter name for self-hosted. Verify by checking `flagsmith --help` or the Python SDK source. It may be `api_url`, `api`, or `default_flag_handler`.
> - Whether `EventProcessorConfig` is importable from `flagsmith.models` or another path in SDK 6.3.0+. Verify with `python -c "from flagsmith.models import EventProcessorConfig"`.
> - The exact flush call: might be `flagsmith.event_processor.flush()` or `flagsmith.flush()`. Verify before writing `flags.py`.

---

## 2. Proposed Repo Structure

```
ErrLab/
├── AGENTS.md                    # Standing project context
├── README.md                    # Submission README
├── .env.example                 # Template: FLAGSMITH_ENVIRONMENT_KEY=your_key_here
├── .gitignore                   # .env, *.env, results/raw/, __pycache__, etc.
├── pyproject.toml               # Project metadata + dependencies
├── docs/
│   └── PLAN.md                  # This plan
├── errlab/
│   ├── __init__.py              # Package init, version
│   ├── cli.py                   # argparse entry point: `errlab deploy`, `errlab retry`
│   ├── core.py                  # attempt_deploy(identity, scenario) → result + error msg
│   ├── messages.py              # Three variant templates × three error types (9 strings)
│   ├── flags.py                 # ALL Flagsmith code: init, get_experiment_flag, track_event, flush
│   └── identity.py              # Generate/persist anonymous user ID (~/.errlab/identity)
├── simulate/
│   ├── run.py                   # Simulation harness: --n, --seed, --dry-run
│   └── model.yaml               # Ground-truth recovery rates per variant (and optionally per error)
├── tests/
│   ├── test_messages.py         # Unit tests for message rendering (no Flagsmith needed)
│   ├── test_core.py             # Unit tests for core logic with mocked flags
│   └── test_identity.py         # Identity generation/persistence tests
├── results/
│   ├── raw/                     # (gitignored) CSV output from simulation
│   └── screenshots/             # Experiment result screenshots for README
└── scripts/
    └── smoke_test.py            # Phase 3: 20-identity pipeline test
```

### Module responsibilities

| Module | Responsibility | Imports Flagsmith? |
|---|---|---|
| `cli.py` | Parses `errlab deploy --scenario <X>` and `errlab retry`. Entry point. | No — calls `core` and `flags` |
| `core.py` | `attempt_deploy(identity, scenario)` — simulates a deploy, returns success/failure + the error shown. Both CLI and simulation call this. | No — calls `flags` and `messages` |
| `messages.py` | 9 static templates: 3 variants × 3 error types. Pure data, no logic. | No |
| `flags.py` | **Only** module that imports `flagsmith`. Exposes: `init()`, `get_variant(identity) → str`, `record_conversion(identity)`, `flush()`. Reads env vars. | **Yes** |
| `identity.py` | Generates a UUID, saves to `~/.errlab/identity`, returns it on subsequent calls. | No |
| `simulate/run.py` | Seeded bot loop. Calls `core.attempt_deploy` per bot with real SDK. Writes CSV. | Indirectly via `core` → `flags` |

---

## 3. Flagsmith Cloud vs. Local Docker Decision

### Decision: **Local Docker (self-hosted)**

### Reasoning

| Factor | Cloud | Local Docker |
|---|---|---|
| Experimentation available? | Only on **Scale-Up or Enterprise** plans (confirmed by docs) | Yes, with `EXPERIMENTATION_ENABLED: 'true'` and a warehouse (or Postgres fallback for testing) |
| Cost | Free tier likely does NOT include Experiments | Free (just Docker) |
| Warehouse | Managed ClickHouse (paid plans only) | Postgres fallback for local dev/testing (docs say "strictly for local development") |
| Hackathon context | Hackathon says "Cloud is free to start" but doesn't guarantee Experimentation | Full control, no account gatekeeping |

> [!WARNING]
> **Discrepancy with PLAN.md:** PLAN.md says "Flagsmith Cloud may be limited to Enterprise plans" and to "fall back to local Docker." The live docs confirm this: Cloud Experimentation needs Scale-Up/Enterprise. So we go local from the start, saving 15 minutes of Cloud debugging.

### Quick 15-minute confirmation check

1. Run `docker info` and `docker compose version` — confirm Docker is running (2 min)
2. Confirm ports 8000 and 8001 are free: `netstat -ano | findstr ":8000 :8001"` (1 min)
3. Pull and start Flagsmith:
   ```bash
   curl -o docker-compose.yml https://raw.githubusercontent.com/Flagsmith/flagsmith/main/docker-compose.yml
   docker compose up -d
   ```
   (5–8 min for first pull)
4. Open `http://localhost:8000`, create superuser account, check that "Experiments" tab appears in environment settings (3 min)
5. If Experiments tab is missing, set `EXPERIMENTATION_ENABLED: 'true'` in docker-compose env and restart (2 min)

**If this fails**, fall back to Flagsmith Cloud and check whether the hackathon provides an upgraded account or coupon.

---

## 4. Simulation Design

### Bot decision logic

Each simulated bot follows the **exact same code path** a real user would:

```
1. Bot gets a unique identity: f"bot-{seed}-{index:05d}"
2. Bot picks a random error scenario (uniform across 3 types)
3. Bot calls core.attempt_deploy(identity, scenario)
   → This internally calls flags.get_variant(identity) via get_experiment_flag
   → Flagsmith assigns a variant and records the exposure
   → The error message for that variant+scenario is displayed (logged)
4. Bot decides whether to retry successfully:
   → Look up the ground-truth recovery rate for the assigned variant
   → Draw a random float; if < rate, retry succeeds
5. If retry succeeds → flags.record_conversion(identity)
6. Log the row: identity, variant, scenario, retry_outcome to CSV
```

### Seeding

```python
import random
rng = random.Random(seed)  # Dedicated RNG instance, not global
```

- The seed is passed via `--seed` (default: a fixed value like `20261127`)
- The seed is saved in the CSV header and in `simulate/model.yaml`
- Flagsmith's own variant assignment is **not** controlled by our seed (it's server-side bucketing), but the bot's retry decision **is** seeded and reproducible

### Sample size

| Variant | Target N | Recovery rate |
|---|---|---|
| terse (control) | 3,000 | 35% |
| with_fix | 3,000 | 48% |
| with_fix_and_link | 3,000 | 50% |

**Total: ~9,000 bots.** Since Flagsmith handles traffic split (roughly 33/33/33), we run `--n 9000` total.

**Why 3,000:** The 13pp gap (terse → with_fix) is detectable with ~300/variant. The 2pp gap (with_fix → with_fix_and_link) needs thousands, and even at 3,000 it may not reach 95% win probability — which we document honestly as expected.

### Stopping rule

- **Fixed-horizon, no peeking, no early stopping.** We run all 9,000 bots, then look at results once.
- Write the sample size into `simulate/model.yaml` **before** the main run.
- If the local instance struggles under load, reduce to 3,000 total (1,000/variant), state it in the README.

### Concurrency handling

- **Sequential processing**: one bot at a time, with a small sleep between API calls (e.g. 50–100ms)
- Remote evaluation means one HTTP call per `get_experiment_flag` and one per `track_event`
- At 100ms/call, 9,000 bots × ~2 calls each = ~30 min total — acceptable
- **No threading**: keeps it simple, avoids rate limit issues, and the SDK's event buffer handles batching
- If too slow, we can batch with `asyncio` using a semaphore of 5–10 concurrent requests, but start sequential

### CSV cross-check

Output file: `results/raw/simulation_YYYYMMDD_HHMMSS.csv`

```csv
identity,variant,scenario,retry_outcome,timestamp
bot-20261127-00001,with_fix,port_in_use,success,2026-11-27T10:00:01
bot-20261127-00002,terse,invalid_config,failure,2026-11-27T10:00:01
...
```

**Cross-check procedure:**
1. After simulation, compute conversion rates per variant from the CSV
2. Compare against Flagsmith's dashboard numbers (allow ±2% for batching delay/event loss)
3. Document both numbers in the README

### Ground-truth rate mapping

```yaml
# simulate/model.yaml
seed: 20261127
sample_size: 9000
variants:
  terse:
    recovery_rate: 0.35
  with_fix:
    recovery_rate: 0.48
  with_fix_and_link:
    recovery_rate: 0.50
```

Optionally, per-error-type rates (labeled as exploratory):

```yaml
variants:
  terse:
    invalid_config: 0.30
    missing_api_key: 0.35
    port_in_use: 0.40
  with_fix:
    invalid_config: 0.45
    missing_api_key: 0.50
    port_in_use: 0.49
  with_fix_and_link:
    invalid_config: 0.47
    missing_api_key: 0.55
    port_in_use: 0.48
```

If used, the **primary result** is still the flat per-variant rate; per-error breakdown is exploratory.

---

## 5. Secrets-Handling Plan

### Where secrets live

| Secret | Location | In repo? |
|---|---|---|
| `FLAGSMITH_ENVIRONMENT_KEY` | `.env` file in project root | **No** (gitignored) |
| `FLAGSMITH_API_URL` | `.env` file | **No** |
| Flagsmith CLI credentials | `~/.flagsmith/` or wherever `flagsmith init` stores them | **No** (outside repo) |
| Docker superuser password | Set during first `localhost:8000` setup | **No** (not stored in files) |

### What is gitignored (already in `.gitignore`)

```
.env
*.env
results/raw/
__pycache__/
*.pyc
.venv/
```

### `.env.example` (committed, no real values)

```bash
# Copy to .env and fill in your values
FLAGSMITH_ENVIRONMENT_KEY=your_server_side_environment_key_here
FLAGSMITH_API_URL=http://localhost:8000/api/v1/
```

### Verification steps

1. Before every commit: `git diff --staged` to check no keys appear
2. Before final submission: `grep -rn "FLAGSMITH\|api_key\|environment_key\|password" --include="*.py" --include="*.md" --include="*.yaml"` — should return only placeholder references
3. Check git history: `git log --all -p | grep -i "key\|secret\|password"` — should return nothing real
4. `.env` is loaded via `python-dotenv` in `flags.py`, never hardcoded

---

## Detailed Phase-by-Phase Plan

---

### Phase 0: Foundations (30 min)

**Goal:** Repo exists, tools verified, registrations done.

**Deliverable:** A committed repo with AGENTS.md, .gitignore, .env.example, and docs/PLAN.md.

**Steps:**

1. **Register on WeMakeDevs** — go to wemakedevs.org/hackathons/flagsmith, register, join Flagsmith Discord, star the Flagsmith GitHub repo
2. **Verify tools:**
   ```powershell
   python --version          # Expect 3.10+
   git --version             # Any recent
   docker info               # Docker running
   docker compose version    # Compose v2
   ```
3. **Check existing repo state** — AGENTS.md, .gitignore, docs/PLAN.md already exist
4. **Fill in `.env.example`:**
   ```bash
   # Copy to .env and fill in your values
   FLAGSMITH_ENVIRONMENT_KEY=your_server_side_environment_key_here
   FLAGSMITH_API_URL=http://localhost:8000/api/v1/
   ```
5. **Create `pyproject.toml`** at repo root:
   ```toml
   [project]
   name = "errlab"
   version = "0.1.0"
   requires-python = ">=3.10"
   dependencies = [
       "flagsmith>=6.3.0",
       "python-dotenv>=1.0.0",
       "pyyaml>=6.0",
   ]

   [project.optional-dependencies]
   dev = ["pytest>=7.0"]

   [project.scripts]
   errlab = "errlab.cli:main"
   ```
6. **Commit and push:**
   ```bash
   git add -A && git commit -m "Phase 0: foundations" && git push
   ```

**Verify:** `python --version` ≥ 3.10, `docker info` succeeds, repo has all files, `git log --oneline` shows the commit.

**What could go wrong:**
- Docker not installed or not running → install Docker Desktop, restart
- Python < 3.10 → install from python.org
- Git push fails → check SSH keys / HTTPS token

**Time estimate:** 30 min

---

### Phase 1: Flagsmith Up and Running (1.5–2 h)

**Goal:** Local Flagsmith instance with Experimentation enabled, the flag created with all three keyed variants, the metric created, and a draft experiment.

**Deliverable:** Dashboard shows the flag, metric, and draft experiment. CLI is authenticated.

**Steps:**

1. **Free ports:**
   ```powershell
   netstat -ano | findstr ":8000 :8001"
   ```
   Kill anything on those ports.

2. **Pull and start Flagsmith:**
   ```powershell
   cd c:\Users\Surya\Documents\projects
   curl -o docker-compose.yml https://raw.githubusercontent.com/Flagsmith/flagsmith/main/docker-compose.yml
   docker compose up -d
   ```
   Wait for all containers to be healthy (~5 min on first pull, could be longer).

3. **Create superuser:** Open `http://localhost:8000`, follow the welcome screen to create org, project, and environments (Development + Production). Note down the **server-side environment key** for Development.

4. **Enable Experimentation** (if not already): In docker-compose.yml, ensure `EXPERIMENTATION_ENABLED: 'true'` is set in the API service environment. Restart if changed.

5. **Install Flagsmith CLI:**
   ```powershell
   pip install flagsmith-cli
   # or: npm install -g flagsmith-cli
   ```
   Authenticate:
   ```bash
   flagsmith login  # Points at localhost:8000
   flagsmith init   # Select org, project, Development environment
   ```
   This writes `flagsmith.json` locally. **Keep CLI credentials outside the repo** (they go to `~/.flagsmith/` by default).

6. **Create the flag:**
   ```bash
   flagsmith feature create error_message_style --value "terse" --enabled
   ```

7. **Add keyed variants:**
   ```bash
   flagsmith feature variant add error_message_style --key terse --value "terse" --weight 33
   flagsmith feature variant add error_message_style --key with_fix --value "with_fix" --weight 33
   flagsmith feature variant add error_message_style --key with_fix_and_link --value "with_fix_and_link" --weight 34
   ```

8. **Verify every variant has a key:**
   ```bash
   flagsmith feature get error_message_style --json
   ```
   Each variant in the output must have a non-empty `key` field. **This is critical** — variants without keys record no exposures.

9. **Create the metric:** Via the dashboard (Environment → Experiments → create metric `retry_succeeded` of type "occurrence/conversion").

10. **Create a draft experiment:** Via the dashboard — link it to the flag `error_message_style` and the metric `retry_succeeded`. Leave it in draft.

11. **Connect warehouse (if needed):** For local Postgres fallback (suitable for testing), the docs say events go to Postgres automatically. Verify in Environment Settings → Warehouse.

12. **Save the environment key to `.env`:**
    ```bash
    echo "FLAGSMITH_ENVIRONMENT_KEY=ser.your_key_here" > .env
    echo "FLAGSMITH_API_URL=http://localhost:8000/api/v1/" >> .env
    ```

**Verify:**
- `http://localhost:8000` dashboard shows the flag with 3 keyed variants
- Metric `retry_succeeded` exists
- Draft experiment links the flag and metric
- `flagsmith feature get error_message_style --json` shows all three variant keys
- `.env` has the environment key (not committed)

**What could go wrong:**
- Docker pull takes forever → pre-pull images, increase Docker memory to 4GB+
- Ports in use → `netstat` check, kill conflicting processes
- CLI auth fails → check API URL (`http://localhost:8000/api/v1/`), try browser login first
- Experimentation tab missing → verify `EXPERIMENTATION_ENABLED` env var in docker-compose
- Variant keys missing → re-add with explicit `--key` flag; verify with `--json`

**Fallback:** If local Docker is completely broken, try Flagsmith Cloud. Create account, check if Experiments tab exists. If not, ask in Flagsmith Discord whether hackathon participants get access.

**Time estimate:** 1.5–2 h (Docker pull is the wildcard)

---

### Phase 2: Build the CLI (2 h)

**Goal:** A working `errlab deploy --scenario <X>` command where error wording comes entirely from the Flagsmith flag.

**Deliverable:** Files created: `errlab/__init__.py`, `errlab/cli.py`, `errlab/core.py`, `errlab/messages.py`, `errlab/flags.py`, `errlab/identity.py`, `tests/test_messages.py`.

**Steps:**

1. **Create `errlab/flags.py`** — the ONLY module that imports flagsmith:
   ```python
   import os
   from dotenv import load_dotenv
   from flagsmith import Flagsmith

   load_dotenv()
   _client = None

   def init():
       global _client
       _client = Flagsmith(
           environment_key=os.environ["FLAGSMITH_ENVIRONMENT_KEY"],
           enable_events=True,
           api_url=os.environ.get("FLAGSMITH_API_URL", "https://edge.api.flagsmith.com/api/v1/"),
       )

   def get_variant(identity: str) -> str:
       flag = _client.get_experiment_flag(
           feature_name="error_message_style",
           identifier=identity,
       )
       return flag.value

   def record_conversion(identity: str):
       _client.track_event(
           event_name="retry_succeeded",
           identifier=identity,
       )

   def flush():
       _client.event_processor.flush()
   ```

2. **Create `errlab/messages.py`** — 9 templates (3 variants × 3 error types):
   ```python
   MESSAGES = {
       "terse": {
           "invalid_config": "Error: invalid configuration.",
           "missing_api_key": "Error: API key not found.",
           "port_in_use": "Error: port already in use.",
       },
       "with_fix": {
           "invalid_config": "Error: invalid configuration.\nFix: Check that config.yaml exists and has a valid 'deploy.target' field.",
           "missing_api_key": "Error: API key not found.\nFix: Run `errlab config set-key <YOUR_KEY>` or set the DEPLOY_API_KEY env var.",
           "port_in_use": "Error: port 8080 already in use.\nFix: Run `lsof -i :8080` to find the process, then kill it.",
       },
       "with_fix_and_link": {
           # Same as with_fix, plus a docs link
       },
   }

   def get_error_message(variant: str, scenario: str) -> str:
       return MESSAGES[variant][scenario]
   ```

3. **Create `errlab/core.py`** — shared by CLI and simulation:
   ```python
   from errlab import flags, messages

   def attempt_deploy(identity: str, scenario: str) -> dict:
       # 1. Simulate the deploy failure
       # 2. Get the variant from Flagsmith (records exposure)
       variant = flags.get_variant(identity)
       # 3. Get the appropriate error message
       error_msg = messages.get_error_message(variant, scenario)
       # 4. Return structured result
       return {"variant": variant, "error_message": error_msg, "scenario": scenario}
   ```

4. **Create `errlab/identity.py`** — persistent anonymous ID:
   ```python
   import uuid
   from pathlib import Path

   IDENTITY_FILE = Path.home() / ".errlab" / "identity"

   def get_or_create_identity() -> str:
       if IDENTITY_FILE.exists():
           return IDENTITY_FILE.read_text().strip()
       IDENTITY_FILE.parent.mkdir(parents=True, exist_ok=True)
       identity = f"user-{uuid.uuid4().hex[:12]}"
       IDENTITY_FILE.write_text(identity)
       return identity
   ```

5. **Create `errlab/cli.py`** — entry point:
   ```python
   import argparse
   from errlab import core, flags, identity

   def main():
       parser = argparse.ArgumentParser(prog="errlab")
       sub = parser.add_subparsers(dest="command")

       deploy = sub.add_parser("deploy")
       deploy.add_argument("--scenario", choices=["invalid_config", "missing_api_key", "port_in_use"],
                           default="invalid_config")

       args = parser.parse_args()
       if args.command == "deploy":
           flags.init()
           user_id = identity.get_or_create_identity()
           result = core.attempt_deploy(user_id, args.scenario)
           print(result["error_message"])
           flags.flush()
   ```

6. **Create `errlab/__init__.py`:**
   ```python
   """ErrLab: A/B testing CLI error messages with Flagsmith."""
   ```

7. **Create `tests/test_messages.py`** — unit tests that don't need Flagsmith:
   ```python
   from errlab.messages import get_error_message, MESSAGES

   def test_all_variants_and_scenarios_exist():
       for variant in ["terse", "with_fix", "with_fix_and_link"]:
           for scenario in ["invalid_config", "missing_api_key", "port_in_use"]:
               msg = get_error_message(variant, scenario)
               assert isinstance(msg, str) and len(msg) > 0

   def test_terse_is_shortest():
       for scenario in ["invalid_config", "missing_api_key", "port_in_use"]:
           assert len(MESSAGES["terse"][scenario]) < len(MESSAGES["with_fix"][scenario])
   ```

8. **Install and test:**
   ```bash
   pip install -e ".[dev]"
   pytest tests/test_messages.py -v
   errlab deploy --scenario invalid_config
   ```

9. **Manual variant check:** Change the flag's control value or variant weights in the Flagsmith dashboard. Run `errlab deploy` again. The message should change.

**Verify:**
- `pytest tests/test_messages.py` passes
- `errlab deploy --scenario port_in_use` prints a message
- Changing the served variant in the Flagsmith dashboard changes what `errlab deploy` prints
- `git diff` shows only new files, no secrets

**What could go wrong:**
- `flagsmith` SDK import error → check `pip install flagsmith>=6.3.0`
- `api_url` parameter name wrong → check SDK source or `help(Flagsmith.__init__)`
- `get_experiment_flag` raises → verify flag name matches exactly, identity is a string
- `flag.value` returns unexpected type → check with `print(type(flag.value), flag.value)`

**Fallback:** If `get_experiment_flag` doesn't exist in the installed SDK version, fall back to `get_identity_flags` + manual exposure tracking (check docs for alternative approach).

**Time estimate:** 2 h

---

### Phase 3: Pipeline Smoke Test — Day 1 Gate (1 h)

**Goal:** Prove the end-to-end data path: exposure + conversion events appear in Flagsmith.

**Deliverable:** `scripts/smoke_test.py` runs 20 identities; Flagsmith dashboard shows exposures and conversions.

**Steps:**

1. **Create `scripts/smoke_test.py`:**
   ```python
   """Run 20 identities through attempt_deploy, half retry successfully."""
   import time
   from errlab import flags, core

   flags.init()
   scenarios = ["invalid_config", "missing_api_key", "port_in_use"]

   for i in range(20):
       identity = f"smoke-{i:04d}"
       scenario = scenarios[i % 3]
       result = core.attempt_deploy(identity, scenario)
       print(f"{identity}: variant={result['variant']}, scenario={scenario}")

       # Simulate: even-numbered bots retry successfully
       if i % 2 == 0:
           flags.record_conversion(identity)
           print(f"  → retry succeeded")
       time.sleep(0.1)

   flags.flush()
   print("Done. Check Flagsmith dashboard for exposures and conversions.")
   ```

2. **Start the experiment** in the dashboard (change from draft to running).

3. **Run the smoke test:**
   ```bash
   python scripts/smoke_test.py
   ```

4. **Wait 1–2 minutes** for events to be processed.

5. **Check the dashboard:** Navigate to the experiment → verify exposures and conversions appear for all three variants.

**Troubleshooting order** (if data doesn't appear):

1. Events URL correct? Check `FLAGSMITH_API_URL` in `.env` matches the Docker instance
2. Every variant has a key? `flagsmith feature get error_message_style --json`
3. Same identifier for exposure and conversion? Print both in smoke test
4. Events flushed? Add a `time.sleep(5)` after `flush()` and check
5. Experiment actually running (not still in draft)?
6. Post the exact error in Flagsmith Discord

**Verify:**
- Flagsmith dashboard → Experiment page shows non-zero exposures and conversions
- At least 2 of the 3 variants show some conversions (depends on traffic split)

**What could go wrong:**
- Events silently dropped → check Docker logs: `docker compose logs api`
- Warehouse connection missing → for Postgres fallback, check env var `EXPERIMENTATION_ENABLED`
- Experiment in wrong state → ensure it's "Running", not "Draft" or "Stopped"

**Fallback:** If events don't appear after 30 min of debugging, post in Flagsmith Discord with exact error. If still stuck on Nov 27, reduce experiment scope to 2 variants (terse + with_fix) to simplify debugging.

**Time estimate:** 1 h

> [!IMPORTANT]
> **Day 1 Gate:** Do NOT proceed past this phase until exposures and conversions are visible in Flagsmith. Commit everything and stop for the night.

---

### Phase 4: Simulation Harness (2.5 h)

**Goal:** A reproducible, seeded simulation that runs ~9,000 bots through the real SDK.

**Deliverable:** `simulate/run.py`, `simulate/model.yaml`, CSV output in `results/raw/`.

**Steps:**

1. **Create `simulate/model.yaml`:**
   ```yaml
   seed: 20261127
   sample_size: 9000
   stopping_rule: "Fixed-horizon. Run all N bots, then look at results once."
   variants:
     terse:
       recovery_rate: 0.35
     with_fix:
       recovery_rate: 0.48
     with_fix_and_link:
       recovery_rate: 0.50
   ```

2. **Create `simulate/run.py`:**
   ```python
   """
   Seeded simulation harness for ErrLab.
   Each bot: get unique ID → trigger error → receive flag-driven message → retry with ground-truth probability.
   """
   import argparse, csv, random, time, yaml, sys
   from pathlib import Path
   from datetime import datetime
   from errlab import flags, core

   def load_model(path="simulate/model.yaml"):
       with open(path) as f:
           return yaml.safe_load(f)

   def run(n, seed, dry_run=False):
       model = load_model()
       rng = random.Random(seed)
       scenarios = ["invalid_config", "missing_api_key", "port_in_use"]

       if not dry_run:
           flags.init()

       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       out_path = Path(f"results/raw/simulation_{timestamp}.csv")
       out_path.parent.mkdir(parents=True, exist_ok=True)

       with open(out_path, "w", newline="") as f:
           writer = csv.writer(f)
           writer.writerow(["identity", "variant", "scenario", "retry_outcome", "timestamp"])

           for i in range(n):
               identity = f"bot-{seed}-{i:05d}"
               scenario = rng.choice(scenarios)

               if dry_run:
                   variant = rng.choice(["terse", "with_fix", "with_fix_and_link"])
               else:
                   result = core.attempt_deploy(identity, scenario)
                   variant = result["variant"]

               # Bot decision: retry success based on ground-truth rate
               rate = model["variants"][variant]["recovery_rate"]
               retry_success = rng.random() < rate

               if retry_success and not dry_run:
                   flags.record_conversion(identity)

               outcome = "success" if retry_success else "failure"
               writer.writerow([identity, variant, scenario, outcome,
                               datetime.now().isoformat()])

               if i % 500 == 0:
                   print(f"  Progress: {i}/{n} bots processed")

               if not dry_run:
                   time.sleep(0.05)  # 50ms between calls

       if not dry_run:
           flags.flush()
           time.sleep(5)  # Let events land

       print(f"Done. Output: {out_path}")

   if __name__ == "__main__":
       parser = argparse.ArgumentParser()
       parser.add_argument("--n", type=int, default=9000)
       parser.add_argument("--seed", type=int, default=20261127)
       parser.add_argument("--dry-run", action="store_true")
       args = parser.parse_args()
       run(args.n, args.seed, args.dry_run)
   ```

3. **Pilot run (300 bots):**
   ```bash
   python simulate/run.py --n 300 --seed 42
   ```

4. **Cross-check:** Count conversions per variant in the CSV:
   ```python
   import pandas as pd
   df = pd.read_csv("results/raw/simulation_*.csv")
   print(df.groupby("variant")["retry_outcome"].value_counts(normalize=True))
   ```
   Rates should roughly match the model (±5% at n=100/variant).

5. **Verify in Flagsmith:** Check that exposure and conversion counts are close to the CSV counts.

6. **Dry-run test:**
   ```bash
   python simulate/run.py --n 100 --dry-run
   ```
   Should complete in seconds with no network calls.

**Verify:**
- `results/raw/simulation_*.csv` exists with correct columns
- Per-variant conversion rates in CSV roughly match model rates (35%, 48%, 50%)
- Flagsmith dashboard numbers roughly match CSV numbers (±2%)
- `--dry-run` works without Flagsmith

**What could go wrong:**
- Rate limiting from Flagsmith API → increase sleep interval to 100ms
- SDK throws on rapid sequential calls → add retry logic with backoff
- Memory issues on 9K bots → process in batches of 1000, flushing between

**Fallback:** If 9,000 bots is too slow or unstable, reduce to 3,000 (1,000/variant). Still enough to detect the 13pp effect. State the reduced sample in the README.

**Time estimate:** 2.5 h

---

### Phase 5: A/A Sanity Check (Optional, 45 min)

**Goal:** Prove the pipeline is unbiased by running identical variants and showing no winner.

**Decision:** Skip this if behind schedule. It's valuable but not required for submission.

**Steps:**

1. Create a second flag `aa_test_flag` with two variants that render identical messages
2. Run 600 bots (300/variant) with equal ground-truth rates (40%/40%)
3. Check that neither variant has >70% win probability (i.e. no confident winner)
4. Screenshot the flat result

**Verify:** No variant shows > 70% win probability.

**Skip condition:** If Phase 4 finished late (after ~6 PM Nov 27), skip this entirely.

**Time estimate:** 45 min

---

### Phase 6: The Real Experiment + Analysis (2 h)

**Goal:** Run the full 9,000-bot simulation, capture results, explain them.

**Deliverable:** Screenshots of results, 5-line summary, CSV cross-check.

**Steps:**

1. **Confirm pre-registration:** Verify `simulate/model.yaml` has sample_size and stopping_rule written (from Phase 4).

2. **Reset or start fresh experiment** in dashboard if the Phase 3/4 pilot data is mixed in. Alternatively, create a new experiment linked to the same flag and metric.

3. **Run the full simulation:**
   ```bash
   python simulate/run.py --n 9000 --seed 20261127
   ```
   Estimated runtime: ~15–30 min.

4. **Wait for events to land** — give it 5–10 minutes after the script finishes.

5. **Screenshot results:**
   - Win probability per variant
   - Lift estimates
   - Credible intervals (if shown)
   - Save to `results/screenshots/`

6. **Cross-check headline numbers:**
   ```python
   import pandas as pd
   df = pd.read_csv("results/raw/simulation_*.csv")  # latest file
   summary = df.groupby("variant")["retry_outcome"].apply(
       lambda x: (x == "success").mean()
   )
   print(summary)
   ```
   Compare with Flagsmith's reported rates.

7. **Write 5-line summary:**
   ```
   Hypothesis: Adding a concrete fix raises recovery by ≥10pp.
   Sample: ~3,000 bots per variant (9,000 total), simulated, seed=20261127.
   Winner: with_fix_and_link (50% recovery) vs terse (35% recovery).
   Lift: ~15pp for with_fix vs control; ~2pp for with_fix_and_link vs with_fix.
   Caveat: The 2pp link advantage likely not statistically confident at this sample size.
   ```

8. **Any per-error-type breakdown** from the CSV is labeled "exploratory, not the primary result."

**Verify:**
- Screenshots exist in `results/screenshots/`
- CSV cross-check matches Flagsmith within ±2%
- Written summary is honest about simulated traffic and built-in effects

**What could go wrong:**
- Flagsmith shows "collecting data" instead of results → minimum thresholds not met (need 50 identities and 5 conversions per variant — easily met at 3,000/variant)
- Results don't match CSV → check for duplicate identities or missing conversions

**Time estimate:** 2 h

---

### Phase 7: Ship the Winner (1.5 h)

**Goal:** Roll out the winning variant through the flag with no code change.

**Deliverable:** Before/after terminal recording; `git diff` shows no code changes.

**Steps:**

1. **Stop the experiment** in the dashboard (follow the docs: Experiment → Stop).

2. **Roll out the winner:** In the dashboard, set the flag `error_message_style` default value to the winning variant (e.g. `with_fix_and_link`) and set its weight to 100%.
   ```bash
   flagsmith flag update error_message_style --value "with_fix_and_link"
   flagsmith flag update error_message_style --weight with_fix_and_link=100 --weight terse=0 --weight with_fix=0
   ```

3. **Demonstrate no code change:**
   ```bash
   git status   # Should show nothing modified
   git diff     # Empty
   errlab deploy --scenario missing_api_key
   # Should print the with_fix_and_link version
   ```

4. **Record terminal capture:** Use a tool like `asciinema` or Windows Terminal's built-in recording, or a screen recorder for the demo video.

**Verify:**
- `errlab deploy` now shows the winner's message for all scenarios
- `git diff` is empty — no code changed
- Terminal recording saved

**What could go wrong:**
- Flag rollout doesn't take effect immediately → clear any SDK caching, restart
- CLI still shows old variant → identity may be sticky-bucketed; use a new identity or restart

**Time estimate:** 1.5 h

---

### Phase 8: README, Cleanup, Security (2 h)

**Goal:** Submission-ready repo with a complete README.

**Deliverable:** Updated README.md, all tests passing, no secrets anywhere.

**Steps:**

1. **Write README.md** with sections:
   - One-line pitch and hypothesis
   - How Flagsmith is used (flag → variants → metric → exposure/conversion → experiment → ship winner)
   - Setup steps (Docker, env vars, install, run CLI, run simulation)
   - Simulation model (stated plainly: rates, seed, sample size)
   - Results with screenshots, caveats, next steps
   - Project structure

2. **Run full test suite:**
   ```bash
   pytest tests/ -v
   ```

3. **Fresh-clone test:** Clone to a temp directory, follow only the README:
   ```bash
   cd %TEMP% && git clone <repo-url> errlab-test && cd errlab-test
   # Follow README setup steps
   ```

4. **Security scan:**
   ```powershell
   git log --all -p | Select-String -Pattern "FLAGSMITH|api_key|password|secret" -CaseSensitive:$false
   # Should return only placeholders and documentation references
   ```

5. **Verify `.env.example`** has only placeholder values.

6. **Commit final:**
   ```bash
   git add -A && git commit -m "Phase 8: README and cleanup" && git push
   ```

**Verify:**
- `pytest` passes
- Fresh clone works with README instructions only
- `grep` finds no real secrets in git history
- `.env.example` present with placeholders

**What could go wrong:**
- Accidentally committed a key earlier → `git filter-branch` or `git-filter-repo` to rewrite history (nuclear option: re-create repo from clean files)
- Tests fail → fix and re-run

**Time estimate:** 2 h

---

### Phase 9: Demo Video + Submission (2 h)

**Goal:** 2–3 minute demo video uploaded, submission completed on WeMakeDevs.

**Deliverable:** Video file, completed submission form.

**Steps:**

1. **Check submission form** for length limits, format requirements, and required fields.

2. **Record demo video** (suggested structure from PLAN.md):
   - 0:00 — The problem: confusing CLI errors, the hypothesis
   - 0:30 — The CLI with three message styles (run `errlab deploy` with different variants)
   - 1:00 — The Flagsmith dashboard: flag, metric, experiment
   - 1:45 — Results screen: win probability, lift, what they mean
   - 2:30 — Shipping the winner: `git diff` empty, CLI shows new message
   - Throughout: state clearly that traffic is simulated and what effects were built in

3. **Recording tools:**
   - OBS Studio (free) or Windows Game Bar (Win+G) for screen recording
   - Or Loom for quick recording with webcam

4. **Upload video** to YouTube (unlisted) or wherever the submission form requires.

5. **Submit on WeMakeDevs:**
   - Public GitHub repo URL
   - Demo video URL
   - Team member info
   - Track: Track 01 (Test Something Real)

6. **Final verification:**
   - Repo is public
   - README links work
   - Video plays
   - All team members registered

**Verify:**
- Video is accessible from the submitted URL
- Submission form accepted
- Submitted before 8 PM IST Nov 29 (target: Nov 28)

**What could go wrong:**
- Video too long → edit down to key moments
- Upload fails → try alternative platform (Google Drive, Vimeo)
- Submission form has unexpected fields → fill in what's available, ask in Discord

**Time estimate:** 2 h

---

## Open Questions (ranked by importance)

> [!IMPORTANT]

1. **Have you registered on WeMakeDevs and do you have a Flagsmith Cloud account?**
   If you already have a Cloud account on a paid plan, we could skip Docker entirely. If not, local Docker is confirmed as the path.

2. **Docker Desktop installed and running on your machine?**
   The local path requires Docker with ≥4GB RAM allocated. If Docker isn't set up, that's a 30-min detour we should know about now.

3. **Do you want per-error-type ground-truth rates (exploratory breakdown), or keep it flat per-variant only?**
   Flat is simpler, more explainable, and covers the primary hypothesis. Per-error-type adds richness but complexity. Recommendation: flat only, mention per-error as "future work."

4. **Solo or team submission?**
   This affects the WeMakeDevs registration and whether we need to coordinate with anyone else.

5. **Screen recording tool preference?**
   OBS Studio is free and reliable. If you already have something else (Loom, Camtasia, Windows Game Bar), we'll use that instead.

---

## First Three Actions After Approval

1. **Phase 0 — set up foundations:** Verify Python/Docker/Git, fill in `.env.example`, create `pyproject.toml`, commit and push.

2. **Phase 1 — start Docker Flagsmith:** Pull `docker-compose.yml`, run `docker compose up -d`, create superuser, install CLI, create the flag with three keyed variants, create the metric, create draft experiment, save environment key to `.env`.

3. **Phase 2 — build the CLI:** Create all 6 source files (`flags.py`, `messages.py`, `core.py`, `identity.py`, `cli.py`, `__init__.py`), write `test_messages.py`, install with `pip install -e .`, run tests, manually verify the flag drives the CLI output.

---

> [!TIP]
> **Scope discipline:** Everything above is strictly one experiment done well. If at any point I suggest adding a web dashboard, extra commands, analytics charts, or anything beyond the Phase 0–9 deliverables, flag it as scope creep and say no.
