import heapq


def merge_sorted_streams(*streams, key=lambda x: x):
    values = []

    def _add_next(iterator):
        try:
            value = next(iterator)
            sort_key = key(value)
            heapq.heappush(values, (sort_key, value, iterator))
        except StopIteration:
            pass

    for stream in streams:
        iterator = iter(stream)
        _add_next(iterator)
    while values:
        _sort_key, value, iterator = heapq.heappop(values)
        yield value
        _add_next(iterator)
