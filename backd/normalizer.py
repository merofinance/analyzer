from typing import Any


def normalize_value(value: Any) -> dict:
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
