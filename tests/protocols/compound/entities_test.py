import pytest

from backd.protocols.compound.entities import InterestRateModels
from backd.protocols.compound.interest_rate_models import InterestRateModel


def test_interest_rate_models(dsr):
    models = InterestRateModels(dsr=dsr)
    assert len(models) == 0
    with pytest.raises(KeyError):
        models.get_model("0x1234")
    with pytest.raises(ValueError):
        models.create_model("0x1234")
    models.create_model("0xbae0")
    assert len(models) == 1
    assert isinstance(models.get_model("0xbae0"), InterestRateModel)
