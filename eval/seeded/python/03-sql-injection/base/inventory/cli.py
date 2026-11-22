"""Command line entry point: python -m inventory.cli DB COMMAND ..."""

import argparse
import sys

from inventory import db


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inventory")
    parser.add_argument("database")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("name")
    add.add_argument("qty", type=int)
    sub.add_parser("list")
    args = parser.parse_args(argv)

    conn = db.connect(args.database)
    if args.command == "add":
        db.add_item(conn, args.name, args.qty)
    elif args.command == "list":
        for name, qty in db.list_items(conn):
            print(f"{name}\t{qty}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
