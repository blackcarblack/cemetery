# /home/ubuntu/backtesting_project/core/slippage.py

import backtrader as bt
import random

class CustomSlippage(bt.CommInfoBase): # Inherit from CommInfoBase to also handle commission if needed, or just object
    """
    A custom slippage model that simulates:
    - Fixed spread component.
    - Variable slippage based on order size relative to volume.
    - Random delay component.

    Note: Backtrader's default slippage models might be simpler.
    This is a conceptual implementation for more complex modeling.
    Backtrader applies slippage *after* the theoretical fill price.
    """
    params = (
        ("fixed_spread", 0.0001),  # Fixed spread as a fraction of price (e.g., 0.01%)
        ("volume_impact_factor", 0.1), # How much % of bar volume impacts price
        ("min_delay_ms", 5),      # Minimum order execution delay in milliseconds
        ("max_delay_ms", 100),     # Maximum order execution delay in milliseconds
        # Commission can also be handled here if inheriting CommInfoBase
        # (
        #     "commission", 0.001, # Example: 0.1% commission
        #     "mult", 1.0,
        #     "margin", None,
        #     "commtype", bt.CommInfoBase.COMM_PERC,
        # )
    )

    def _getslippage(self, price, size, isbuy, data):
        """
        Calculates the slippage amount based on spread and volume impact.
        This method is called internally by Backtrader when simulating fills.
        It needs to return the *slippage amount* to be added/subtracted.
        """
        # 1. Fixed Spread Component
        spread_slippage = price * self.p.fixed_spread / 2.0 # Apply half spread

        # 2. Volume Impact Component
        # Use the volume of the current bar as a proxy for liquidity
        # A large order relative to volume causes more slippage
        bar_volume = data.volume[0]
        volume_slippage = 0.0
        if bar_volume > 0:
            order_ratio = abs(size) / bar_volume
            # Slippage increases non-linearly with order size ratio
            volume_slippage = price * self.p.volume_impact_factor * (order_ratio ** 0.5)

        # Total slippage amount
        total_slippage = spread_slippage + volume_slippage

        # Slippage is always adverse
        if isbuy:
            return total_slippage # Add slippage for buys
        else:
            return -total_slippage # Subtract slippage for sells (price moves against you)

    def _getdelay(self):
        """
        Simulates a random delay in order execution.
        Returns delay in days (Backtrader's unit for time delays).
        """
        delay_ms = random.uniform(self.p.min_delay_ms, self.p.max_delay_ms)
        delay_days = delay_ms / (1000 * 60 * 60 * 24) # Convert ms to days
        return delay_days

    # Override get_slippage_perc if you prefer percentage-based calculation
    # def get_slippage_perc(self, price, size, isbuy, data):
    #     slippage_amount = self._getslippage(price, size, isbuy, data)
    #     return slippage_amount / price if price else 0.0

    # Override execute to potentially incorporate delay logic if needed
    # def execute(self, order, data, broker, cash, size, price, date):
    #     # Custom execution logic potentially using self._getdelay()
    #     # Default Backtrader execution handles slippage via _getslippage
    #     # Delay might require more complex handling, potentially by modifying
    #     # the execution price based on price movement during the delay,
    #     # which is non-trivial in standard Backtrader.
    #     # For now, we rely on Backtrader's default execution flow applying
    #     # the slippage calculated by _getslippage.
    #     pass

    # If inheriting CommInfoBase, you might need to implement commission logic
    # def getcommission(self, size, price):
    #     if self.p.commtype == self.COMM_PERC:
    #         return abs(size) * price * self.p.commission
    #     elif self.p.commtype == self.COMM_FIXED:
    #         return self.p.commission
    #     return 0.0


