import datetime as dt
from functools import lru_cache
from typing import Iterable

from ... import db, utils
from ...entities import PointInTime
from ...event_processor import Processor
from ...hook import Hooks
from ...protocol import Protocol
from . import oracles  # pylint: disable=unused-import
from . import plots
from .constants import DS_VALUES_MAPPING, DSR_ADDRESS, NULL_ADDRESS
from .entities import CompoundState
from .processor import CompoundProcessor


@Protocol.register("compound")
class CompoundProtocol(Protocol):
    def create_processor(self, hooks: Hooks = None) -> Processor:
        return CompoundProcessor(hooks=hooks)

    def create_empty_state(self) -> CompoundState:
        return CompoundState.create()

    def count_events(self, min_block: int = None, max_block: int = None) -> int:
        condition = self.make_block_range_condition(min_block, max_block)
        collections = [
            db.db.events,
            db.db.ds_values,
            db.db.chi_values,
            db.db.prices,
            db.db.blocks,
        ]
        sai_events_count = len(list(self.sai_price_events(min_block, max_block)))
        db_events_count = sum(col.count_documents(condition) for col in collections)
        return sai_events_count + db_events_count

    def iterate_events(
        self, min_block: int = None, max_block: int = None
    ) -> Iterable[dict]:
        condition = self.make_block_range_condition(min_block, max_block)
        return utils.merge_sorted_streams(
            db.db.events.find(condition).sort(db.SORT_KEY),
            self.fetch_ds_values(condition),
            self.fetch_chi_values(condition),
            self.fetch_external_prices(condition),
            self.fetch_block_timestamps(condition),
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
        cursor = db.db.ds_values.find(condition, no_cursor_timeout=True).sort(
            "blockNumber"
        )
        for row in cursor:
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
        cursor.close()

    def fetch_chi_values(self, condition: dict) -> Iterable[dict]:
        cursor = db.db.chi_values.find(condition, no_cursor_timeout=True).sort(
            "blockNumber"
        )
        for row in cursor:
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
        cursor.close()

    def fetch_external_prices(self, condition: dict) -> Iterable[dict]:
        cursor = db.prices().find(condition, no_cursor_timeout=True).sort("blockNumber")
        for row in cursor:
            yield {
                "event": "ExternalPriceUpdated",
                "address": oracles.PriceOracleV1.registered_name,
                "returnValues": {
                    "price": row["price"].to_decimal(),
                    "symbol": row["symbol"],
                },
                "blockNumber": row["blockNumber"],
                "transactionIndex": -10,
                "logIndex": -10,
            }
        cursor.close()

    def fetch_block_timestamps(self, condition: dict) -> Iterable[dict]:
        projection = {"blockNumber": 1, "timestamp": 1}
        cursor = db.db.blocks.find(
            condition, projection=projection, no_cursor_timeout=True
        ).sort("blockNumber")
        for row in cursor:
            yield {
                "event": "TimestampUpdated",
                "address": NULL_ADDRESS,
                "returnValues": {
                    "timestamp": dt.datetime.fromtimestamp(
                        int(row["timestamp"]), dt.timezone.utc
                    ),
                },
                "blockNumber": row["blockNumber"],
                "transactionIndex": -1000,
                "logIndex": -1000,
            }
        cursor.close()

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
        cursor = db.db.events.aggregate(
            [
                {"$match": {"event": "AccrueInterest"}},
                {"$group": {"_id": "$address", "max_block": {"$max": "$blockNumber"}}},
                {"$group": {"_id": None, "block": {"$min": "$max_block"}}},
            ]
        )
        return next(cursor)["block"]

    def get_plots(self):
        return plots
