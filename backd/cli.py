import argparse
import pickle

from . import executor
from .db import create_indices
from .protocol import Protocol


class ParseKwargs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, {})
        for value in values:
            key, value = value.split("=")
            getattr(namespace, self.dest)[key] = value


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


def add_state_arg(subparser):
    subparser.add_argument("-s", "--state", required=True, help="state pickle file")


def add_output_arg(subparser, required=False):
    subparser.add_argument("-o", "--output", required=required, help="output file")


plot_parser = subparsers.add_parser("plot")
add_protocol_choice(plot_parser)
plot_subparsers = plot_parser.add_subparsers(dest="subcommand")

plot_supbow_num_time_parser = plot_subparsers.add_parser(
    "suppliers-borrowers-over-time",
    help="plots suppliers and borrowers over time",
)
add_state_arg(plot_supbow_num_time_parser)
add_output_arg(plot_supbow_num_time_parser)
plot_supbow_num_time_parser.add_argument(
    "-i", "--interval", default=100, type=int, help="interval between blocks"
)

plot_supbow_time_parser = plot_subparsers.add_parser(
    "supply-borrow-over-time",
    help="plots supply and borrows over time",
)
add_state_arg(plot_supbow_time_parser)
add_output_arg(plot_supbow_time_parser)
plot_supbow_time_parser.add_argument(
    "--resample", default="1d", help="period to use for resampling"
)

plot_liquidable_over_time_parser = plot_subparsers.add_parser(
    "liquidable-over-time", help="plots liquidable positions over time"
)
add_output_arg(plot_liquidable_over_time_parser)
plot_liquidable_over_time_parser.add_argument("files", nargs="+", help="files to plot")
plot_liquidable_over_time_parser.add_argument(
    "-s", "--styles", nargs="*", help="plot styles", default=["o", "x", "v", "^"]
)
plot_liquidable_over_time_parser.add_argument(
    "-l", "--labels", nargs="*", help="plot labels"
)
plot_liquidable_over_time_parser.add_argument(
    "--resample", default="1d", help="period to use for resampling"
)

plot_supbow_ratios_time_parser = plot_subparsers.add_parser(
    "supply-borrow-ratios-over-time",
    help="plots supply and borrow ratios over time",
)
add_state_arg(plot_supbow_ratios_time_parser)
add_output_arg(plot_supbow_ratios_time_parser)
plot_supbow_ratios_time_parser.add_argument(
    "-t",
    "--thresholds",
    nargs="*",
    default=[1.0, 1.05, 1.1, 1.25, 1.5, 2.0],
    type=float,
    help="thresholds to use for plotting",
)

plot_liquidations_time_parser = plot_subparsers.add_parser(
    "liquidations-over-time",
    help="plots liquidations over time",
)
add_state_arg(plot_liquidations_time_parser)
add_output_arg(plot_liquidations_time_parser)

plot_supply_borrow_distribution_parser = plot_subparsers.add_parser(
    "supply-borrow-distribution",
    help="plots supply/borrow distribution",
)
add_state_arg(plot_supply_borrow_distribution_parser)
add_output_arg(plot_supply_borrow_distribution_parser)
plot_supply_borrow_distribution_parser.add_argument(
    "-p",
    "--property",
    default="supply",
    help="property to plot",
    choices=["supply", "borrow"],
)
plot_supply_borrow_distribution_parser.add_argument(
    "-t",
    "--threshold",
    type=int,
    default=100,
    help="minimum amount of USD to be considered",
)
plot_supply_borrow_distribution_parser.add_argument(
    "-b", "--bucket-size", type=int, default=10, help="number of users per bucket"
)
plot_supply_borrow_distribution_parser.add_argument(
    "-i", "--interval", default=50, type=int, help="interval between ticks"
)

plot_time_to_liquidation_parser = plot_subparsers.add_parser(
    "time-to-liquidation",
    help="plots time to liquidation",
)
add_state_arg(plot_time_to_liquidation_parser)
add_output_arg(plot_time_to_liquidation_parser)
plot_supply_borrow_distribution_parser.add_argument(
    "-m", "--max-blocks", default=17, type=int, help="maximum number of blocks to plot"
)

plot_top_suppliers_and_borrowers_parser = plot_subparsers.add_parser(
    "top-suppliers-and-borrowers",
    help="creates table with top suppliers and borrowers",
)
add_state_arg(plot_top_suppliers_and_borrowers_parser)
plot_top_suppliers_and_borrowers_parser.add_argument(
    "-n",
    "--top-n",
    help="Number of suppliers and borrowers to plot",
    type=int,
    default=10,
)


export_parser = subparsers.add_parser("export")
add_protocol_choice(export_parser)
export_subparsers = export_parser.add_subparsers(dest="subcommand")
export_borsup_time_parser = export_subparsers.add_parser("borrow-supply-over-time")
export_borsup_time_parser.add_argument(
    "-s", "--state", required=True, help="state pickle file"
)
add_output_arg(export_borsup_time_parser, required=True)
export_borsup_time_parser.add_argument("-t", "--threshold", default=10_000, type=int)


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
    if not args["subcommand"]:
        plot_parser.error("no subcommand provided")
    func_name = "plot_{0}".format(args["subcommand"].replace("-", "_"))
    func = getattr(plots, func_name, None)
    if not func:
        plot_parser.error(
            "unknown plot {0} for protocol {1}".format(args["type"], args["protocol"])
        )
    func(args)


def run_export(args):
    protocol: Protocol = Protocol.get(args["protocol"])()
    exporter = protocol.get_exporter()
    if not args["subcommand"]:
        export_parser.error("no subcommand provided")
    func_name = "export_{0}".format(args["subcommand"].replace("-", "_"))
    func = getattr(exporter, func_name)
    func(args)


def run():
    args = parser.parse_args()
    if not args.command:
        parser.error("no command given")
    func = globals()["run_" + args.command.replace("-", "_")]
    func(vars(args))
