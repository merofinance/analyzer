import matplotlib.pyplot as plt

from ... import db
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


def plot_liquidatable_over_time(args: dict):
    state = CompoundState.load(args["state"])
    block_dates = db.get_block_dates()
    users_borrow_supply = state.extra[UsersBorrowSupply.extra_key]

    blocks = [block for block in users_borrow_supply if block in block_dates]
    x = [block_dates[block] for block in blocks]

    users = users_borrow_supply[blocks[-1]]

    thresholds = [1.0, 1.05, 1.1, 1.25, 1.5, 2.0]
    labels = ["{0:.2f}%".format(t) for t in thresholds]

    block_buckets = []
    for block in blocks:
        users = users_borrow_supply[block]
        buckets = [0] * len(thresholds)
        for supply, borrow in users.values():
            ratio = supply / borrow
            for i, value in enumerate(thresholds):
                # only add to first valid bucket
                if ratio < value:
                    buckets[i] += borrow / 10 ** 18
                    break
        block_buckets.append(buckets)

    ys = list(zip(*block_buckets))

    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Collateral in USD")
    plt.stackplot(x, *ys, labels=labels)
    plt.legend()
    plt.tight_layout()
    output_plot(args.get("output"))


def output_plot(output: str = None):
    if output is None:
        plt.show()
    else:
        plt.savefig(output)
