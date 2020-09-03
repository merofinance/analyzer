from backd.protocols.compound.interest_rate_models import USDTRateModel
from backd.protocols.compound.interest_rate_models import Base0bpsSlope2000bpsRateModel
from backd.protocols.compound.interest_rate_models import Base200bpsSlope1000bpsRateModel
from backd.protocols.compound.interest_rate_models import Base200bpsSlope3000bpsRateModel
from backd.protocols.compound.interest_rate_models import Base500bpsSlope1200bpsRateModel
from backd.protocols.compound.interest_rate_models import Base500bpsSlope1500bpsRateModel


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


def test_base200bps_slope1000bps_rate_model():
    # https://etherscan.io/address/0x0c3f8df27e1a00b47653fde878d68d35f00714c0#readContract
    model = Base200bpsSlope1000bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000) == 29897803870


def test_base200bps_slope3000bps_rate_model():
    # https://etherscan.io/address/0xbae04cbf96391086dc643e842b517734e214d698#readContract
    model = Base200bpsSlope3000bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000) == 70667536420


def test_base500bps_slope1200bps_rate_model():
    # https://etherscan.io/address/0xa1046abfc2598f48c44fb320d281d3f3c0733c9a#readContract
    model = Base500bpsSlope1200bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000) == 48244183518


def test_base500bps_slope1500bps_rate_model():
    # https://etherscan.io/address/0xd928c8ead620bb316d2cefe3caf81dc2dec6ff63#readContract
    model = Base500bpsSlope1500bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000) == 54359643400
