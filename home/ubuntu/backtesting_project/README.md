# Cryptocurrency Backtesting Engine

This project provides a backtesting framework for cryptocurrency trading strategies using Python and the Backtrader library. It allows you to test your strategies on historical data provided in CSV format, taking into account factors like commission, slippage, and execution delays.

## Features

*   **Backtrader Integration:** Leverages the powerful Backtrader library for event-driven backtesting.
*   **CSV Data Input:** Easily load historical price data (OHLCV) from CSV files.
*   **Customizable Strategies:** Define your own trading strategies by inheriting from a base class.
*   **Parameterizable:** Pass parameters to your strategies via the command line.
*   **Realistic Simulation:** Includes models for:
    *   Commission (percentage-based).
    *   Slippage (fixed spread + volume impact).
    *   Execution Delay (randomized).
*   **Flexible Timeframes:** Supports various timeframes (e.g., `1m`, `5m`, `1h`, `1d`).
*   **Date Range Selection:** Specify the start and end dates for your backtest.
*   **Reporting:**
    *   Generates standard Backtrader plots (equity curve, trades, etc.).
    *   Creates detailed HTML performance reports using QuantStats.

## Project Structure

```
backtesting_project/
├── core/                  # Core backtesting engine components
│   ├── __init__.py
│   ├── backtester.py      # Main backtesting logic (Cerebro setup, run)
│   ├── data_handler.py    # Loads and prepares CSV data
│   ├── reporting.py       # Generates plots and HTML reports
│   └── slippage.py        # Custom slippage and delay model
├── data/                  # Directory for your CSV data files
│   └── sample_data.csv    # Example empty data file (replace with real data)
│   └── test_data_daily.csv # Sample daily data for testing
├── reports/               # Output directory for plots and reports
├── strategies/            # Strategy definitions
│   ├── __init__.py
│   ├── base_strategy.py   # Base strategy class and example (MovingAverageCross)
│   └── user_strategy.py   # Template for your custom strategies
├── main.py                # Command-line interface to run backtests
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Setup

1.  **Clone or Download:** Get the project files.
2.  **Prepare Data:**
    *   Place your historical cryptocurrency data in CSV format inside the `data/` directory.
    *   The CSV file must have columns: `Date`, `Open`, `High`, `Low`, `Close`, `Volume`.
    *   The `Date` column should be in a format recognizable by Pandas/Backtrader, ideally `YYYY-MM-DD HH:MM:SS` or `YYYY-MM-DD` for daily data. The `data_handler.py` currently expects `YYYY-MM-DD HH:MM:SS` by default but Backtrader is flexible.
    *   A sample daily data file (`test_data_daily.csv`) is included for demonstration.
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run backtests using the `main.py` script from your terminal within the `backtesting_project` directory.

**Command Line Arguments:**

*   `--data`: (Required) Path to the CSV data file (e.g., `data/test_data_daily.csv`).
*   `--symbol`: (Required) Trading pair symbol (e.g., `BTCUSDT`).
*   `--timeframe`: (Required) Data timeframe (e.g., `1h`, `1d`).
*   `--fromdate`: (Required) Start date (`YYYY-MM-DD`).
*   `--todate`: (Required) End date (`YYYY-MM-DD`).
*   `--strategy-module`: Module containing the strategy class (default: `base_strategy`). Use `user_strategy` for strategies in `user_strategy.py`.
*   `--strategy`: (Required) Name of the strategy class (e.g., `MovingAverageCrossStrategy`, `MyCustomStrategy`).
*   `--strategy-params`: Strategy parameters as `key=value` pairs (e.g., `fast_ma_period=10 slow_ma_period=50`).
*   `--cash`: Initial portfolio cash (default: `10000.0`).
*   `--commission`: Commission percentage (default: `0.001`).
*   `--spread`: Fixed spread fraction for slippage (default: `0.0001`).
*   `--volume-impact`: Volume impact factor for slippage (default: `0.1`).
*   `--min-delay`: Min execution delay in ms (default: `5`).
*   `--max-delay`: Max execution delay in ms (default: `50`).
*   `--plot`: Generate Backtrader plot (saved in `reports/`).
*   `--report`: Generate HTML report using QuantStats (saved in `reports/`).
*   `--output-dir`: Directory to save plots and reports (default: `reports`).

**Example:**

Run the sample `MovingAverageCrossStrategy` on the included daily test data:

```bash
python main.py \
    --data data/test_data_daily.csv \
    --symbol TESTBTCUSD \
    --timeframe 1d \
    --fromdate 2021-01-01 \
    --todate 2023-06-30 \
    --strategy MovingAverageCrossStrategy \
    --strategy-params fast_ma_period=15 slow_ma_period=60 \
    --cash 100000 \
    --commission 0.001 \
    --spread 0.0002 \
    --plot \
    --report
```

This command will:

1.  Load data from `data/test_data_daily.csv`.
2.  Run the `MovingAverageCrossStrategy` with MA periods 15 and 60.
3.  Simulate trading between `2021-01-01` and `2023-06-30` with $100,000 initial cash, 0.1% commission, and specified slippage.
4.  Generate a plot (`.png`) and an HTML report in the `reports/` directory.

## Creating Your Own Strategy

1.  Open `strategies/user_strategy.py`.
2.  Create a new class that inherits from `BaseStrategy` (or `bt.Strategy` if you don't need the base logging/handling).
3.  Implement the `__init__` method to define your indicators.
4.  Implement the `next` method to define your entry and exit logic.
5.  Run your strategy using `main.py`, specifying `--strategy-module user_strategy` and `--strategy YourStrategyClassName`.

```python
# In strategies/user_strategy.py
from .base_strategy import BaseStrategy
import backtrader as bt

class MyRSIStrategy(BaseStrategy):
    params = (
        ("rsi_period", 14),
        ("rsi_overbought", 70),
        ("rsi_oversold", 30),
    )

    def __init__(self):
        super().__init__()
        self.rsi = bt.indicators.RSI(period=self.params.rsi_period)

    def next(self):
        if self.order: # Check for pending orders
            return

        if not self.position: # Not in the market
            if self.rsi < self.params.rsi_oversold:
                self.log(f"BUY CREATE, RSI: {self.rsi[0]:.2f}")
                self.order = self.buy()
        else: # In the market
            if self.rsi > self.params.rsi_overbought:
                self.log(f"SELL CREATE, RSI: {self.rsi[0]:.2f}")
                self.order = self.sell()
```

**Run the custom RSI strategy:**

```bash
python main.py \
    --data data/test_data_daily.csv \
    --symbol TESTBTCUSD \
    --timeframe 1d \
    --fromdate 2021-01-01 \
    --todate 2023-06-30 \
    --strategy-module user_strategy \
    --strategy MyRSIStrategy \
    --strategy-params rsi_period=21 rsi_overbought=75 rsi_oversold=25 \
    --plot \
    --report
```

