import argparse

from .db import create_indices

parser = argparse.ArgumentParser(
    prog="backd",
    description="Command-line interface for backd.fund")


subparsers = parser.add_subparsers(dest="command")

subparsers.add_parser("create-indices")


def run_create_indices(_args):
    create_indices()


def run():
    args = parser.parse_args()
    if not args.command:
        parser.error("no command given")
    func = globals()["run_" + args.command.replace("-", "_")]
    func(vars(args))
