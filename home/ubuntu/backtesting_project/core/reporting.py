# /home/ubuntu/backtesting_project/core/reporting.py

import backtrader as bt
import quantstats as qs
import pandas as pd
import os
import matplotlib

# Set Matplotlib backend to Agg to avoid GUI requirement in headless environment
matplotlib.use("Agg")
import matplotlib.pyplot as plt # Import after setting backend

# Ensure reports directory exists
def ensure_report_dir(report_dir):
    os.makedirs(report_dir, exist_ok=True)

def generate_html_report(stats, report_file_path, title="Strategy Backtest Report"):
    """
    Generates an HTML performance report using QuantStats.

    Args:
        stats (dict): Dictionary of analyzer results from Cerebro, must include 'pyfolio'.
        report_file_path (str): Full path to save the HTML report.
        title (str): Title for the report.
    """
    if 'pyfolio' not in stats or not stats['pyfolio']:
        print("Error: PyFolio analyzer results not found or empty. Cannot generate HTML report.")
        return

    try:
        # PyFolio analyzer returns a dictionary. We need the 'returns' series.
        pyfolio_results = stats['pyfolio']
        # The returns are typically under the key 'returns'
        returns_analyzer = pyfolio_results.get('returns')

        if returns_analyzer is None or not isinstance(returns_analyzer, dict):
             print("Error: Could not find 'returns' dictionary within PyFolio results.")
             # Attempt to find returns from the 'returns' analyzer if pyfolio structure is different
             if 'returns' in stats and stats['returns']:
                 print("Trying 'returns' analyzer directly...")
                 returns_dict = stats['returns']
                 # Convert dict to Series, assuming keys are dates and values are returns
                 returns_series = pd.Series(returns_dict).sort_index()
             else:
                 print("No suitable returns data found.")
                 return
        else:
            # Convert the returns dictionary from PyFolio to a pandas Series
            # The keys are datetime objects, values are the daily returns
            returns_series = pd.Series(returns_analyzer).sort_index()

        if returns_series.empty:
            print("Error: Returns series is empty. Cannot generate report.")
            return

        # Ensure the index is timezone-naive, QuantStats might require this
        if returns_series.index.tz is not None:
            returns_series.index = returns_series.index.tz_localize(None)

        print(f"Generating QuantStats HTML report to: {report_file_path}")
        # Use quantstats to generate the report
        qs.reports.html(returns_series, output=report_file_path, title=title)
        print("HTML report generated successfully.")

    except KeyError as e:
        print(f"Error accessing PyFolio results key: {e}. Check analyzer structure.")
    except Exception as e:
        print(f"An unexpected error occurred during HTML report generation: {e}")

def plot_results(cerebro, results, plot_file_path, **kwargs):
    """
    Generates and saves the standard Backtrader plot.

    Args:
        cerebro (bt.Cerebro): The Cerebro engine instance after running.
        results (list): The list returned by cerebro.run().
        plot_file_path (str): Full path to save the plot image.
        **kwargs: Additional arguments passed to cerebro.plot().
    """
    if not results:
        print("No results to plot.")
        return

    try:
        print(f"Generating Backtrader plot to: {plot_file_path}")
        # Use style='candlestick' or other styles as needed
        figure = cerebro.plot(style='line', volume=True, iplot=False, savefig=True, figfilename=plot_file_path, **kwargs)[0][0]
        # figure.savefig(plot_file_path, dpi=300) # cerebro.plot handles saving with savefig=True
        plt.close(figure) # Close the figure to free memory
        print("Backtrader plot saved successfully.")
    except Exception as e:
        print(f"An error occurred during plot generation: {e}")

# Example usage (for testing purposes)
if __name__ == '__main__':
    # This part requires running a backtest first to get stats
    # We'll simulate some dummy stats for testing the report generation
    print("Testing reporting functions (requires dummy data)...")
    report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))
    ensure_report_dir(report_dir)

    # Dummy returns data (replace with actual backtest results)
    dates = pd.date_range('2022-01-01', '2022-12-31', freq='D')
    dummy_returns = pd.Series(pd.np.random.randn(len(dates)) * 0.01, index=dates)
    dummy_stats = {
        'pyfolio': {
            'returns': dummy_returns.to_dict()
        }
        # Add other dummy analyzer results if needed for testing plot
    }

    html_report_path = os.path.join(report_dir, 'test_report.html')
    generate_html_report(dummy_stats, html_report_path, title="Test Strategy Report")

    # Plotting requires a Cerebro instance and results, harder to fake
    # print("Plotting test skipped as it requires a full Cerebro run.")


