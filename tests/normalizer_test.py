from backd import normalizer


def test_normalize_value():
    assert normalizer.normalize_value("0xA12b3C") == "0xa12b3c"


def test_normalize_event_values(compound_dummy_events):
    new_comptroller_event = compound_dummy_events[0]
    normalized_values = normalizer.normalize_event_values(new_comptroller_event["returnValues"])
    assert normalized_values["newComptroller"] == "0xc2a1"


def test_normalize_event(compound_dummy_events):
    new_comptroller_event = compound_dummy_events[0]
    normalized_event = normalizer.normalize_event(new_comptroller_event)
    assert normalized_event["address"] == "0x1a3b"
    assert normalized_event["returnValues"]["newComptroller"] == "0xc2a1"
