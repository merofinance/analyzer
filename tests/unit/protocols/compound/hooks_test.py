from backd.protocols.compound.hooks import DSRHook
from backd.protocols.compound.entities import CompoundState, CDaiMarket
from backd.entities import PointInTime
from backd.tokens.dai.dsr import DSR
from backd.protocols.compound import constants


def test_dsr_hook(dummy_dsr_rates):
    dsr = DSR(dummy_dsr_rates)
    state = CompoundState("compound", dsr=dsr)
    state.current_event_time = PointInTime(99, 1, 1)
    hook = DSRHook()

    state.markets.add_market(
        CDaiMarket("0x1234", dsr_amount=10))
    hook.block_start(state, 99)
    assert state.markets.find_by_address(
        "0x1234").dsr_amount == 10

    cdai_market = CDaiMarket(constants.CDAI_ADDRESS, dsr_amount=10)
    state.markets.add_market(cdai_market)
    hook.block_start(state, 99)
    assert cdai_market.dsr_amount == 10

    state.current_event_time = PointInTime(105, 1, 1)
    hook.block_start(state, 105)
    assert cdai_market.dsr_amount == 11

    state.current_event_time = PointInTime(106, 1, 1)
    hook.block_start(state, 106)
    assert cdai_market.dsr_amount == 12

    state.current_event_time = PointInTime(110, 1, 1)
    hook.block_start(state, 110)
    assert cdai_market.dsr_amount == 18
