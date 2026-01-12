"""
Data Router CLI Entry Point
Created: 2024-12-25 (P7.3)
Modularized: 2026-01-02 (RULE-032)

Usage:
    python -m governance.router rule --id RULE-023 --name "New Rule"
    python -m governance.router decision --id DECISION-005 --name "Decision"
    python -m governance.router session --id SESSION-2024-12-25-PHASE9
"""
import argparse
import json

from governance.router import create_data_router


def main():
    """CLI for data router."""
    parser = argparse.ArgumentParser(description="Data Router")
    parser.add_argument("type", choices=["rule", "decision", "session"])
    parser.add_argument("--id", required=True, help="Item ID")
    parser.add_argument("--name", help="Item name")
    parser.add_argument("--content", help="Content/directive")
    parser.add_argument("--dry-run", "-n", action="store_true")
    args = parser.parse_args()

    router = create_data_router(dry_run=args.dry_run)

    if args.type == "rule":
        result = router.route_rule(
            rule_id=args.id,
            name=args.name or "Unnamed Rule",
            directive=args.content or ""
        )
    elif args.type == "decision":
        result = router.route_decision(
            decision_id=args.id,
            name=args.name or "Unnamed Decision",
            context=args.content or ""
        )
    else:
        result = router.route_session(
            session_id=args.id,
            content=args.content or ""
        )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
