from backd.protocols.compound.interest_rate_models import USDTRateModel
from backd.protocols.compound.interest_rate_models import Base0bpsSlope2000bpsRateModel


def test_usdt_rate_model():
    # https://etherscan.io/address/0x6bc8fe27d0c7207733656595e73c0d5cf7afae36#readContract
    model = USDTRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000) == 66590563165
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17)) == 35958904108
    assert model.get_utilization_rate(2000, 1500, 1000) == 600000000000000000


def test_base0bps_slope2000bps_rate_model():
    # https://etherscan.io/address/0xc64c4cba055efa614ce01f4bad8a9f519c4f8fab#readContract
    model = Base0bpsSlope2000bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000) == 40769732550
