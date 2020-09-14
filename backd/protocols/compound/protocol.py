from typing import Iterable

from ...event_processor import Processor
from ...hook import Hooks
from ...entities import PointInTime
from ...db import db, SORT_KEY
from ...protocol import Protocol
from ... import utils
from .entities import CompoundState
from .processor import CompoundProcessor
from . import oracles # pylint: disable=unused-import
from .constants import DS_VALUES_MAPPING


@Protocol.register("compound")
class CompoundProtocol(Protocol):
    def create_processor(self, hooks: Hooks = None) -> Processor:
        return CompoundProcessor(hooks=hooks)

    def create_empty_state(self) -> CompoundState:
        return CompoundState.create()

    def count_events(self, min_block: int = None, max_block: int = None) -> int:
        condition = self.make_max_block_condition(min_block, max_block)
        return db.events.count_documents(condition) + db.ds_values.count_documents(condition)

    def iterate_events(self, min_block: int = None, max_block: int = None) -> Iterable[dict]:
        condition = self.make_max_block_condition(min_block, max_block)
        return utils.merge_sorted_streams(
            db.events.find(condition).sort(SORT_KEY),
            self.fetch_ds_values(condition),
            self.sai_price_events(min_block=min_block, max_block=max_block),
            key=PointInTime.from_event,
        )

    def sai_price_events(self, min_block: int = None, max_block: int = None):
        events = [{
            "address": "0xddc46a3b076aec7ab3fc37420a8edd2959764ec4",
            "block": 10_067_346,
            "sai_price": 5285551943761727,
        }]

        for event in events:
            if (min_block is not None and event["block"] < min_block) or \
                    max_block is not None and event["block"] > max_block:
                continue
            yield {
                "event": "SaiPriceSet",
                "address": event["address"],
                "returnValues": {
                    "newPriceMantissa": str(event["sai_price"])
                },
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
                # assume it is the first event in the block
                # although it would require more information to be sure
                "transactionIndex": -1,
                "logIndex": -1,
            }

    def make_max_block_condition(self, min_block: int = None, max_block: int = None) -> dict:
        block_number = {}
        if min_block:
            block_number.update({"$gte": min_block})
        if max_block:
            block_number.update({"$lte": max_block})
        if block_number:
            return {"blockNumber": block_number}
        return {}
