# /home/ubuntu/backtesting_project/strategies/user_strategy.py

import backtrader as bt
from .base_strategy import BaseStrategy # Import base class

# -----------------------------------------------------------------------------
# --- Define Your Custom Strategy Here ---
# -----------------------------------------------------------------------------

class MyCustomStrategy(BaseStrategy):
    """
    This is a placeholder for your custom strategy.
    Inherit from BaseStrategy to get basic logging and order/trade handling.
    Implement the __init__ method to set up indicators and the next method
    for your trading logic.
    """
    params = (
        # Add your strategy parameters here, e.g.:
        # ("my_param", 20),
        ("verbose", True), # Inherited, controls logging
    )

    def __init__(self):
        """Initialize indicators and state variables."""
        super().__init__() # Call the base class initializer

        # --- Add your indicators here ---
        # Example: Simple Moving Average
        # self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.my_param)

        self.log("MyCustomStrategy Initialized")

    def next(self):
        """Define the trading logic for each bar."""
        # Access data like this:
        # self.data.open[0], self.data.high[0], self.data.low[0], self.data.close[0]
        # self.data.volume[0], self.data.datetime[0]

        # Log the closing price
        # self.log(f"Current Close: {self.dataclose[0]:.2f}")

        # --- Implement your entry and exit logic here ---

        # Example: Buy if close is above SMA (if SMA was defined in __init__)
        # if not self.position: # Not in the market
        #     if self.dataclose[0] > self.sma[0]:
        #         self.log(f"BUY CREATE, Close: {self.dataclose[0]:.2f}")
        #         self.order = self.buy()
        # else: # Already in the market
        #     if self.dataclose[0] < self.sma[0]:
        #         self.log(f"SELL CREATE, Close: {self.dataclose[0]:.2f}")
        #         self.order = self.sell()

        pass # Remove this once you add logic

# -----------------------------------------------------------------------------
# --- You can add more strategy classes below ---
# -----------------------------------------------------------------------------


