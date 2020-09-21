import argparse
import pickle

from . import executor
from .db import create_indices

parser = argparse.ArgumentParser(
    prog="backd", description="Command-line interface for backd.fund"
)


subparsers = parser.add_subparsers(dest="command")

subparsers.add_parser("create-indices")

process_all_events_parser = subparsers.add_parser("process-all-events")
process_all_events_parser.add_argument(
    "-p", "--protocol", default="compound", help="protocol to use"
)
process_all_events_parser.add_argument(
    "--max-block", type=int, help="block up to which the simulation should run"
)
process_all_events_parser.add_argument("--hooks", nargs="+", help="hooks to execute")
process_all_events_parser.add_argument(
    "-o", "--output", required=True, help="output pickle file"
)


def run_create_indices(_args):
    create_indices()


def run_process_all_events(args):
    state = executor.process_all_events(
        args["protocol"], hooks=args["hooks"], max_block=args["max_block"]
    )
    with open(args["output"], "wb") as f:
        pickle.dump(state, f)


def run():
    args = parser.parse_args()
    if not args.command:
        parser.error("no command given")
    func = globals()["run_" + args.command.replace("-", "_")]
    func(vars(args))
