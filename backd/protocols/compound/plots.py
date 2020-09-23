import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler
from matplotlib.ticker import FuncFormatter

from ... import constants, db
from ...plot_utils import COLORS, DEFAULT_PALETTE
from .entities import CompoundState
from .hooks import Borrowers, LiquidationAmounts, Suppliers, UsersBorrowSupply

INT_FORMATTER = FuncFormatter(lambda x, _: "{:,}".format(int(x)))
LARGE_MONETARY_FORMATTER = FuncFormatter(lambda x, _: "{:,}M".format(x // 1e6))

mpl.rcParams["axes.prop_cycle"] = cycler(color=DEFAULT_PALETTE)


def get_option(args: dict, key: str, transform=lambda x: x, default=None):
    if args.get("options") and key in args["options"]:
        return transform(args["options"][key])
    return default


def plot_suppliers_and_borrowers_over_time(args: dict):
    state = CompoundState.load(args["state"])
    block_dates = db.get_block_dates()

    def get_users(history):
        return [
            (block, count)
            for block, count in history.items()
            if count > 0 and block in block_dates
        ]

    def get_xy(users, interval):
        x = [block_dates[v[0]] for v in users[::interval]]
        y = [v[1] for v in users[::interval]]
        return x, y

    suppliers = get_users(state.extra[Suppliers.extra_key].historical_count)
    borrowers = get_users(state.extra[Borrowers.extra_key].historical_count)
    interval = get_option(args, "interval", transform=int, default=100)

    x1, y1 = get_xy(suppliers, interval)
    x2, y2 = get_xy(borrowers, interval)

    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Number of accounts")
    plt.plot(x1, y1, "-", label="Suppliers")
    plt.plot(x2, y2, "-", label="Borrowers")
    ax = plt.gca()
    ax.yaxis.set_major_formatter(INT_FORMATTER)
    plt.tight_layout()
    plt.legend(loc="upper left")

    output_plot(args.get("output"))


def plot_supply_borrow_over_time(args: dict):
    state = CompoundState.load(args["state"])
    supply_borrows = state.extra["supply-borrow"].set_index("timestamp")

    sampling_period = get_option(args, "period", default="1h")
    key_mapping = {
        "borrows": "Total borrowed",
        "supply": "Total supply",
        "underlying": "Total locked",
    }
    for key, new_key in key_mapping.items():
        supply_borrows[new_key] = supply_borrows[key] / 1e18

    # TODO: check this is actually doing mean per market
    # within a time bin and then summing all the means
    means = (
        supply_borrows.groupby("market").resample(sampling_period).mean().sum(level=1)
    )
    ax = means[list(key_mapping.values())].plot()
    ax.yaxis.set_major_formatter(LARGE_MONETARY_FORMATTER)
    ax.set_ylabel("Amount (USD)")
    ax.set_xlabel("Date")
    plt.tight_layout()
    output_plot(args.get("output"))


def plot_supply_borrow_ratios_over_time(args: dict):
    state = CompoundState.load(args["state"])
    block_dates = db.get_block_dates()
    users_borrow_supply = state.extra[UsersBorrowSupply.extra_key]

    blocks = [block for block in users_borrow_supply if block in block_dates]
    x = [block_dates[block] for block in blocks]

    thresholds = get_option(
        args,
        "thresholds",
        transform=lambda x: [float(v) for v in x.split(",")],
        default=[1.0, 1.05, 1.1, 1.25, 1.5, 2.0],
    )
    labels = ["< {0:.2f}%".format(t * 100) for t in thresholds]
    labels.append("$\\geq$ {0:.2f}%".format(thresholds[-1] * 100))

    block_buckets = []
    total_supplies = []
    for block in blocks:
        users = users_borrow_supply[block]
        buckets = [0] * (len(thresholds) + 1)
        total = 0
        for supply, borrow in users.values():
            normalized_supply = supply / constants.DEFAULT_DECIMALS
            total += normalized_supply
            if borrow == 0:
                ratio = 1000
            else:
                ratio = supply / borrow
            for i, value in enumerate(thresholds):
                # only add to first valid bucket
                if ratio < value:
                    buckets[i] += normalized_supply
                    break
            else:
                buckets[-1] += normalized_supply
        total_supplies.append(total)
        block_buckets.append(buckets)

    ys = list(zip(*block_buckets))

    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Collateral in USD")
    # plt.plot_date(x, total_supplies, fmt="-")
    plt.stackplot(x, *ys, labels=labels, colors=DEFAULT_PALETTE)
    ax = plt.gca()
    ax.yaxis.set_major_formatter(LARGE_MONETARY_FORMATTER)
    plt.legend(title="Supply/borrow ratio", loc="upper left")
    plt.tight_layout()
    output_plot(args.get("output"))


def plot_liquidations_over_time(args: dict):
    state = CompoundState.load(args["state"])
    liquidation_info = state.extra[LiquidationAmounts.extra_key]
    group_key = liquidation_info.timestamp.dt.floor("d")

    counts = liquidation_info.groupby(group_key).size()
    amounts = liquidation_info.groupby(group_key).usd_seized.sum() / 1e18

    ax = plt.gca()
    l1 = ax.plot_date(counts.index, counts.values, fmt="--", color=DEFAULT_PALETTE[0])
    plt.xticks(rotation=45)
    ax.set_ylabel("Number of liquidations")
    ax.set_xlabel("Date")
    ax2 = ax.twinx()
    l2 = ax2.plot_date(amounts.index, amounts.values, fmt="-", color=DEFAULT_PALETTE[1])
    ax2.set_ylabel("Amount liquidated (USD)")
    ax2.yaxis.set_major_formatter(LARGE_MONETARY_FORMATTER)
    ax.legend(l1 + l2, ["Count", "Amount"], loc="upper left")
    plt.tight_layout()
    output_plot(args.get("output"))


def plot_supply_borrow_distribution(args: dict):
    state = CompoundState.load(args["state"])
    users = state.compute_unique_users()
    prop = get_option(args, "property", default="supply")

    values = []
    threshold = get_option(args, "threshold", transform=int, default=100)
    for user in users:
        total_supply, total_borrow = state.compute_user_position(user)
        value = total_supply if prop == "supply" else total_borrow
        if value > threshold * 10 ** 18:
            values.append(value / 1e18)

    bucket_size = get_option(args, "bucket_size", transform=int, default=10)
    total = sum(values)
    values = sorted(values)
    padding = [0] * (bucket_size - len(values) % bucket_size)
    values = np.array(padding + values)
    values = np.sum(values.reshape(-1, bucket_size), axis=1)
    cum_values = [sum(values[:i]) for i in range(0, len(values) + 1)]

    heights = [v / total for v in cum_values]
    x = np.arange(len(heights))
    ax1 = plt.gca()
    ax1.bar(x, heights, width=1.0, color=COLORS["gray"])

    ax1.set_yticks(list(ax1.get_yticks())[:-1])
    ax1.set_yticklabels(["{0:,}".format(int(total * v)) for v in ax1.get_yticks()])
    ax1.set_ylabel("Amount of USD")

    ax1.set_xlabel("Number of users")
    ax1.tick_params(axis="x", rotation=45)

    interval = get_option(args, "interval", transform=int, default=50)
    ticks = np.append(x[::interval][:-1], x[-1])
    ax2 = ax1.twinx()
    ax2.bar(x, heights, width=1.0, color=COLORS["gray"])

    ax2.set_yticks(list(ax2.get_yticks())[:-1])  # use FixedLocator
    ax2.set_yticklabels(["{0}%".format(int(v * 100)) for v in ax2.get_yticks()])
    ax2.set_ylabel("Percentage of USD")

    ax2.set_xticks(ticks)
    ax2.set_xticklabels(ticks * bucket_size)

    plt.tight_layout()

    output_plot(args["output"])


def output_plot(output: str = None):
    if output is None:
        plt.show()
    else:
        plt.savefig(output)
