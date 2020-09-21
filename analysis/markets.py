import pandas as pd
import backd.protocols.compound.constants as cnstnts
from backd import db

ctokens = pd.DataFrame(cnstnts.MARKETS)[['address','symbol','decimals']].set_index('address')
db.db.blocks.delete_one({"timestamp": "timestamp"})
block_dates = db.get_block_dates()

liquidations = list(db.db.events.find({"event": "LiquidateBorrow"}))


def ctoken_sym(addr):
    return ctokens.loc[str.lower(addr)]['symbol']

def ctoken_dec(addr):
    return 10**8 #ctokens.loc[str.lower(addr)]['decimals']


liquidations_db = pd.DataFrame({
    'borrowedToken': ctoken_sym(this_row['address']),
    'timestamp': block_dates[this_row['blockNumber']],
    'transactionHash': this_row['transactionHash'],
    'liquidator': this_row['returnValues']['liquidator'],
    'borrower': this_row['returnValues']['borrower'],
    'repayAmount': int(this_row['returnValues']['repayAmount'])/ctoken_dec(this_row['address']),
    'collateralToken': ctoken_sym(this_row['returnValues']['cTokenCollateral']),
    'collateralSeized': int(this_row['returnValues']['seizeTokens'])/ctoken_dec(this_row['returnValues']['cTokenCollateral'])
} for this_row in liquidations)


liquidations_db.groupby(['borrowedToken']).sum()
liquidations_db.groupby(['collateralToken']).sum()['collateralSeized']