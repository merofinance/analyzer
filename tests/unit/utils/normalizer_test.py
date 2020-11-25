from backd.fetcher.event_listener import normalize_event
from backd.utils import normalizer
from tests.fixtures import get_event


def test_normalize_value():
    assert normalizer.normalize_value("0xA12b3C") == "0xa12b3c"


def test_normalize_event_values(compound_dummy_events):
    new_comptroller_event = get_event(compound_dummy_events, "NewComptroller")
    normalized_values = normalizer.normalize_event_values(
        new_comptroller_event["returnValues"]
    )
    assert normalized_values["newComptroller"] == "0xc2a1"


def test_normalize_event(compound_dummy_events):
    new_comptroller_event = get_event(compound_dummy_events, "NewComptroller")
    normalized_event = normalizer.normalize_event(new_comptroller_event)
    assert normalized_event["address"] == "0x1a3b"
    assert normalized_event["returnValues"]["newComptroller"] == "0xc2a1"


def test_normalize_web3_event(web3_event):
    event = normalizer.normalize_web3_event(web3_event)
    assert event["returnValues"]["value"] == "55000000"
    tx_hash = "0x8a582772dd73ca46eae762091379b69df8908272e58e0b2f7b709820fa971a50"
    assert event["transactionHash"] == tx_hash
