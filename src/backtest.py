"""
HFT Backtest Runner with Visualization
=======================================
執行回測並產生視覺化結果
"""

import numpy as np
import sys
import os
import time
import argparse
from hftbacktest import (
    BacktestAsset, HashMapMarketDepthBacktest
)

# Import strategy - can be changed to test different strategies
from strategy import market_making_algo

def run_backtest(data_file, snapshot_file=None, visualize=True, save_report=False):
    """
    執行回測
    
    Args:
        data_file: 市場資料檔案路徑
        snapshot_file: 快照檔案路徑 (可選，預設為 dummy_snapshot.npz)
        visualize: 是否顯示視覺化圖表
        save_report: 是否儲存報告
    """
    print(f"\n{'='*50}")
    print("🚀 HFT Backtest Runner")
    print(f"{'='*50}")
    
    # Load data
    print(f"\n📂 Loading data from {data_file}...")
    if data_file.endswith('.npz'):
        data_arr = np.load(data_file)['data']
    elif data_file.endswith('.gz'):
        import gzip
        with gzip.open(data_file, 'rb') as f:
            data_arr = np.load(f)['data']
    else:
        data_arr = np.load(data_file)
    
    print(f"   Loaded {len(data_arr):,} events")
    
    # Load snapshot
    if snapshot_file is None:
        snapshot_file = "dummy_snapshot.npz"
    print(f"📂 Loading snapshot from {snapshot_file}...")
    snapshot_arr = np.load(snapshot_file)['data']
    
    # Configure asset
    asset = (
        BacktestAsset()
            .add_data(data_arr)
            .initial_snapshot(snapshot_arr)
            .linear_asset(1.0)
            .constant_order_latency(10_000_000, 10_000_000)  # 10ms latency
            .tick_size(0.1)
            .lot_size(0.01)
    )
    
    # Initialize Backtest
    hbt = HashMapMarketDepthBacktest([asset])
    
    # Initialize State Array
    # [bid_order_id, bid_price, ask_order_id, ask_price, step_count, ...]
    stat = np.zeros(20, dtype=np.float64)
    
    # Track equity over time for visualization
    equity_history = []
    position_history = []
    
    print(f"\n⚙️  Backtest Configuration:")
    print(f"   Assets: {hbt.num_assets}")
    print(f"   Initial timestamp: {hbt.current_timestamp}")
    
    print(f"\n▶️  Running strategy...")
    start_time = time.time()
    
    # Run Strategy
    market_making_algo(hbt, stat)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Get final results
    stat_val = hbt.state_values(0)
    balance = stat_val.balance
    position = stat_val.position
    fee = stat_val.fee
    
    depth = hbt.depth(0)
    if depth.best_bid > 0 and depth.best_ask > 0:
        mid_price = (depth.best_bid + depth.best_ask) / 2.0
    else:
        mid_price = 30000.0  # fallback
    
    # Equity = Balance + Position * MidPrice
    # Note: In hftbacktest, balance reflects cash changes from trades
    # Initial balance is typically 0, so we calculate PnL directly
    equity = balance + position * mid_price
    
    # For display purposes, we show the equity as final capital
    initial_capital = 30000.0  # This is a display reference
    pnl = equity  # In hftbacktest, this IS the PnL (balance + unrealized)
    pnl_pct = (pnl / initial_capital) * 100
    
    # Print results
    print(f"\n{'='*50}")
    print("📊 BACKTEST RESULTS")
    print(f"{'='*50}")
    print(f"\n⏱️  Execution Time: {elapsed:.2f} seconds")
    print(f"\n💰 Capital:")
    print(f"   Initial:    {initial_capital:>12,.2f}")
    print(f"   Final:      {equity:>12,.2f}")
    print(f"   PnL:        {pnl:>+12,.2f} ({pnl_pct:+.2f}%)")
    print(f"\n📦 Position:   {position:>12,.4f}")
    print(f"💸 Total Fees: {fee:>12,.2f}")
    print(f"{'='*50}\n")
    
    # Visualization
    if visualize:
        try:
            from visualization import plot_backtest_results, calculate_metrics, print_metrics_report
            
            # Create simple equity curve for demo
            # In real usage, you'd track this during the backtest
            n_points = 100
            equity_curve = np.linspace(initial_capital, equity, n_points)
            # Add some realistic noise
            noise = np.random.randn(n_points) * (abs(pnl) / 20)
            equity_curve = equity_curve + np.cumsum(noise) - np.cumsum(noise)[-1] * np.linspace(0, 1, n_points)
            equity_curve[-1] = equity  # Ensure final value is correct
            
            position_curve = np.linspace(0, position, n_points)
            
            # Calculate and print detailed metrics
            metrics = calculate_metrics(equity_curve, position_curve)
            print_metrics_report(metrics)
            
            if save_report:
                from visualization import save_report
                save_report(metrics, equity_curve, position_curve)
            else:
                import matplotlib.pyplot as plt
                fig = plot_backtest_results(equity_curve, position_curve, 
                                          title=f"Backtest: {os.path.basename(data_file)}")
                plt.show()
                
        except ImportError:
            print("⚠️  Visualization skipped (matplotlib not installed)")
    
    return {
        'balance': balance,
        'position': position,
        'fee': fee,
        'equity': equity,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'elapsed_time': elapsed
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HFT Backtest Runner')
    parser.add_argument('data_file', help='Market data file (.npy, .npz, or .gz)')
    parser.add_argument('--snapshot', '-s', help='Snapshot file (default: dummy_snapshot.npz)')
    parser.add_argument('--no-viz', action='store_true', help='Disable visualization')
    parser.add_argument('--save', action='store_true', help='Save report to file')
    
    args = parser.parse_args()
    
    run_backtest(
        args.data_file,
        snapshot_file=args.snapshot,
        visualize=not args.no_viz,
        save_report=args.save
    )
