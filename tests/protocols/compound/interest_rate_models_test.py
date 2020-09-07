import pytest

from backd.protocols.compound.interest_rate_models import USDTRateModel, JumpRateModel
from backd.protocols.compound.interest_rate_models import JumpRateModelV2
from backd.protocols.compound.interest_rate_models import DAIInterestRateModel
from backd.protocols.compound.interest_rate_models import DAIInterestRateModelV2
from backd.protocols.compound.interest_rate_models import DAIInterestRateModelV3
from backd.protocols.compound.interest_rate_models import Base0bpsSlope2000bpsRateModel
from backd.protocols.compound.interest_rate_models import Base200bpsSlope1000bpsRateModel
from backd.protocols.compound.interest_rate_models import Base200bpsSlope3000bpsRateModel
from backd.protocols.compound.interest_rate_models import Base500bpsSlope1200bpsRateModel
from backd.protocols.compound.interest_rate_models import Base500bpsSlope1500bpsRateModel
from backd.tokens.dai.dsr import DSR


BLOCK_NUMBER = 102


def test_jump_rate_model():
    # https://etherscan.io/address/0x5562024784cc914069d67d89a28e3201bf7b57e7#readContract
    model = JumpRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 15854895991
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17), BLOCK_NUMBER) == 8561643834
    assert model.get_utilization_rate(2000, 1500, 1000) == 600000000000000000

def test_jump_rate_model_v2():
    # https://etherscan.io/address/0xfb564da37b41b2f6b6edcc3e56fbf523bd9f2012#readContract
    model = JumpRateModelV2()

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 14269406392
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17), BLOCK_NUMBER) == 7705479451
    assert model.get_utilization_rate(2000, 1500, 1000) == 600000000000000000


def test_usdt_rate_model():
    # https://etherscan.io/address/0x6bc8fe27d0c7207733656595e73c0d5cf7afae36#readContract
    model = USDTRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 66590563165
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17), BLOCK_NUMBER) == 35958904108
    assert model.get_utilization_rate(2000, 1500, 1000) == 600000000000000000


def test_base0bps_slope2000bps_rate_model():
    # https://etherscan.io/address/0xc64c4cba055efa614ce01f4bad8a9f519c4f8fab#readContract
    model = Base0bpsSlope2000bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 40769732550


def test_base200bps_slope1000bps_rate_model():
    # https://etherscan.io/address/0x0c3f8df27e1a00b47653fde878d68d35f00714c0#readContract
    model = Base200bpsSlope1000bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 29897803870


def test_base200bps_slope3000bps_rate_model():
    # https://etherscan.io/address/0xbae04cbf96391086dc643e842b517734e214d698#readContract
    model = Base200bpsSlope3000bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 70667536420


def test_base500bps_slope1200bps_rate_model():
    # https://etherscan.io/address/0xa1046abfc2598f48c44fb320d281d3f3c0733c9a#readContract
    model = Base500bpsSlope1200bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 48244183518


def test_base500bps_slope1500bps_rate_model():
    # https://etherscan.io/address/0xd928c8ead620bb316d2cefe3caf81dc2dec6ff63#readContract
    model = Base500bpsSlope1500bpsRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 54359643400


def test_dai_interest_rate_model(dsr_rates):
    # https://etherscan.io/address/0xec163986cC9a6593D6AdDcBFf5509430D348030F#readContract
    dsr = DSR(dsr_rates)
    model = DAIInterestRateModel(dsr,
                                 base_rate_per_block=0,
                                 multiplier_per_block=264248265,
                                 jump_multiplier_per_block=570776255707)

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 158548959
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17), BLOCK_NUMBER) == 85616437

    old_block = 9684437 # dsr_per_block = 18655209840
    model = DAIInterestRateModel(dsr,
                                 base_rate_per_block=19637062989,
                                 multiplier_per_block=264248265,
                                 jump_multiplier_per_block=570776255707)
    assert model.dsr_per_block(old_block) == 18655209840
    assert model.get_borrow_rate(2000, 1500, 1000, old_block) == 19795611948
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17), old_block) == 25613798323


def test_dai_interest_rate_model_v2(dsr_rates):
    # https://etherscan.io/address/0x000000007675b5E1dA008f037A0800B309e0C493#readContract
    dsr = DSR(dsr_rates)
    model = DAIInterestRateModelV2(dsr,
                                   base_rate_per_block=0,
                                   multiplier_per_block=10569930661,
                                   jump_multiplier_per_block=570776255707)

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 6341958396
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17), BLOCK_NUMBER) == 3424657533


def test_dai_interest_rate_model_v3(dsr_rates):
    # https://etherscan.io/address/0xfeD941d39905B23D6FAf02C8301d40bD4834E27F#readContract
    dsr = DSR(dsr_rates)
    model = DAIInterestRateModelV3(dsr)

    assert model.get_borrow_rate(2000, 1500, 1000, BLOCK_NUMBER) == 14269406392
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17), BLOCK_NUMBER) == 7705479451


def test_interest_rate_model_update_params():
    model = JumpRateModel()
    assert model.multiplier_per_block == 10569930661

    model.update_params({"0": 100, "multiplierPerBlock": 100, "kink": 200, "1": 200})
    assert model.kink == 200
    assert model.multiplier_per_block == 100

    with pytest.raises(ValueError):
        model.update_params({"someParam": 100})
