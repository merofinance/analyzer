# backd

## Setting up the database

MongoDB needs to be running

```
zcat /path/to/events/*.jsonl.gz | mongoimport --db=backd-data --collection=events
```

Then, run `create_indices` from `db.py`
