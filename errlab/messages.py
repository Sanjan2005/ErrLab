"""Static error message templates for ErrLab variants and scenarios.

Pure data module with no external dependencies or side effects.
"""

from typing import Dict

SCENARIOS = ("invalid_config", "missing_api_key", "port_in_use")
VARIANTS = ("terse", "with_fix", "with_fix_and_link")

MESSAGES: Dict[str, Dict[str, str]] = {
    "terse": {
        "invalid_config": "Error: invalid configuration.",
        "missing_api_key": "Error: API key not found.",
        "port_in_use": "Error: port already in use.",
    },
    "with_fix": {
        "invalid_config": (
            "Error: invalid configuration.\n"
            "Fix: Check that config.yaml exists and contains a valid 'deploy.target' field."
        ),
        "missing_api_key": (
            "Error: API key not found.\n"
            "Fix: Run 'errlab config set-key <KEY>' or set the DEPLOY_API_KEY environment variable."
        ),
        "port_in_use": (
            "Error: port 8080 already in use.\n"
            "Fix: Identify conflicting process on port 8080 ('lsof -i :8080' or 'netstat -ano | findstr :8080') and terminate it."
        ),
    },
    "with_fix_and_link": {
        "invalid_config": (
            "Error: invalid configuration.\n"
            "Fix: Check that config.yaml exists and contains a valid 'deploy.target' field.\n"
            "Docs: https://errlab.dev/docs/config-schema"
        ),
        "missing_api_key": (
            "Error: API key not found.\n"
            "Fix: Run 'errlab config set-key <KEY>' or set the DEPLOY_API_KEY environment variable.\n"
            "Docs: https://errlab.dev/docs/authentication"
        ),
        "port_in_use": (
            "Error: port 8080 already in use.\n"
            "Fix: Identify conflicting process on port 8080 ('lsof -i :8080' or 'netstat -ano | findstr :8080') and terminate it.\n"
            "Docs: https://errlab.dev/docs/port-conflicts"
        ),
    },
}


def get_error_message(variant: str, scenario: str) -> str:
    """Retrieve the error message string for a given variant and scenario.

    Falls back to 'terse' if variant is unknown, and returns a generic error
    if scenario is unrecognized.
    """
    variant_messages = MESSAGES.get(variant, MESSAGES["terse"])
    if scenario not in variant_messages:
        return f"Error: unknown scenario '{scenario}'."
    return variant_messages[scenario]
