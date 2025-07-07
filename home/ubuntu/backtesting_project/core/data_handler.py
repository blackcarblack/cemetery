# /home/ubuntu/backtesting_project/core/data_handler.py

import backtrader as bt
import pandas as pd
from datetime import datetime

class CustomCSVData(bt.feeds.GenericCSVData):
    """Custom CSV Data Feed that includes specific parameters."""
    params = (
        ("dtformat", "%Y-%m-%d %H:%M:%S"),  # Standard datetime format, adjust if needed
        ("datetime", 0),
        ("open", 1),
        ("high", 2),
        ("low", 3),
        ("close", 4),
        ("volume", 5),
        ("openinterest", -1)  # -1 indicates column is not present
    )

def load_data(data_path, symbol, timeframe, start_date_str, end_date_str):
    """
    Loads historical data from a CSV file for a specific symbol and timeframe,
    filtering by date range.

    Args:
        data_path (str): Path to the CSV file.
        symbol (str): The trading pair symbol (e.g., 'BTCUSDT'). Used for potential future logic,
                      currently assumes the CSV contains data for the desired symbol.
        timeframe (str): The timeframe of the data (e.g., '1h', '1d'). Backtrader handles this.
        start_date_str (str): Start date in 'YYYY-MM-DD' format.
        end_date_str (str): End date in 'YYYY-MM-DD' format.

    Returns:
        bt.feeds.GenericCSVData: Backtrader data feed object or None if error.
    """
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # Basic validation for date format in CSV can be added here if needed
        # For now, we rely on Backtrader's parsing

        data_feed = CustomCSVData(
            dataname=data_path,
            fromdate=start_date,
            todate=end_date,
            timeframe=bt.TimeFrame.TFrame(timeframe), # Convert string timeframe
            # Add other parameters if your CSV has a different structure
        )
        print(f"Data loaded successfully for {symbol} from {start_date_str} to {end_date_str}")
        return data_feed

    except FileNotFoundError:
        print(f"Error: Data file not found at {data_path}")
        return None
    except ValueError as e:
        print(f"Error parsing dates or data: {e}")
        print("Ensure start/end dates are YYYY-MM-DD and CSV format is correct.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during data loading: {e}")
        return None

# Example usage (for testing purposes, will be called from main.py later)
if __name__ == '__main__':
    # Create a dummy CSV for testing
    dummy_data = {
        'Date': pd.to_datetime(['2023-01-01 00:00:00', '2023-01-01 01:00:00', '2023-01-02 00:00:00', '2023-01-03 00:00:00']),
        'Open': [100, 101, 105, 108],
        'High': [102, 103, 106, 110],
        'Low': [99, 100, 104, 107],
        'Close': [101, 102, 105.5, 109],
        'Volume': [1000, 1200, 1100, 1300]
    }
    df = pd.DataFrame(dummy_data)
    test_csv_path = '../data/test_data.csv' # Relative path for testing within core dir
    df.to_csv(test_csv_path, index=False)

    print(f"Created dummy data file: {test_csv_path}")

    # Test loading the data
    feed = load_data(test_csv_path, 'TESTBTC', 'Hours', '2023-01-01', '2023-01-02')

    if feed:
        print("Data feed created successfully.")
        # You could add a simple cerebro run here to verify the feed loads
    else:
        print("Failed to create data feed.")


