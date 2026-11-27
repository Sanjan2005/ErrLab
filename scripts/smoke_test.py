"""Phase 3: Pipeline smoke test for ErrLab.

Runs 20 unique identities through attempt_deploy, with roughly half retrying
successfully to send conversion events. Flushes events and prints verification
summary.
"""

import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from errlab import core, flags, messages


def run_smoke_test():
    flags.init()
    scenarios = list(messages.SCENARIOS)

    print("=" * 65)
    print("Starting ErrLab Pipeline Smoke Test (20 identities)...")
    print("=" * 65)

    variant_counts = {"terse": 0, "with_fix": 0, "with_fix_and_link": 0}
    conversion_counts = {"terse": 0, "with_fix": 0, "with_fix_and_link": 0}

    for i in range(20):
        identity = f"smoke-user-{i:03d}"
        scenario = scenarios[i % len(scenarios)]

        # 1. Attempt deploy (records exposure via get_experiment_flag)
        result = core.attempt_deploy(identity, scenario)
        variant = result["variant"]
        variant_counts[variant] = variant_counts.get(variant, 0) + 1

        # 2. Simulate 50% retry conversion rate (even indices retry successfully)
        will_retry = (i % 2 == 0)
        status_suffix = ""
        if will_retry:
            flags.record_conversion(identity)
            conversion_counts[variant] = conversion_counts.get(variant, 0) + 1
            status_suffix = " -> Retry converted!"

        print(
            f"[{i+1:02d}/20] {identity} | scenario={scenario:<16} | variant={variant:<18}{status_suffix}"
        )
        time.sleep(0.1)

    print("\nFlushing events to Flagsmith...")
    flags.flush()
    print("Waiting 10 seconds for remote event pipeline ingestion...")
    time.sleep(10)

    print("\n" + "=" * 65)
    print("Local Smoke Test Summary:")
    print("Total identities tested: 20")
    for v in ("terse", "with_fix", "with_fix_and_link"):
        exposures = variant_counts.get(v, 0)
        convs = conversion_counts.get(v, 0)
        rate = (convs / exposures * 100) if exposures else 0.0
        print(
            f"  Variant '{v:<18}': {exposures:2d} exposures, {convs:2d} conversions ({rate:.1f}%)"
        )
    print("=" * 65)
    print("Pipeline smoke test completed successfully.")
    print("Trigger refresh via Flagsmith API to inspect live warehouse numbers.")



if __name__ == "__main__":
    run_smoke_test()
