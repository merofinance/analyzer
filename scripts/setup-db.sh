#!/bin/sh

if [ $# -ne 1 ]; then
  echo "usage: setup-db.sh /path/to/events"
  exit 1
fi

events_path="$1"

find "$events_path" -name "*.jsonl.gz" | xargs zcat | mongoimport --db=backd-data --collection=events
python scripts/store_dsr.py data/dsr-rates.json
backd create-indices
