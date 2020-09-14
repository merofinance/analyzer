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

    def count_events(self, max_block: int = None) -> int:
        condition = self.make_max_block_condition(max_block)
        return db.events.count_documents(condition) + db.ds_values.count_documents(condition)

    def iterate_events(self, max_block: int = None) -> Iterable[dict]:
        condition = self.make_max_block_condition(max_block)
        return utils.merge_sorted_streams(
            db.events.find(condition).sort(SORT_KEY),
            self.fetch_ds_values(condition),
            key=PointInTime.from_event,
        )

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

    def make_max_block_condition(self, max_block: int = None) -> dict:
        if max_block is None:
            return {}
        return {"blockNumber": {"$lte": max_block}}
