"""Unit tests for ErrLab message templates."""

from errlab.messages import MESSAGES, SCENARIOS, VARIANTS, get_error_message


def test_all_variants_and_scenarios_configured():
    assert set(VARIANTS) == {"terse", "with_fix", "with_fix_and_link"}
    assert set(SCENARIOS) == {"invalid_config", "missing_api_key", "port_in_use"}
    for variant in VARIANTS:
        assert variant in MESSAGES
        for scenario in SCENARIOS:
            assert scenario in MESSAGES[variant]
            msg = MESSAGES[variant][scenario]
            assert isinstance(msg, str)
            assert len(msg) > 0


def test_message_length_hierarchy():
    """Ensure with_fix and with_fix_and_link add actionable details beyond terse."""
    for scenario in SCENARIOS:
        terse_len = len(MESSAGES["terse"][scenario])
        fix_len = len(MESSAGES["with_fix"][scenario])
        link_len = len(MESSAGES["with_fix_and_link"][scenario])

        assert fix_len > terse_len
        assert link_len > fix_len


def test_link_variant_contains_docs_url():
    for scenario in SCENARIOS:
        msg = MESSAGES["with_fix_and_link"][scenario]
        assert "Docs: https://" in msg


def test_fallback_behavior():
    # Unknown variant falls back to terse
    msg = get_error_message("non_existent_variant", "invalid_config")
    assert msg == MESSAGES["terse"]["invalid_config"]

    # Unknown scenario produces descriptive error
    msg = get_error_message("terse", "unknown_scenario")
    assert "unknown scenario" in msg
