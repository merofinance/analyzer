from backd import db


def test_count_events():
    assert db.count_events() == len(list(db.iterate_events()))
