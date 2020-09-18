#!/bin/sh

if [ $# -ne 1 ]; then
  echo "usage: setup-db.sh /path/to/data"
  exit 1
fi

data_path="$1"

find "$data_path/events" -name "*.jsonl.gz" | xargs zcat | mongoimport --db=backd-data --collection=events
python scripts/store_dsr.py data/dsr-rates.json
python scripts/store_ds_values.py "$data_path/compound/medianizer-peek-full.jsonl.gz" -a 0x729D19f657BD0614b4985Cf1D82531c67569197B
backd create-indices
