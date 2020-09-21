#!/bin/bash

set -e

if [ $# -ne 1 ]; then
  echo "usage: setup-db.sh /path/to/data"
  exit 1
fi

data_path="$1"
echo "Using data in $data_path"

echo "Inserting all blocks"
zcat "$data_path/blocks.csv.gz" | mongoimport --db=backd-data --collection=blocks --headerline --type=csv
echo "Inserting all events"
find "$data_path/events" -name "*.jsonl.gz" -print0 | xargs -0 zcat | mongoimport --db=backd-data --collection=events
echo "Inserting DSR rates"
python scripts/store_int_results.py data/dsr-rates.json -c dsr -f rate
echo "Inserting chi values"
python scripts/store_int_results.py "$data_path/compound/chi-values.jsonl.gz" -c chi_values -f chi
echo "Inserting DS Values"
python scripts/store_ds_values.py "$data_path/compound/medianizer-peek-full.jsonl.gz" -a 0x729D19f657BD0614b4985Cf1D82531c67569197B
echo "Creating indices"
backd create-indices
