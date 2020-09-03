from abc import ABC, abstractmethod
from ...base_factory import BaseFactory


EXP_SCALE = int(1e18)


def get_exp(num: int, denom: int) -> int:
    return (num * EXP_SCALE) // denom


class InterestRate(ABC, BaseFactory):
    @abstractmethod
    def get_borrow_rate(self, cash: int, borrows: int, reserves: int) -> int:
        """Calculates the current borrow interest rate per block

        :param cash: The total amount of cash the market has
        :param borrows: The total amount of borrows the market has outstanding
        :param reserves: The total amnount of reserves the market has
        :return: The borrow rate per block (as a percentage, and scaled by 1e18)
        """


    @abstractmethod
    def get_supply_rate(self, cash: int, borrows: int,
                        reserves: int, reserve_factor_mantissa: int) -> int:
        """Calculates the current supply interest rate per block

        :param cash: The total amount of cash the market has
        :param borrows: The total amount of borrows the market has outstanding
        :param reserves: The total amnount of reserves the market has
        :param reserve_factor_mantissa: The current reserve factor the market has
        :return The: supply rate per block (as a percentage, and scaled by 1e18)
        """


@InterestRate.register("0x6bc8fe27d0c7207733656595e73c0d5cf7afae36")
class USDTRateModel(InterestRate):
    def __init__(self):
        self.base_rate_per_block = 9512937595
        self.blocks_per_year = 2102400
        self.kink = 900000000000000000
        self.jump_multiplier_per_block = 951293759512
        self.multiplier_per_block = 95129375951

    def get_borrow_rate(self, cash: int, borrows: int, reserves: int) -> int:
        utilization_rate = self.get_utilization_rate(cash, borrows, reserves)
        if utilization_rate <= self.kink:
            return utilization_rate * self.multiplier_per_block // 1e18 + self.base_rate_per_block
        normal_rate = self.kink * self.multiplier_per_block // 1e18 + self.base_rate_per_block
        excess_util = utilization_rate - self.kink
        return excess_util * self.jump_multiplier_per_block // 1e18 + normal_rate

    def get_supply_rate(self, cash: int, borrows: int,
                        reserves: int, reserve_factor_mantissa: int) -> int:
        one_minus_reserve_factor = 1e18 - reserve_factor_mantissa
        borrow_rate = self.get_borrow_rate(cash, borrows, reserves)
        rate_to_pool= borrow_rate * one_minus_reserve_factor // 1e18
        return self.get_utilization_rate(cash, borrows, reserves) * rate_to_pool // 1e18

    def get_utilization_rate(self, cash: int, borrows: int, reserves: int) -> int:
        # Utilization rate is 0 when there are no borrows
        if borrows == 0:
            return 0

        return borrows * 1e18 // (cash + borrows - reserves)



class BaseSlopeRateModel(InterestRate):
    def __init__(self, multiplier: int, base_rate: int):
        self.blocks_per_year = 2102400
        self.multiplier = multiplier
        self.base_rate = base_rate

    def get_utilization_rate(self, cash: int, borrows: int) -> int:
        # Utilization rate is 0 when there are no borrows
        if borrows == 0:
            return 0

        return get_exp(borrows, cash + borrows)

    def get_borrow_rate(self, cash: int, borrows: int, reserves: int) -> int:
        annual_borrow_rate = self.get_annual_borrow_rate(cash, borrows)
        return annual_borrow_rate // self.blocks_per_year

    def get_supply_rate(self, cash: int, borrows: int,
                        reserves: int, reserve_factor_mantissa: int) -> int:
        raise ValueError("supply rate not supported by this model")

    def get_annual_borrow_rate(self, cash: int, borrows: int) -> int:
        utilization_rate = self.get_utilization_rate(cash, borrows)

        # Borrow Rate is 5% + UtilizationRate * 45% (baseRate + UtilizationRate * multiplier);
        # 45% of utilizationRate, is `rate * 45 / 100`
        utilization_rate_muled = utilization_rate * self.multiplier
        utilization_rate_scaled = utilization_rate_muled // EXP_SCALE
        annual_borrow_rate = utilization_rate_scaled + self.base_rate
        return annual_borrow_rate


@InterestRate.register("0xc64c4cba055efa614ce01f4bad8a9f519c4f8fab")
class Base0bpsSlope2000bpsRateModel(BaseSlopeRateModel):
    def __init__(self):
        super().__init__(200000000000000000, 0)


@InterestRate.register("0x0c3f8df27e1a00b47653fde878d68d35f00714c0")
class Base200bpsSlope1000bpsRateModel(BaseSlopeRateModel):
    def __init__(self):
        super().__init__(100000000000000000, 20000000000000000)


@InterestRate.register("0xbae04cbf96391086dc643e842b517734e214d698")
class Base200bpsSlope3000bpsRateModel(BaseSlopeRateModel):
    def __init__(self):
        super().__init__(300000000000000000, 20000000000000000)


@InterestRate.register("0xa1046abfc2598f48c44fb320d281d3f3c0733c9a")
class Base500bpsSlope1200bpsRateModel(BaseSlopeRateModel):
    def __init__(self):
        super().__init__(120000000000000000, 50000000000000000)


@InterestRate.register("0xd928c8ead620bb316d2cefe3caf81dc2dec6ff63")
class Base500bpsSlope1500bpsRateModel(BaseSlopeRateModel):
    def __init__(self):
        super().__init__(150000000000000000, 50000000000000000)