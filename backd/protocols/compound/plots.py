import matplotlib.pyplot as plt

from ... import constants, db
from ...plot_utils import DEFAULT_PALETTE
from .entities import CompoundState
from .hooks import NonZeroUsers, UsersBorrowSupply


def plot_borrowers_over_time(args: dict):
    state = CompoundState.load(args["state"])
    block_dates = db.get_block_dates()
    users_count = state.extra[NonZeroUsers.extra_key].historical_count
    non_zero_users = [
        (block, count)
        for block, count in users_count.items()
        if count > 0 and block in block_dates
    ]
    interval = int(args["options"].get("interval", 1))
    x = [block_dates[v[0]] for v in non_zero_users[::interval]]
    y = [v[1] for v in non_zero_users[::interval]]
    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Number of borrowers")
    plt.plot_date(x, y, fmt="-")
    plt.tight_layout()
    output_plot(args.get("output"))


def plot_supply_borrow_over_time(args: dict):
    state = CompoundState.load(args["state"])
    block_dates = db.get_block_dates()
    users_borrow_supply = state.extra[UsersBorrowSupply.extra_key]

    blocks = [block for block in users_borrow_supply if block in block_dates]
    x = [block_dates[block] for block in blocks]

    if args["options"] and "thresholds" in args["options"]:
        thresholds = [float(v) for v in args["options"]["thresholds"].split(",")]
    else:
        thresholds = [1.0, 1.05, 1.1, 1.25, 1.5, 2.0]
    labels = ["< {0:.2f}%".format(t * 100) for t in thresholds]
    labels.append(">= {0:.2f}%".format(thresholds[-1] * 100))

    block_buckets = []
    total_borrows = []
    for block in blocks:
        users = users_borrow_supply[block]
        buckets = [0] * (len(thresholds) + 1)
        total = 0
        for supply, borrow in users.values():
            normalized_borrow = borrow / constants.DEFAULT_DECIMALS
            total += normalized_borrow
            ratio = supply / borrow
            for i, value in enumerate(thresholds):
                # only add to first valid bucket
                if ratio < value:
                    buckets[i] += normalized_borrow
                    break
            else:
                buckets[-1] += normalized_borrow
        total_borrows.append(total)
        block_buckets.append(buckets)

    ys = list(zip(*block_buckets))

    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Collateral in USD")
    plt.plot_date(x, total_borrows, fmt="-")
    plt.stackplot(x, *ys, labels=labels, colors=DEFAULT_PALETTE)
    plt.legend(title="Supply/borrow ratio", loc="upper left")
    plt.tight_layout()
    output_plot(args.get("output"))


def output_plot(output: str = None):
    if output is None:
        plt.show()
    else:
        plt.savefig(output)
