# /home/ubuntu/backtesting_project/core/backtester.py

import backtrader as bt
import importlib
import os
import sys
from datetime import datetime

# Add project root to path to allow importing modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from core.data_handler import load_data
from core.slippage import CustomSlippage

def run_backtest(config):
    """
    Runs the backtesting process based on the provided configuration.

    Args:
        config (dict): A dictionary containing backtest parameters:
            - data_path (str): Path to the CSV data file.
            - symbol (str): Trading pair symbol.
            - timeframe (str): Data timeframe (e.g., '1h', '1d').
            - start_date (str): Start date ('YYYY-MM-DD').
            - end_date (str): End date ('YYYY-MM-DD').
            - strategy_name (str): Name of the strategy class to use (must exist in strategies module).
            - strategy_params (dict): Dictionary of parameters for the strategy.
            - initial_cash (float): Starting portfolio cash.
            - commission (float): Commission percentage (e.g., 0.001 for 0.1%).
            - slippage_params (dict): Parameters for the CustomSlippage model.

    Returns:
        tuple: (results, stats) where 'results' is the list of strategy instances
               (usually one) and 'stats' contains analyzer results, or (None, None) on error.
    """
    cerebro = bt.Cerebro()

    # --- 1. Load Data --- 
    # Convert string timeframe like '1h', '1d' to Backtrader enum
    tf_map = {
        '1m': (bt.TimeFrame.Minutes, 1),
        '5m': (bt.TimeFrame.Minutes, 5),
        '15m': (bt.TimeFrame.Minutes, 15),
        '30m': (bt.TimeFrame.Minutes, 30),
        '1h': (bt.TimeFrame.Minutes, 60), # Use Minutes for hourly
        '4h': (bt.TimeFrame.Minutes, 240),
        '1d': (bt.TimeFrame.Days, 1),
        '1w': (bt.TimeFrame.Weeks, 1),
        '1M': (bt.TimeFrame.Months, 1),
    }
    if config['timeframe'] not in tf_map:
        print(f"Error: Invalid timeframe specified: {config['timeframe']}")
        print(f"Valid timeframes: {list(tf_map.keys())}")
        return None, None

    bt_timeframe, bt_compression = tf_map[config['timeframe']]

    data_feed = load_data(
        data_path=config['data_path'],
        symbol=config['symbol'],
        timeframe=bt_timeframe, # Pass the Backtrader enum
        start_date_str=config['start_date'],
        end_date_str=config['end_date']
    )

    if data_feed is None:
        print("Error: Failed to load data feed.")
        return None, None

    # Add data feed to Cerebro
    cerebro.adddata(data_feed, name=config['symbol'])
    # Resample if necessary (e.g., using daily data to test an hourly strategy - less common with CSV)
    # cerebro.resampledata(data_feed, timeframe=bt_timeframe, compression=bt_compression)

    # --- 2. Load Strategy --- 
    try:
        # Dynamically import the strategy module
        # Assumes strategy file is named like the class but lowercase_snake_case
        # e.g., MovingAverageCrossStrategy -> moving_average_cross_strategy.py (adjust if needed)
        # For simplicity, let's assume all user strategies are in user_strategy.py for now
        # and base strategies are in base_strategy.py

        strategy_module_name = f"strategies.{config['strategy_module']}" # e.g., strategies.base_strategy
        strategy_module = importlib.import_module(strategy_module_name)
        StrategyClass = getattr(strategy_module, config['strategy_name'])

        # Add strategy to Cerebro with parameters
        cerebro.addstrategy(StrategyClass, **config.get('strategy_params', {}))
        print(f"Strategy '{config['strategy_name']}' loaded successfully.")

    except (ImportError, AttributeError) as e:
        print(f"Error loading strategy '{config['strategy_name']}' from module '{strategy_module_name}': {e}")
        print("Ensure the strategy class exists and the module name is correct.")
        return None, None

    # --- 3. Set Initial Cash --- 
    cerebro.broker.setcash(config.get('initial_cash', 10000.0))

    # --- 4. Configure Commission and Slippage --- 
    # Create slippage instance
    slippage_model = CustomSlippage(**config.get('slippage_params', {}))
    cerebro.broker.set_slippage(slippage_model)

    # Set commission
    cerebro.broker.setcommission(commission=config.get('commission', 0.001)) # Example: 0.1%

    # --- 5. Add Analyzers --- 
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn') # System Quality Number
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns', timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.PeriodStats, _name='period_stats')
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio') # For advanced analysis / HTML reports

    # --- 6. Run Backtest --- 
    print(f"Starting backtest for {config['symbol']} ({config['start_date']} to {config['end_date']})...")
    results = cerebro.run()
    print("Backtest finished.")

    # --- 7. Extract Results --- 
    if results and len(results) > 0:
        strategy_instance = results[0]
        analyzers = strategy_instance.analyzers
        stats = {}
        for name, analyzer in analyzers.getitems():
            stats[name] = analyzer.get_analysis()
        return cerebro, results, stats
    else:
        print("Error: Backtest did not produce results.")
        return None, None

# Example usage (for testing purposes, will be called from main.py later)
if __name__ == '__main__':
    # Create dummy data if it doesn't exist
    test_csv_path = os.path.join(project_root, 'data', 'test_data_daily.csv')
    if not os.path.exists(test_csv_path):
        print("Creating dummy daily data for testing...")
        import pandas as pd
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
        data = {
            'Date': dates.strftime('%Y-%m-%d %H:%M:%S'), # Format expected by CustomCSVData
            'Open': 100 + (pd.Series(range(len(dates))) * 0.1) + (pd.np.random.randn(len(dates)) * 5),
            'High': lambda x: x['Open'] + pd.np.random.rand(len(dates)) * 5,
            'Low': lambda x: x['Open'] - pd.np.random.rand(len(dates)) * 5,
            'Close': lambda x: x['Open'] + (pd.np.random.randn(len(dates)) * 3),
            'Volume': 1000 + pd.np.random.randint(0, 500, size=len(dates))
        }
        df = pd.DataFrame(data)
        df['High'] = df.apply(df['High'], axis=1)
        df['Low'] = df.apply(df['Low'], axis=1)
        df['Close'] = df.apply(df['Close'], axis=1)
        df['Open'] = df['Open'].round(2)
        df['High'] = df[['Open', 'Low', 'Close']].max(axis=1) + (pd.np.random.rand(len(dates)) * 2).round(2)
        df['Low'] = df[['Open', 'High', 'Close']].min(axis=1) - (pd.np.random.rand(len(dates)) * 2).round(2)
        df['Close'] = (df['Open'] + df['Close']) / 2 # Simplify close calculation
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].round(2)
        df.to_csv(test_csv_path, index=False)
        print(f"Dummy data created: {test_csv_path}")

    test_config = {
        'data_path': test_csv_path,
        'symbol': 'TESTBTCUSD',
        'timeframe': '1d', # Daily data
        'start_date': '2021-01-01',
        'end_date': '2023-06-30',
        'strategy_module': 'base_strategy', # Module where the strategy class is defined
        'strategy_name': 'MovingAverageCrossStrategy', # Class name
        'strategy_params': {'fast_ma_period': 15, 'slow_ma_period': 60, 'verbose': False},
        'initial_cash': 100000.0,
        'commission': 0.001, # 0.1%
        'slippage_params': {
            'fixed_spread': 0.0002, # 0.02%
            'volume_impact_factor': 0.1,
            'min_delay_ms': 5,
            'max_delay_ms': 50
        }
    }

    results, stats = run_backtest(test_config)

    if results and stats:
        print("\n--- Backtest Results Summary ---")
        print(f"Final Portfolio Value: {results[0].broker.getvalue():,.2f}")
        # Print some key stats
        if 'trade_analyzer' in stats and stats['trade_analyzer']:
            ta = stats['trade_analyzer']
            print(f"Total Trades: {ta.total.total}")
            print(f"Winning Trades: {ta.won.total}")
            print(f"Losing Trades: {ta.lost.total}")
            if ta.total.total > 0:
                 print(f"Win Rate: {ta.won.total / ta.total.total * 100:.2f}%")
            print(f"Total Net Profit: {ta.pnl.net.total:.2f}")
        if 'drawdown' in stats and stats['drawdown']:
            print(f"Max Drawdown: {stats['drawdown'].max.drawdown:.2f}%")
        if 'sharpe_ratio' in stats and stats['sharpe_ratio']:
            print(f"Sharpe Ratio: {stats['sharpe_ratio'].sharperatio:.3f}")
        if 'sqn' in stats and stats['sqn']:
             print(f"SQN: {stats['sqn'].sqn:.2f}")

        # PyFolio analyzer results are complex, usually used for plotting
        # print("\nPyFolio Analyzer Results:")
        # print(stats.get('pyfolio'))
    else:
        print("Backtest execution failed.")


