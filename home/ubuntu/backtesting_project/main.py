# /home/ubuntu/backtesting_project/main.py

import os
import sys
import argparse
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.backtester import run_backtest
from core.reporting import generate_html_report, plot_results, ensure_report_dir

def main():
    parser = argparse.ArgumentParser(description="Cryptocurrency Backtesting Engine")

    # --- Data Arguments ---
    parser.add_argument("--data", required=True, help="Path to the CSV data file (e.g., data/BTCUSDT_1h.csv)")
    parser.add_argument("--symbol", required=True, help="Trading pair symbol (e.g., BTCUSDT)")
    parser.add_argument("--timeframe", required=True, help="Data timeframe (e.g., 1m, 5m, 1h, 1d)")
    parser.add_argument("--fromdate", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--todate", required=True, help="End date (YYYY-MM-DD)")

    # --- Strategy Arguments ---
    parser.add_argument("--strategy-module", default="base_strategy", help="Module containing the strategy class (e.g., base_strategy, user_strategy)")
    parser.add_argument("--strategy", required=True, help="Name of the strategy class to run")
    # Strategy parameters are handled loosely here; a config file might be better for complex params
    parser.add_argument("--strategy-params", nargs=\'*\', help="Strategy parameters as key=value pairs (e.g., fast_ma_period=10 slow_ma_period=50)")

    # --- Backtest Engine Arguments ---
    parser.add_argument("--cash", type=float, default=10000.0, help="Initial portfolio cash")
    parser.add_argument("--commission", type=float, default=0.001, help="Commission per trade (e.g., 0.001 for 0.1%)")

    # --- Slippage/Spread Arguments ---
    parser.add_argument("--spread", type=float, default=0.0001, help="Fixed spread fraction (e.g., 0.0001 for 0.01%)")
    parser.add_argument("--volume-impact", type=float, default=0.1, help="Volume impact factor for slippage")
    parser.add_argument("--min-delay", type=int, default=5, help="Min execution delay (ms)")
    parser.add_argument("--max-delay", type=int, default=50, help="Max execution delay (ms)")

    # --- Output Arguments ---
    parser.add_argument("--plot", action="store_true", help="Generate Backtrader plot")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--output-dir", default="reports", help="Directory to save plots and reports")

    args = parser.parse_args()

    # --- Prepare Configuration ---
    strategy_params_dict = {}
    if args.strategy_params:
        for param in args.strategy_params:
            try:
                key, value = param.split("=")
                # Attempt to convert value to float or int if possible
                try:
                    value = float(value)
                    if value.is_integer():
                        value = int(value)
                except ValueError:
                    pass # Keep as string if conversion fails
                strategy_params_dict[key] = value
            except ValueError:
                print(f"Warning: Could not parse strategy parameter 	{param}	. Expected format: key=value")

    config = {
        "data_path": args.data,
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "start_date": args.fromdate,
        "end_date": args.todate,
        "strategy_module": args.strategy_module,
        "strategy_name": args.strategy,
        "strategy_params": strategy_params_dict,
        "initial_cash": args.cash,
        "commission": args.commission,
        "slippage_params": {
            "fixed_spread": args.spread,
            "volume_impact_factor": args.volume_impact,
            "min_delay_ms": args.min_delay,
            "max_delay_ms": args.max_delay
        }
    }

    # --- Run Backtest ---
    cerebro, results, stats = run_backtest(config)

    # --- Generate Outputs ---
    if results and stats:
        print("\n--- Backtest Run Summary ---")
        final_value = results[0].broker.getvalue()
        print(f"Initial Portfolio Value: {config["initial_cash"]:,.2f}")
        print(f"Final Portfolio Value:   {final_value:,.2f}")
        pnl = final_value - config["initial_cash"]
        print(f"Net Profit/Loss:       {pnl:,.2f}")

        # Create unique output filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{args.symbol}_{args.strategy}_{args.timeframe}_{timestamp}"
        report_dir = os.path.join(project_root, args.output_dir)
        ensure_report_dir(report_dir)

        if args.plot:
            plot_filename = os.path.join(report_dir, f"{base_filename}_plot.png")
            plot_results(cerebro, results, plot_filename)

        if args.report:
            report_filename = os.path.join(report_dir, f"{base_filename}_report.html")
            report_title = f"{args.symbol} | {args.strategy} ({args.timeframe}) | {args.fromdate} to {args.todate}"
            generate_html_report(stats, report_filename, title=report_title)

        print(f"\nOutputs generated in: {report_dir}")

    else:
        print("Backtest failed to produce results. No reports generated.")

if __name__ == "__main__":
    main()


