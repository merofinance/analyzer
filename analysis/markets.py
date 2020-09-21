import pandas as pd
import backd.protocols.compound.constants as cnstnts
from backd import db

liquidations = list(db.db.events.find({"event": "LiquidateBorrow"}))

db.db.blocks.delete_one({"timestamp": "timestamp"})
block_dates = db.get_block_dates()

liquidations_db = pd.DataFrame({
    'address': this_row['address'],
    'blockNumber': this_row['blockNumber'],
    'transactionHash': this_row['transactionHash'],
    'liquidator': this_row['returnValues']['liquidator'],
    'borrower': this_row['returnValues']['borrower'],
    'repayAmount': this_row['returnValues']['repayAmount'],
    'cTokenCollateral': this_row['returnValues']['cTokenCollateral'],
    'seizeTokens': this_row['returnValues']['seizeTokens']
} for this_row in liquidations)




# import gzip
# import json
# import math
# import pickle
# import multiprocessing
# import csv
# import glob

# import numpy as np
# from os import path
# from datetime import datetime
# from itertools import groupby
# from collections import Counter
# from param import *

# def market_info(file):
#     print('start', file)
#     events = []
#     events_LiquidateBorrow  = []
#     with gzip.open(file) as f:
#         for i, row in enumerate(f):
#             this_row = json.loads(row)
#             data = {
#                 'address': this_row['address'],
#                 'blockNumber': this_row['blockNumber'],
#                 'event': this_row['event']
#             }
#             events.append(data)
#             # if this_row['event'] == 'LiquidateBorrow':
#             #    data_LiquidateBorrow = {
#             #     'blockNumber': this_row['blockNumber'],
#             #     'transactionHash': this_row['transactionHash'],
#             #     'liquidator': this_row['returnValues']['liquidator'],
#             #     'borrower': this_row['returnValues']['borrower'],
#             #     'repayAmount': this_row['returnValues']['repayAmount'],
#             #     'cTokenCollateral': this_row['returnValues']['cTokenCollateral'],
#             #     'seizeTokens': this_row['returnValues']['seizeTokens'],
#             #    }
#             #    events_LiquidateBorrow.append(data_LiquidateBorrow)
#             if i % 10000 == 0:
#                 print(i)
#     events_df = pd.DataFrame(events)
#     events_df_LiquidateBorrow = pd.DataFrame(events_LiquidateBorrow)
#     return(events_df, events_df_LiquidateBorrow)