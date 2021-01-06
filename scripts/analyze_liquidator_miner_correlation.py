from collections import defaultdict
from typing import Any, Counter, Dict

import pandas as pd
from backd.db import db

liquidation_events = list(db.events.find({"event": "LiquidateBorrow"}))

liquidation_events_by_block = defaultdict(list)
for evt in liquidation_events:
    liquidation_events_by_block[evt["blockNumber"]].append(evt)

blocks_condition = {"blockNumber": {"$in": list(liquidation_events_by_block)}}
blocks = {b["blockNumber"]: b for b in db.blocks.find(blocks_condition)}

miners: Dict[str, Dict[str, Any]] = defaultdict(
    lambda: {"liquidators": Counter(), "blocks_count": 0}
)

liquidators = defaultdict(Counter)
for block_number, liquidations in liquidation_events_by_block.items():
    block = blocks[block_number]
    miner_address = block["miner"]
    miner = miners[miner_address]
    for evt in liquidations:
        liquidator = evt["returnValues"]["liquidator"]
        miner["liquidators"][liquidator] += 1
        liquidators[liquidator][miner_address] += 1
    miner["blocks_count"] += 1


def with_top_n(miner, n=5):
    return {**miner, "liquidators": miner["liquidators"].most_common(n)}


def liquidators_stats(miner):
    stats = pd.Series(miner["liquidators"].values()).describe()
    liquidations_count = sum(miner["liquidators"].values())
    sorted_liquidators = sorted(miner["liquidators"].values(), key=lambda x: -x)
    if len(sorted_liquidators) > 1:
        rel_diff_top2 = (sorted_liquidators[0] - sorted_liquidators[1]) / (
            sorted_liquidators[0] + sorted_liquidators[1]
        )
        abs_diff_top2 = (sorted_liquidators[0] - sorted_liquidators[1]) / sum(
            sorted_liquidators
        )
    else:
        abs_diff_top2 = 1
        rel_diff_top2 = 1
    return {
        "blocks_count": miner["blocks_count"],
        "liquidations_count": liquidations_count,
        "rel_diff_top2": round(rel_diff_top2, 3),
        "abs_diff_top2": round(abs_diff_top2, 3),
        "stats": dict(stats),
    }


def analyze_miners(liquidator):
    liquidations_count = sum(liquidator.values())
    ratios = []
    for _, value in liquidator.most_common():
        ratios.append(round(value / liquidations_count, 4))
        if sum(ratios) >= 0.9:
            break
    return {"liquidations_count": liquidations_count, "ratios": ratios}


def show_liquidations(miner):
    return sorted(
        [
            (evt["blockNumber"], evt["returnValues"]["liquidator"])
            for evt in liquidation_events
            if blocks[evt["blockNumber"]]["miner"] == miner
        ],
        key=lambda x: x[0],
    )


stats = {k: liquidators_stats(v) for k, v in miners.items()}
top_miners = [
    (k, v) for k, v in sorted(stats.items(), key=lambda x: -x[1]["blocks_count"])
][:10]


n = 5


def multirow(string, n=n):
    return r"\multirow{" + str(n) + "}{*}{" + string + "}"


for address, miner in sorted(miners.items(), key=lambda x: -x[1]["blocks_count"])[:10]:
    print(
        multirow(f"\\contractaddr{{{address}}}"),
        "&",
        multirow(f"{miner['blocks_count']:n}"),
        end=" & ",
    )
    prefix = ""
    for liquidator_address, liquidations_count in miner["liquidators"].most_common(n):
        print(
            f"{prefix}\\contractaddr{{{liquidator_address}}} & {liquidations_count:3}\\\\"
        )
        prefix = len(liquidator_address) * " " + " & " + " " * 5 + " & "
    print(r"\hline")
