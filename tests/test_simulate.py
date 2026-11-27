"""Unit tests for ErrLab simulation harness."""

import csv
from pathlib import Path
from simulate import run


def test_model_yaml_integrity():
    model_path = Path(__file__).resolve().parent.parent / "simulate" / "model.yaml"
    model = run.load_model(model_path)

    assert "ground_truth_rates" in model
    rates = model["ground_truth_rates"]
    assert rates["terse"] == 0.35
    assert rates["with_fix"] == 0.48
    assert rates["with_fix_and_link"] == 0.50
    assert model["seed"] == 20261127
    assert model["planned_sample_size"] == 9000


def test_dry_run_simulation(tmp_path):
    csv_out = tmp_path / "test_sim.csv"

    out_file = run.simulate(
        n=60,
        seed=12345,
        dry_run=True,
        delay=0,
        output_path=csv_out,
    )

    assert out_file.exists()

    with open(out_file, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    # Header + 60 bot rows
    assert len(reader) == 61
    assert reader[0] == ["identity", "variant", "scenario", "retry_outcome", "timestamp"]

    # Check identities and outcomes
    identities = [row[0] for row in reader[1:]]
    assert identities[0] == "bot-12345-00000"
    assert identities[-1] == "bot-12345-00059"
    assert len(set(identities)) == 60

    outcomes = set(row[3] for row in reader[1:])
    assert outcomes.issubset({"success", "failure"})
