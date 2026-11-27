"""Command-line interface entry point for ErrLab.

Provides:
  errlab deploy [--scenario <invalid_config|missing_api_key|port_in_use>]
  errlab retry
  errlab identity [--reset]
"""

import argparse
import sys

from errlab import core, flags, identity, messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="errlab",
        description="ErrLab: CLI A/B test demo for Flagsmith Toggle Wars Track 01",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # `errlab deploy`
    deploy_parser = subparsers.add_parser(
        "deploy", help="Simulate a deployment attempt (triggers flag-driven error)"
    )
    deploy_parser.add_argument(
        "--scenario",
        choices=messages.SCENARIOS,
        default="invalid_config",
        help="Error scenario to simulate (default: invalid_config)",
    )

    # `errlab retry`
    subparsers.add_parser(
        "retry", help="Retry deployment after error (records conversion if successful)"
    )

    # `errlab identity`
    id_parser = subparsers.add_parser(
        "identity", help="Inspect or reset current anonymous user identity"
    )
    id_parser.add_argument(
        "--reset",
        action="store_true",
        help="Generate a fresh anonymous identity",
    )

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "identity":
        if args.reset:
            new_id = identity.reset_identity()
            print(f"Identity reset. New identity: {new_id}")
        else:
            current_id = identity.get_or_create_identity()
            print(f"Current identity: {current_id}")
        return 0

    # For deploy and retry, initialize Flagsmith client
    try:
        flags.init()
    except Exception as e:
        sys.stderr.write(f"Flagsmith configuration error: {e}\n")
        return 2

    user_id = identity.get_or_create_identity()

    if args.command == "deploy":
        result = core.attempt_deploy(user_id, scenario=args.scenario)
        flags.flush()
        sys.stderr.write(f"{result['error_message']}\n")
        return 1

    if args.command == "retry":
        result = core.attempt_retry(user_id)
        if result["success"]:
            print(result["message"])
            return 0
        else:
            sys.stderr.write(f"{result['message']}\n")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
