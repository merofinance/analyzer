# backd

## Install backd

```
git clone https://github.com/danhper/backd.git
cd backd
pip install -e .
```

## Data

The required data can be downloaded from:
https://www.dropbox.com/sh/i5v1orfxg2la7f6/AACNX9078VnONF02lIWwZjbJa?dl=0

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


## Mainnet contracts

* comptroller: https://etherscan.io/address/0xaf601cbff871d0be62d18f79c31e387c76fa0374#code
