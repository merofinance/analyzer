import pandas as pd
from .entities import CompoundState
from ... import db
from . import constants
from .hooks import UsersBorrowSupply


def export_borrow_supply_over_time(args: dict):
    block_dates = db.get_block_dates()
    state = CompoundState.load(args["state"])
    users_borrow_supply = state.extra[UsersBorrowSupply.extra_key]

    blocks = [block for block in users_borrow_supply if block in block_dates]
    threshold = args["threshold"]
    liquidable = []

    for block in blocks:
        block_total = 0
        users = users_borrow_supply[block]
        for supply, borrow in users.values():
            if borrow > 0 and supply / borrow < 1:
                block_total += supply / constants.DEFAULT_DECIMALS
        if block_total > threshold:
            liquidable.append(
                {
                    "block": block,
                    "timestamp": block_dates[block],
                    "value": block_total,
                }
            )
    df = pd.DataFrame(liquidable).set_index("timestamp")
    df.to_csv(args["output"])
