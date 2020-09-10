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


@Protocol.register("compound")
class CompoundProtocol(Protocol):
    def create_processor(self, hooks: Hooks = None) -> Processor:
        return CompoundProcessor(hooks=hooks)

    def create_empty_state(self) -> CompoundState:
        return CompoundState.create()

    def count_events(self) -> int:
        return db.events.count_documents({}) + db.ds_values.count_documents({})

    def iterate_events(self) -> Iterable[dict]:
        return utils.merge_sorted_streams(
            db.events.find().sort(SORT_KEY),
            self.fetch_ds_values(),
            key=PointInTime.from_event,
        )

    def fetch_ds_values(self) -> Iterable[dict]:
        for row in db.ds_values.find().sort("block"):
            yield {
                "event": "InvertedPricePosted",
                "address": row["address"],
                "returnValues": {"newPriceMantissa": str(row["price"])},
                "blockNumber": row["block"],
                # assume it is the first event in the block
                # although it would require more information to be sure
                "transactionIndex": -1,
                "logIndex": -1,
            }
