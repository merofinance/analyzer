from typing import Any, Union

from web3.types import LogReceipt


def normalize_value(value: Any) -> Any:
    if isinstance(value, int):
        value = str(value)
    if isinstance(value, str) and value.startswith("0x"):
        return value.lower()
    return value


def normalize_event_values(event_values: dict):
    return {k: normalize_value(v) for k, v in event_values.items()}


def normalize_event(event: dict):
    return {
        **event,
        "address": event["address"].lower(),
        "returnValues": normalize_event_values(event["returnValues"]),
    }


def normalize_web3_event(raw_event: Union[dict, LogReceipt]):
    event = dict(raw_event).copy()
    event["transactionHash"] = event["transactionHash"].hex()  # type: ignore
    event["blockHash"] = event["blockHash"].hex()  # type: ignore
    event["returnValues"] = normalize_event_values(event.pop("args", {}))  # type: ignore
    return event
