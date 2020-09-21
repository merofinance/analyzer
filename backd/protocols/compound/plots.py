import matplotlib.pyplot as plt

from ... import db
from .entities import CompoundState
from .hooks import NonZeroUsers


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


def output_plot(output: str = None):
    if output is None:
        plt.show()
    else:
        plt.savefig(output)
