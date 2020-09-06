# backd

## Install backd

```
git clone https://github.com/danhper/backd.git
cd backd
pip install -e .
```

## Setting up the database

MongoDB needs to be running

```
find /path/to/events -name "*.jsonl.gz" | xargs zcat | mongoimport --db=backd-data --collection=events
python scripts/store_dsr.py data/dsr-rates.json
backd create-indices
```

## Testing

Populate test database

```
python scripts/import_test_data.py
```

Run tests

```
pytest
```
