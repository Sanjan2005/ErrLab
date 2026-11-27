"""ErrLab Seeded Bot Simulation Harness.

Simulates N unique bot users navigating the ErrLab CLI deployment workflow:
1. Each bot receives a deterministic unique identity (`bot-{seed}-{index:05d}`).
2. Triggers an error via `core.attempt_deploy(identity, scenario)`.
   Flagsmith evaluates the multivariate flag and records the exposure event.
3. Bot determines retry recovery outcome based on the pre-registered ground-truth
   rates in `simulate/model.yaml`.
4. If retry succeeds, records the `retry_succeeded` conversion event via Flagsmith SDK.
5. All runs log to a raw CSV in `results/raw/` for auditing and cross-checking.
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict

import yaml

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from errlab import core, flags, messages


def load_model(model_path: Path) -> Dict[str, Any]:
    with open(model_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def simulate(
    n: int = 300,
    seed: int = 20261127,
    dry_run: bool = False,
    delay: float = 0.02,
    batch_flush: int = 100,
    output_path: Path | None = None,
    model_path: Path | None = None,
) -> Path:
    if model_path is None:
        model_path = PROJECT_ROOT / "simulate" / "model.yaml"

    model = load_model(model_path)
    rates: Dict[str, float] = model["ground_truth_rates"]
    scenarios = model.get("scenarios", list(messages.SCENARIOS))

    rng = random.Random(seed)

    if not dry_run:
        flags.init()

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = PROJECT_ROOT / "results" / "raw"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"simulation_{timestamp}.csv"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    mode_str = "[DRY RUN - No Flagsmith calls]" if dry_run else "[LIVE - Remote Flagsmith SDK]"
    print("=" * 70)
    print(f"ErrLab Bot Simulation {mode_str}")
    print(f"Total Bots (N): {n} | Seed: {seed} | Delay: {delay}s | Flush Interval: {batch_flush}")
    print(f"Target Output:  {output_path.name}")
    print("=" * 70)

    variant_stats: Dict[str, Dict[str, int]] = {
        v: {"exposures": 0, "conversions": 0}
        for v in messages.VARIANTS
    }

    start_time = time.time()

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["identity", "variant", "scenario", "retry_outcome", "timestamp"])

        for i in range(n):
            identity = f"bot-{seed}-{i:05d}"
            scenario = rng.choice(scenarios)

            if dry_run:
                # Simulate deterministic 33/33/33 traffic split for dry runs
                variant = ("terse", "with_fix", "with_fix_and_link")[i % 3]
            else:
                # Real deployment attempt: Flagsmith evaluates flag & records exposure
                result = core.attempt_deploy(identity, scenario)
                variant = result["variant"]

            # Ground-truth decision model: does this bot recover on first retry?
            recovery_rate = rates.get(variant, 0.35)
            succeeded = rng.random() < recovery_rate
            outcome = "success" if succeeded else "failure"

            if succeeded and not dry_run:
                flags.record_conversion(identity)

            now_iso = datetime.now().isoformat()
            writer.writerow([identity, variant, scenario, outcome, now_iso])

            # Update stats
            if variant not in variant_stats:
                variant_stats[variant] = {"exposures": 0, "conversions": 0}
            variant_stats[variant]["exposures"] += 1
            if succeeded:
                variant_stats[variant]["conversions"] += 1

            # Progress output
            if (i + 1) % 50 == 0 or (i + 1) == n:
                elapsed = time.time() - start_time
                rate_per_sec = (i + 1) / elapsed if elapsed > 0 else 0
                print(f"  Processed {i + 1:>5}/{n} bots ({((i+1)/n)*100:>5.1f}%) [{rate_per_sec:.1f} bots/sec]")

            # Periodic batch flushing to avoid huge in-memory buffer
            if not dry_run and (i + 1) % batch_flush == 0:
                flags.flush()

            if delay > 0 and not dry_run:
                time.sleep(delay)

    # Final event flush
    if not dry_run:
        print("\nFlushing remaining events to Flagsmith...")
        flags.flush()
        print("Waiting 5s for remote ingestion pipeline...")
        time.sleep(5)

    elapsed_total = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"Simulation Complete in {elapsed_total:.1f}s ({n / elapsed_total:.1f} bots/sec)")
    print(f"Saved to: {output_path}")
    print("-" * 70)
    print(f"{'Variant':<20} {'Exposures':<12} {'Conversions':<14} {'Conversion Rate':<15} {'Expected':<10}")
    print("-" * 70)

    for v in messages.VARIANTS:
        exp = variant_stats[v]["exposures"]
        conv = variant_stats[v]["conversions"]
        rate_pct = (conv / exp * 100) if exp > 0 else 0.0
        exp_pct = rates.get(v, 0.0) * 100
        print(f"{v:<20} {exp:<12} {conv:<14} {rate_pct:>6.1f}%          ({exp_pct:.0f}%)")

    print("=" * 70)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ErrLab seeded simulation harness for Flagsmith A/B experiment."
    )
    parser.add_argument(
        "--n", type=int, default=300, help="Number of bot users to simulate (default: 300)"
    )
    parser.add_argument(
        "--seed", type=int, default=20261127, help="Random seed for bot behavior (default: 20261127)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate locally without making Flagsmith network calls"
    )
    parser.add_argument(
        "--delay", type=float, default=0.02, help="Delay in seconds between bot iterations (default: 0.02)"
    )
    parser.add_argument(
        "--batch-flush", type=int, default=100, help="Flush event buffer every K iterations (default: 100)"
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Custom output CSV file path"
    )

    args = parser.parse_args()
    out = Path(args.output) if args.output else None
    simulate(
        n=args.n,
        seed=args.seed,
        dry_run=args.dry_run,
        delay=args.delay,
        batch_flush=args.batch_flush,
        output_path=out,
    )


if __name__ == "__main__":
    main()
