# /home/ubuntu/backtesting_project/strategies/base_strategy.py

import backtrader as bt

class BaseStrategy(bt.Strategy):
    """
    Base class for strategies. Can be inherited by user strategies.
    Includes basic logging.
    """
    params = (
        ("verbose", True), # Enable/disable strategy logging
    )

    def log(self, txt, dt=None):
        """ Logging function for this strategy"""
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} - {txt}")

    def __init__(self):
        """Initializes the strategy"""
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        """Handles order notifications."""
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}"
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        """Handles trade notifications."""
        if not trade.isclosed:
            return

        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")

    def next(self):
        """
        Defines the logic for the next candle.
        This method needs to be overridden by specific strategy implementations.
        """
        # Simply log the closing price of the series from the reference
        # self.log(f"Close, {self.dataclose[0]:.2f}")
        pass # Base strategy does nothing, override in subclasses


class MovingAverageCrossStrategy(BaseStrategy):
    """
    A simple Moving Average Crossover strategy.
    Enters long when the fast MA crosses above the slow MA.
    Exits long when the fast MA crosses below the slow MA.
    """
    params = (
        ("fast_ma_period", 10),
        ("slow_ma_period", 50),
        ("verbose", True),
    )

    def __init__(self):
        """Initializes the strategy indicators and state."""
        super().__init__() # Call base class init

        # Add Moving Average indicators
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_ma_period
        )
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_ma_period
        )

        # Add Crossover indicator
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)

    def next(self):
        """Executes the strategy logic for the next candle."""
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # We are not in the market, look for a signal to enter
            if self.crossover > 0:  # Fast MA crossed above Slow MA
                self.log(f"BUY CREATE, Close: {self.dataclose[0]:.2f}")
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:
            # We are in the market, look for a signal to exit
            if self.crossover < 0:  # Fast MA crossed below Slow MA
                self.log(f"SELL CREATE, Close: {self.dataclose[0]:.2f}")
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


