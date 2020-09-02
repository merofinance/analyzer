from typing import Union
from decimal import Decimal

from bson import Decimal128

from ... import constants
from ...db import db


SECONDS_PER_DAY = 60 * 60 * 24
DAYS_IN_YEAR = 365
DECIMALS = Decimal(10) ** constants.DSR_DECIMALS


def compute_apy(dsr: Union[int, str, Decimal, Decimal128]):
    if isinstance(dsr, Decimal128):
        dsr = dsr.to_decimal()
    if isinstance(dsr, (int, str)):
        dsr = Decimal(dsr)
    return ((dsr / DECIMALS - 1) * SECONDS_PER_DAY + 1) ** DAYS_IN_YEAR


def fetch_dsr_rates():
    return [{"block": row["block"], "rate": row["rate"].to_decimal()}
             for row in db.dsr.find()]
