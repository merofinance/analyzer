from backd import utils


def test_merge_sorted_streams():
    result = list(utils.merge_sorted_streams([1, 5, 8], [2, 4, 7]))
    assert result == [1, 2, 4, 5, 7, 8]

    result = list(utils.merge_sorted_streams(["lb", "fbc", "ibcd"], ["z", "obcde", "nbcdef"], key=len))
    assert result == ["z", "lb", "fbc", "ibcd", "obcde", "nbcdef"]
