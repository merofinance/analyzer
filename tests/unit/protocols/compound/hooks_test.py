from backd.protocols.compound.hooks import DSRHook
from backd.protocols.compound.entities import CompoundState
from backd.entities import Market, PointInTime, Balances
from backd.tokens.dai.dsr import DSR
from backd import constants


def test_dsr_hook(dummy_dsr_rates):
    dsr = DSR(dummy_dsr_rates)
    state = CompoundState("compound", dsr=dsr)
    state.current_event_time = PointInTime(99, 1, 1)
    hook = DSRHook()

    state.markets.add_market(
        Market("0x1234", balances=Balances(total_underlying=10)))
    hook.run(state)
    assert state.markets.find_by_address(
        "0x1234").balances.total_underlying == 10

    cdai_market = Market(constants.CDAI_ADDRESS,
                         balances=Balances(total_underlying=10))
    state.markets.add_market(cdai_market)
    hook.run(state)
    assert cdai_market.balances.total_underlying == 10

    state.current_event_time = PointInTime(105, 1, 1)
    hook.run(state)
    assert cdai_market.balances.total_underlying == 11

    state.current_event_time = PointInTime(106, 1, 1)
    hook.run(state)
    assert cdai_market.balances.total_underlying == 12

    state.current_event_time = PointInTime(110, 1, 1)
    hook.run(state)
    assert cdai_market.balances.total_underlying == 18