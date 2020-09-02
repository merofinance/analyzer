from backd.protocols.compound.interest_rate_models import USDTRateModel


def test_usdt_rate_model():
    # https://etherscan.io/address/0x6bc8fe27d0c7207733656595e73c0d5cf7afae36#readContract
    model = USDTRateModel()

    assert model.get_borrow_rate(2000, 1500, 1000) == 66590563165
    assert model.get_supply_rate(2000, 1500, 1000, int(1e17)) == 35958904108
    assert model.get_utilization_rate(2000, 1500, 1000) == 600000000000000000
