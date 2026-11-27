# ErrLab: Project Brief and Execution Plan

Toggle Wars: The Flagsmith Experimentation Hackathon · Track 01 (Test Something Real) · Prepared Nov 26, 2026

## 1. Project briefing

### The idea

ErrLab is a small Python command-line tool (a fake `deploy` command) that sometimes fails. How each error is worded is controlled by a Flagsmith multivariate flag. We run a real A/B/C experiment with Flagsmith Experimentation to learn which error-message style helps developers recover fastest, then ship the winner by changing the flag, with no code release.

### Why this idea

- Track 01 rewards one experiment done well, not a big app. The experiment is what counts.
- The audience is developers, so the problem (confusing CLI errors) is instantly relatable. This supports the Impact score.
- It shows the full Flagsmith loop: flag, variants, metric, traffic split, result, and rollout of the winner through the same flag. This supports the Use of Flagsmith score.
- It costs nothing: no paid APIs, and Flagsmith can run locally with Docker.
- Simulated traffic is explicitly allowed for Track 01, so the experiment can be run properly in about three days.

### What we aim to achieve

1. Run one well-designed A/B/C experiment with a clear hypothesis, a metric built from real SDK events, and results we can explain in plain language.
2. Keep Flagsmith at the core: the flag decides what users see, the SDK records exposures and conversions, and Flagsmith's Bayesian engine reports the result.
3. Finish with a complete, honest submission: public repo, README with setup steps and Flagsmith usage, and a short demo video.
4. Be able to explain every line of code, since AI coding tools are allowed but understanding is required.

**Hypothesis:** Adding a concrete fix to a CLI error message will raise the share of users who recover on their first retry by at least 10 percentage points over a terse message, because users don't have to diagnose the problem themselves.

### Experiment design at a glance

| Item | Decision |
| --- | --- |
| Flag | `error_message_style` (multivariate) |
| Variants | `terse` (control), `with_fix`, `with_fix_and_link` |
| Primary metric | `retry_succeeded`: the user's first retry after seeing an error succeeds |
| Exposure | Recorded when the error message is displayed |
| Identity | Stable anonymous ID per user (and per simulated bot) |
| Traffic | Simulated bots through the real SDK, seeded and reproducible |
| Ground-truth model | terse 35%, with\_fix 48%, with\_fix\_and\_link 50% recovery (documented openly) |
| Planned sample | About 3,000 bots per variant, fixed in advance, no peeking |
| Ending | Roll out the winning variant through the same flag |

### Deliverables

- [ ] Public GitHub repository
- [ ] Working ErrLab CLI with the flag-driven error messages
- [ ] Simulation harness with a documented model and a saved seed
- [ ] A completed Flagsmith experiment with results screenshots
- [ ] Winner shipped via the flag, with no code change
- [ ] README: pitch, hypothesis, how Flagsmith is used, setup steps, simulation model, results, caveats
- [ ] Demo video (about 2 to 3 minutes; confirm any length limit on the submission form)
- [ ] Submission completed on the WeMakeDevs page before the deadline

### How we will be judged

- Use of Flagsmith: is it core, and do the flags and experiments do real work?
- Impact: does it solve a real problem a developer or team would use?
- Creativity: is the idea new, or does it take a familiar idea somewhere new?
- Demo video: does it show the problem, what we built, and how Flagsmith fits in?
- Track 01 checklist: one experiment done well, a clear hypothesis, versions behind a flag, a metric from real events, and results we can explain.

### Key dates and rules

- Hacking: Nov 26, 8:00 AM IST to Nov 29, 8:00 PM IST. Late submissions are not accepted.
- Our internal target: finish by the end of Nov 28, leaving Nov 29 as buffer only.
- Teams of 1 to 4; every member must register; one track per project.
- Main coding must start after the hackathon begins. AI coding assistants are allowed, but we must understand and be able to explain the code.
- Submission needs: public GitHub repo, README with setup steps and Flagsmith usage, and a short demo video.
- Bonus: starring the Flagsmith repo on GitHub enters a random AirPods draw.

### Success criteria (definition of done)

- A fresh clone runs by following only the README.
- Flagsmith shows exposures and conversions for all three variants.
- The result is explained honestly, including that traffic is simulated.
- No secrets in the repo or its history.

## 2. Schedule and gates

| Day | Phases | Gate (true by end of day) |
| --- | --- | --- |
| Nov 26 | 0, 1, 2, 3 | One scripted user produces an exposure and a conversion that appear in Flagsmith |
| Nov 27 | 4, 5, 6 | Full experiment has run and results screenshots exist |
| Nov 28 | 7, 8, 9 | Everything submitted |

If the Day 1 gate slips, ask in the Flagsmith Discord first thing on Nov 27. Pipeline problems are the most likely time sink.

## 3. What the Flagsmith docs say (verified before planning)

- Experimentation is described as a beta feature, and on Cloud it may be limited to Enterprise plans. The hackathon says Cloud is free to start, so verify your account, and fall back to local Docker if Experiments are missing.
- Experiments currently work with remote evaluation only, and users must be identified. Use the same identifier for flags and events.
- Python SDK: `flagsmith` 6.3.0 or newer, initialised with `enable_events=True`.
- `get_experiment_flag(feature_name, identifier, traits)` evaluates the flag and records the exposure in one call. Only record exposure for identities that are in the experiment (the docs check `flag.experiment.in_experiment`).
- Variants need keys: a variant without a key records no exposures. The name `control` is reserved for the flag's own value. Check with `flagsmith feature get <flag> --json`.
- Self-hosted: point the SDK at your API and set the event ingestion URL (local default `http://localhost:8080/`), otherwise events go to Flagsmith Cloud.
- Events are sent in batches, so flush before a script exits. Look up the exact Python call in the docs.
- Exact `track_event` and flush signatures were not confirmed. Always have the agent read the docs instead of guessing.

## 4. Execution phases

### Phase 0: Foundations (30 min)

**Do**

- Register on the WeMakeDevs page (teammates too), join the Flagsmith Discord, and star the Flagsmith repo.
- Verify Python 3.10+, Git, Docker (running), and your coding agent.
- Create the public GitHub repo now.
- Add a `.gitignore` covering `.env`, `*.env` and `results/raw/`, plus an `.env.example`.
- Commit `AGENTS.md` (see Appendix A).

**Done when:** repo exists, tools verified, `AGENTS.md` committed.

### Phase 1: Flagsmith up and running (1.5 to 2 hours)

**Goal:** an environment with a warehouse connection, the flag, the metric and a draft experiment.

**Decision rule:** spend at most 15 minutes checking whether Experiments are available on Cloud. If not, go local with Docker. Local needs ports 8000, 8001 and 8080 free, and the first run pulls several images, so start early.

**Do**

- Use Flagsmith's own run-locally prompt and then the set-up-an-experiment prompt (links in Appendix C). They install the Flagsmith CLI, create the org API key and handle the warehouse connection.
- Keep CLI credentials in a file outside the repo.
- Create the flag, metric and experiment as designed, but leave the experiment in draft. Confirm every variant has a key.

**Agent prompt**

```
Read AGENTS.md. Set up Flagsmith for this project following Flagsmith's official experiment setup prompt/docs exactly. Create flag error_message_style with variants terse (control), with_fix, with_fix_and_link, and a metric for the event retry_succeeded. Keep the experiment in draft. After each step, verify and show me the output. If anything fails, stop and show the exact error.
```

**Done when:** flag, metric and draft experiment are visible in the dashboard, and the Flagsmith CLI is authenticated (local) or you are logged in (Cloud).

### Phase 2: Build the CLI (2 hours)

**Goal:** a real, small CLI where error wording comes entirely from the flag.

**Design**

- Structure: `errlab/core.py` (logic), `errlab/cli.py` (argument parsing), `errlab/messages.py` (three templates), `errlab/flags.py` (all Flagsmith code in one place).
- Command: `errlab deploy`, with three triggerable failures: `invalid_config`, `missing_api_key`, `port_in_use`.
- Each error has three renderings: terse; with a concrete fix; with a fix plus a docs link.
- Identity: generate an anonymous ID on first run, store it locally, and use it as the Flagsmith identifier.
- Put the deploy-and-retry logic in a function such as `attempt_deploy(identity, scenario)` that both the CLI and the simulation call, so the demo uses the same code path real users would.
- Call `get_experiment_flag` where the error is displayed. Send `retry_succeeded` only when the retry after that error succeeds.

**Agent prompt**

```
Read AGENTS.md and the Flagsmith run-an-experiment docs (Python tab). Build the errlab package: core.py with attempt_deploy(identity, scenario) returning success/failure plus the error shown; messages.py with the three variant templates for three errors; flags.py as the only module importing flagsmith, initialised with enable_events=True and pointing at my Flagsmith instance via env vars; cli.py with `errlab deploy --scenario ...` and `errlab retry`. Evaluate the flag with get_experiment_flag where the error message is displayed. Send the conversion event only when the retry succeeds. Persist an anonymous identity in a local file. Add unit tests for message rendering. Show me the SDK docs section you followed.
```

**Done when:** changing the served variant in the dashboard changes the wording when you run the CLI by hand.

### Phase 3: Pipeline smoke test (1 hour), the Day 1 gate

**Goal:** prove the end-to-end data path before building more.

**Do**

- Write a throwaway script that runs about 20 identities through `attempt_deploy`, with roughly half retrying successfully.
- Flush events before the script exits.
- Start the experiment and check that exposures and conversions appear.

**Troubleshooting order**

1. Events URL set correctly for self-hosted.
2. Every variant has a key.
3. The same identifier is used for exposure and conversion.
4. Events flushed before exit.
5. The experiment is actually running.
6. Post the exact error in Discord.

**Done when:** the experiment page shows exposures and conversions. Do not move on until this is true. Commit and stop for the day.

### Phase 4: Simulation harness (2.5 hours)

**Goal:** a reproducible, honest, seeded simulation that uses the real SDK.

**Ground-truth model** (record in `simulate/model.yaml` and the README)

| Variant | Recovery on first retry |
| --- | --- |
| terse | 35% |
| with\_fix | 48% |
| with\_fix\_and\_link | 50% |

The link adds only a little on top of the fix, which makes a more believable story than a clean sweep. Optionally vary effects by error type (for example, the docs link helps more for `missing_api_key`).

**Design rules**

- Seed the random generator and save the seed.
- Write the sample size and stopping rule before the main run, with no peeking and no early stopping.
- Each bot gets a unique ID, triggers an error, receives the flag-driven message through the real code path, then retries with a success probability from the model.
- Write a local CSV of what each bot saw and did, as a cross-check against Flagsmith.
- Control concurrency, since remote evaluation means one API call per bot.
- Flush events at the end.

**Agent prompt**

```
Read AGENTS.md. Build simulate/run.py: a seeded harness that creates N bots with unique identifiers, calls errlab.core.attempt_deploy for each (real Flagsmith SDK, no mocks), decides retry success from simulate/model.yaml (ground-truth recovery rates per variant, optionally per error type), logs every bot's identity/variant/error/outcome to results/raw/*.csv, handles concurrency and retries gracefully, and flushes events before exit. Add --n, --seed, --dry-run flags. Dry-run must not contact Flagsmith. Explain how bot decisions are made so I can describe it in the README.
```

**Done when:** a 300-bot pilot completes and the CSV counts roughly match Flagsmith's numbers (allowing for batching delay).

### Phase 5: A/A sanity check (optional, 45 min)

Only if Phase 4 finished comfortably. Create a second flag whose variants render identical messages, run a few hundred bots, and show that the result is roughly even with no confident winner. This shows the pipeline is not biased. Skip if behind.

### Phase 6: The real experiment and analysis (2 hours)

**Do**

1. Confirm the sample size and stopping rule written in Phase 4.
2. Start the experiment, run the full simulation, and let events finish landing.
3. Screenshot the results: win probability, lift and any intervals shown.
4. Explain win probability honestly: it is not a guarantee.
5. Cross-check headline numbers against your CSV.
6. Label any per-error-type breakdown from the CSV as exploratory, not the primary result.

**Done when:** you have the screenshots and a five-line summary: hypothesis, sample size, winner, lift, caveats.

### Phase 7: Ship the winner (1.5 hours)

**Do**

- Stop the experiment as the docs describe, then roll out the winning variant to everyone through the same flag.
- Without changing code, run the CLI and show the new message.
- Record a short before/after terminal capture. This is the clearest demonstration of flags and experiments working together.

**Done when:** a fresh CLI run shows the winner's message and `git diff` shows no code changes for the rollout.

### Phase 8: README, cleanup and security (2 hours)

**README contents**

1. One-line pitch and the hypothesis.
2. How Flagsmith is used: flag, variants, metric, exposure and conversion events, experiment, shipping the winner.
3. Setup steps anyone can follow (local Docker or Cloud, env vars, running the CLI and the simulation).
4. The simulation model, stated plainly: traffic is simulated; here are the assumed rates and the seed.
5. Results with screenshots, caveats and next steps.
6. Project structure.

**Cleanup checklist**

- No keys anywhere in the repo or git history; `.env.example` present.
- Tests pass.
- A fresh clone runs using only the README.
- Ask the agent for a secrets scan, then verify it yourself.

### Phase 9: Demo video and submission (2 hours)

Suggested structure (about 2 to 3 minutes):

- 0:00: the problem (confusing CLI errors) and the hypothesis.
- 0:30: the CLI with the three message styles.
- 1:00: the Flagsmith flag, metric and experiment.
- 1:45: the results screen, and what win probability and lift mean.
- 2:30: shipping the winner with no redeploy.
- Throughout: say clearly that traffic is simulated and what effect was built in.

Check the submission form for length limits and upload format. Submit once everything is verified. Treat Nov 29 as buffer, not working time.

## 5. Risks and mitigations

- **Experimentation access on Cloud** is the biggest unknown. Fall back to local Docker quickly.
- **Beta software:** if docs and behaviour disagree, trust behaviour and ask in Discord.
- **Scope creep:** no extra commands, web UI or dashboards. One experiment done well wins.
- **Explainability:** review every file the agent writes and be ready to describe it.
- **Time slip:** if the Day 1 gate is missed, drop Phase 5 first, then reduce the sample size before cutting anything else.

## 6. Final submission checklist

- [ ] All team members registered
- [ ] Public repo with README, setup steps and Flagsmith usage
- [ ] Experiment completed, screenshots saved
- [ ] Winner shipped via the flag
- [ ] Demo video recorded and uploaded
- [ ] No secrets in repo or history
- [ ] Submitted before 8:00 PM IST on Nov 29 (target: Nov 28)
- [ ] Starred the Flagsmith repo (AirPods draw)

## Appendix A: AGENTS.md (standing context for your coding agent)

```
# ErrLab: project context
Goal: Flagsmith Toggle Wars Track 01 entry. One well-designed A/B test, not a big app.
Hypothesis: concrete fix in a CLI error message raises first-retry recovery by >=10pp vs terse.
Stack: Python 3.10+, flagsmith SDK >=6.3.0 (remote evaluation, enable_events=True).
Flag: error_message_style, variants terse (control) / with_fix / with_fix_and_link.
Primary metric: retry_succeeded. Exposure recorded when the error message is displayed.
Rules:
- Read the Flagsmith docs (docs.flagsmith.com/experimentation/run-an-experiment) before writing SDK code. Never guess signatures.
- If something fails, stop and show me the exact error. Don't work around it.
- Never commit or print API keys. Use .env (gitignored).
- Work in small steps; verify each; keep code readable. I must be able to explain every line.
- Every user (including simulated bots) needs a stable identifier.
```

## Appendix B: Simulation sample-size note

A 13-point gap between terse and with\_fix is easy to detect with a few hundred users per variant. A 2-point gap between with\_fix and with\_fix\_and\_link needs thousands, which is why the plan fixes about 3,000 per variant. If the local instance struggles, run a smaller fixed sample, state it in the README, and do not claim a confident difference between the two close variants.

## Appendix C: Links

- Hackathon home: https://www.wemakedevs.org/hackathons/flagsmith
- Schedule: https://www.wemakedevs.org/hackathons/flagsmith/schedule
- Rules: https://www.wemakedevs.org/hackathons/flagsmith/rules
- Resources: https://www.wemakedevs.org/hackathons/flagsmith/resources
- Experimentation docs: https://docs.flagsmith.com/experimentation
- Run an experiment: https://docs.flagsmith.com/experimentation/run-an-experiment
- Set up with a coding agent: https://docs.flagsmith.com/experimentation/set-up-with-a-coding-agent
- Run Flagsmith locally with a coding agent: https://docs.flagsmith.com/getting-started/run-locally-with-a-coding-agent
- Example (PayPal button): https://docs.flagsmith.com/experimentation/example-paypal-button
- Statistics glossary: https://docs.flagsmith.com/experimentation/statistics
- Flagsmith GitHub: https://github.com/Flagsmith/flagsmith
- Flagsmith Discord: https://discord.gg/hFhxNtXzgm
