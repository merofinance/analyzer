import argparse
import pickle

from . import executor
from .db import create_indices
from .protocol import Protocol

parser = argparse.ArgumentParser(
    prog="backd", description="Command-line interface for backd.fund"
)


def add_protocol_choice(subparser):
    subparser.add_argument(
        "-p",
        "--protocol",
        default="compound",
        help="protocol to use",
        choices=Protocol.registered(),
    )


subparsers = parser.add_subparsers(dest="command")

subparsers.add_parser("create-indices")

process_all_events_parser = subparsers.add_parser("process-all-events")
add_protocol_choice(process_all_events_parser)
process_all_events_parser.add_argument(
    "--max-block", type=int, help="block up to which the simulation should run"
)
process_all_events_parser.add_argument("--hooks", nargs="+", help="hooks to execute")
process_all_events_parser.add_argument(
    "-o", "--output", required=True, help="output pickle file"
)


plot_parser = subparsers.add_parser("plot")
add_protocol_choice(plot_parser)
plot_parser.add_argument("type", help="type of plot")
plot_parser.add_argument("-s", "--state", required=True, help="state pickle file")
plot_parser.add_argument("-o", "--output", help="plot output file")


def run_create_indices(_args):
    create_indices()


def run_process_all_events(args):
    state = executor.process_all_events(
        args["protocol"], hooks=args["hooks"], max_block=args["max_block"]
    )
    with open(args["output"], "wb") as f:
        pickle.dump(state, f)


def run_plot(args):
    protocol = Protocol.get(args["protocol"])()
    plots = protocol.get_plots()
    func_name = "plot_{0}".format(args["type"].replace("-", "_"))
    func = getattr(plots, func_name, None)
    if not func:
        plot_parser.error(
            "unknown plot {0} for protocol {1}".format(args["type"], args["protocol"])
        )
    func(args)


def run():
    args = parser.parse_args()
    if not args.command:
        parser.error("no command given")
    func = globals()["run_" + args.command.replace("-", "_")]
    func(vars(args))
