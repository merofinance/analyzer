# backd

## Install backd

```sh
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
find /path/to/data/events -name "*.jsonl.gz" | xargs zcat | mongoimport --db=backd-data --collection=events
python scripts/store_dsr.py data/dsr-rates.json
python scripts/store_ds_values.py /path/to/data/compound/medianizer-peek-full.jsonl.gz -a 0x729D19f657BD0614b4985Cf1D82531c67569197B
backd create-indices
```

Note for iOS users, replace `zcat` with `gzcat`. See [zcat vs gzcat](http://fanhuan.github.io/en/2016/01/07/zcat-vs-gzcat/).

## Testing

Populate test database

```sh
python scripts/import_test_data.py
```

Run tests

```sh
pytest
```


## Mainnet contracts

* comptroller: https://etherscan.io/address/0xaf601cbff871d0be62d18f79c31e387c76fa0374#code
