from abc import ABC, abstractmethod
from ...base_factory import BaseFactory

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
