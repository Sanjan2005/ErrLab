"""Phase 5: A/A pipeline sanity check for ErrLab.

Runs 600 unique bot identities through the aa_test_flag experiment.
Both variants (replica / replica_b) render the EXACT same message,
and all bots have an identical 40% ground-truth conversion rate.

Expected outcome: neither variant should exceed 70% win probability
in the Flagsmith Bayesian engine — confirming the pipeline is unbiased.

Metric event:  aa_check_converted   (Flagsmith experiment ID 1545)
Feature flag:  aa_test_flag          (Flagsmith feature ID 307855)
Variants:      replica (38456)  |  replica_b (38458)   — identical text
"""

import sys
import time
import random
import csv
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from flagsmith import Flagsmith
import os

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AA_FEATURE_NAME = "aa_test_flag"
AA_METRIC_EVENT = "aa_check_converted"
NUM_BOTS = 600
SEED = 20261128          # Different seed from main sim to avoid identity overlap
GROUND_TRUTH_RATE = 0.40  # Same for BOTH variants — that is the whole point
DELAY = 0.02             # seconds between bots
BATCH_FLUSH = 100        # flush every N bots
EXPERIMENT_ID = 1545


def build_client() -> Flagsmith:
    key = os.environ.get("FLAGSMITH_ENVIRONMENT_KEY")
    url = os.environ.get("FLAGSMITH_API_URL", "https://edge.api.flagsmith.com/api/v1/")
    if not key:
        raise ValueError(
            "FLAGSMITH_ENVIRONMENT_KEY missing — set it in .env"
        )
    return Flagsmith(
        environment_key=key,
        enable_events=True,
        api_url=url,
    )


def run_aa_test() -> None:
    print("=" * 70)
    print("ErrLab Phase 5 — A/A Pipeline Sanity Check")
    print(f"Feature:        {AA_FEATURE_NAME}")
    print(f"Metric event:   {AA_METRIC_EVENT}")
    print(f"Bots:           {NUM_BOTS}  |  Seed: {SEED}")
    print(f"Ground-truth:   {GROUND_TRUTH_RATE:.0%} for EVERY variant (identical)")
    print("=" * 70)

    client = build_client()
    rng = random.Random(SEED)

    variant_stats: dict[str, dict[str, int]] = {}

    out_dir = PROJECT_ROOT / "results" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = out_dir / f"aa_test_{timestamp}.csv"

    start_time = time.time()

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["identity", "variant", "converted", "timestamp"])

        for i in range(NUM_BOTS):
            identity = f"aa-bot-{SEED}-{i:05d}"

            # Evaluate the flag — records exposure in Flagsmith experiment 1545
            flag = client.get_experiment_flag(
                feature_name=AA_FEATURE_NAME,
                identifier=identity,
            )
            variant = str(flag.value) if flag and flag.value else "control"

            # Seeded ground-truth: same 40% rate regardless of variant
            converted = rng.random() < GROUND_TRUTH_RATE
            if converted:
                client.track_event(
                    event=AA_METRIC_EVENT,
                    identifier=identity,
                )

            now_iso = datetime.now().isoformat()
            writer.writerow([identity, variant, int(converted), now_iso])

            # Track local stats
            if variant not in variant_stats:
                variant_stats[variant] = {"exposures": 0, "conversions": 0}
            variant_stats[variant]["exposures"] += 1
            if converted:
                variant_stats[variant]["conversions"] += 1

            # Progress
            if (i + 1) % 100 == 0 or (i + 1) == NUM_BOTS:
                elapsed = time.time() - start_time
                rate_per_sec = (i + 1) / elapsed if elapsed > 0 else 0
                print(
                    f"  [{i+1:>4}/{NUM_BOTS}]  "
                    f"{((i+1)/NUM_BOTS)*100:5.1f}%  "
                    f"[{rate_per_sec:.1f} bots/sec]"
                )

            # Batch flush
            if (i + 1) % BATCH_FLUSH == 0:
                client.flush_events()

            if DELAY > 0:
                time.sleep(DELAY)

    # Final flush
    print("\nFlushing remaining events to Flagsmith...")
    client.flush_events()
    print("Waiting 10s for remote event pipeline ingestion...")
    time.sleep(10)

    elapsed_total = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"A/A Test Complete in {elapsed_total:.1f}s ({NUM_BOTS / elapsed_total:.1f} bots/sec)")
    print(f"Output CSV: {output_path.name}")
    print("-" * 70)
    print(f"{'Variant':<20} {'Exposures':<12} {'Conversions':<14} {'Observed Rate':<15}")
    print("-" * 70)
    for v, stats in sorted(variant_stats.items()):
        exp = stats["exposures"]
        conv = stats["conversions"]
        obs = (conv / exp * 100) if exp > 0 else 0.0
        print(f"{v:<20} {exp:<12} {conv:<14} {obs:>6.1f}%")
    print("=" * 70)
    print(
        "\nExpected: both variants near 40% with no confident winner (<70% win prob)."
    )
    print(
        "Trigger refresh: flagsmith api "
        f"\"api/v1/environments/MQSxjKYRor9tQ2DccDBjUA/experiments/{EXPERIMENT_ID}/results/refresh/\" -X POST"
    )


if __name__ == "__main__":
    run_aa_test()
