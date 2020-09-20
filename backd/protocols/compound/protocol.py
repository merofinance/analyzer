from typing import Iterable
from functools import lru_cache

from ...event_processor import Processor
from ...hook import Hooks
from ...entities import PointInTime
from ...db import db, SORT_KEY
from ...protocol import Protocol
from ... import utils
from .entities import CompoundState
from .processor import CompoundProcessor
from . import oracles  # pylint: disable=unused-import
from .constants import DS_VALUES_MAPPING, DSR_ADDRESS


@Protocol.register("compound")
class CompoundProtocol(Protocol):
    def create_processor(self, hooks: Hooks = None) -> Processor:
        return CompoundProcessor(hooks=hooks)

    def create_empty_state(self) -> CompoundState:
        return CompoundState.create()

    def count_events(self, min_block: int = None, max_block: int = None) -> int:
        condition = self.make_block_range_condition(min_block, max_block)
        collections = [db.events, db.ds_values, db.chi_values]
        sai_events_count = len(list(self.sai_price_events(min_block, max_block)))
        db_events_count = sum(col.count_documents(condition) for col in collections)
        return sai_events_count + db_events_count

    def iterate_events(
        self, min_block: int = None, max_block: int = None
    ) -> Iterable[dict]:
        condition = self.make_block_range_condition(min_block, max_block)
        return utils.merge_sorted_streams(
            db.events.find(condition).sort(SORT_KEY),
            self.fetch_ds_values(condition),
            self.fetch_chi_values(condition),
            self.sai_price_events(min_block=min_block, max_block=max_block),
            key=PointInTime.from_event,
        )

    def sai_price_events(self, min_block: int = None, max_block: int = None):
        events = [
            {
                "address": "0xddc46a3b076aec7ab3fc37420a8edd2959764ec4",
                "block": 10_067_346,
                "sai_price": 5285551943761727,
            }
        ]

        for event in events:
            if (
                (min_block is not None and event["block"] < min_block)
                or max_block is not None
                and event["block"] > max_block
            ):
                continue
            yield {
                "event": "SaiPriceSet",
                "address": event["address"],
                "returnValues": {"newPriceMantissa": str(event["sai_price"])},
                "blockNumber": event["block"],
                "transactionIndex": -1,
                "logIndex": -2,
            }

    def fetch_ds_values(self, condition: dict) -> Iterable[dict]:
        for row in db.ds_values.find(condition).sort("blockNumber"):
            yield {
                "event": "InvertedPricePosted",
                "address": row["address"],
                "returnValues": {
                    "newPriceMantissa": str(row["price"]),
                    "tokens": DS_VALUES_MAPPING.get(row["address"].lower(), []),
                },
                "blockNumber": row["blockNumber"],
                "transactionIndex": -1,
                "logIndex": -1,
            }

    def fetch_chi_values(self, condition: dict) -> Iterable[dict]:
        for row in db.chi_values.find(condition).sort("blockNumber"):
            yield {
                "event": "ChiUpdated",
                "address": DSR_ADDRESS,
                "returnValues": {
                    "chi": str(row["chi"]),
                },
                "blockNumber": row["blockNumber"],
                "transactionIndex": -5,
                "logIndex": -5,
            }

    def make_block_range_condition(
        self, min_block: int = None, max_block: int = None
    ) -> dict:
        block_number = {}
        if min_block:
            block_number.update({"$gte": min_block})
        if max_block is None:
            max_block = self.get_max_block()
        block_number.update({"$lte": max_block})
        return {"blockNumber": block_number}

    @lru_cache(maxsize=None)
    def get_max_block(self):
        cursor = db.events.aggregate(
            [
                {"$match": {"event": "AccrueInterest"}},
                {"$group": {"_id": "$address", "max_block": {"$max": "$blockNumber"}}},
                {"$group": {"_id": None, "block": {"$min": "$max_block"}}},
            ]
        )
        return next(cursor)["block"]
