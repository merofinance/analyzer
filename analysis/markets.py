import numpy as np
import pandas as pd
import gzip
import json
import math
from datetime import datetime
from collections import Counter
from itertools import groupby
import pickle
import multiprocessing
import glob
from os import path
from param import *

def market_info(file):
    print('start', file)
    events = []
    with gzip.open(file) as f:
        for i, row in enumerate(f):
            this_row = json.loads(row)
            data = {
                'address': this_row['address'],
                'blockNumber': this_row['blockNumber'],
                'event': this_row['event']
            }
            events.append(data)
            if i % 10000 == 0:
                print(i)
    return(events)



market_files = sorted(glob.glob(DATA_DIR + 'events/compound/markets/*.jsonl.gz'))

xx = market_info(market_files[0])
pd.DataFrame(xx).groupby('event').sum()