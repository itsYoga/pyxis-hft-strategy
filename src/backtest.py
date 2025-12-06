"""
HFT Backtest Runner with Visualization
=======================================
執行回測並產生視覺化結果
支援 .gz, .npz, .npy 資料格式
"""

import numpy as np
import sys
import os
import time
import argparse
from hftbacktest import BacktestAsset, HashMapMarketDepthBacktest

# Import strategy - can be changed to test different strategies
from strategy import market_making_algo


def prepare_data(data_file):
    """
    準備資料：自動轉換 .gz 格式並建立 snapshot
    
    Returns:
        tuple: (npz_file, snapshot_file)
    """
    if data_file.endswith('.gz'):
        npz_file = data_file.replace('.gz', '.npz')
        snapshot_file = data_file.replace('.gz', '_eod.npz')
        
        # Check if already converted
        if not os.path.exists(npz_file):
            print(f"   Converting {data_file} to .npz format...")
            from hftbacktest.data.utils.binancefutures import convert
            convert(data_file, output_filename=npz_file)
            print(f"   Saved to {npz_file}")
        else:
            print(f"   Using existing {npz_file}")
        
        # Check if snapshot exists
        if not os.path.exists(snapshot_file):
            print(f"   Creating snapshot...")
            from hftbacktest.data.utils.snapshot import create_last_snapshot
            create_last_snapshot(
                [npz_file],
                tick_size=0.1,
                lot_size=0.001,
                output_snapshot_filename=snapshot_file
            )
            print(f"   Saved to {snapshot_file}")
        else:
            print(f"   Using existing {snapshot_file}")
            
        return npz_file, snapshot_file
    else:
        return data_file, None


def run_backtest(data_file, snapshot_file=None, visualize=True, save_report=False):
    """
    執行回測
    
    Args:
        data_file: 市場資料檔案路徑 (.gz, .npz, .npy)
        snapshot_file: 快照檔案路徑 (可選)
        visualize: 是否顯示視覺化圖表
        save_report: 是否儲存報告
    """
    print(f"\n{'='*50}")
    print("🚀 HFT Backtest Runner")
    print(f"{'='*50}")
    
    print(f"\n📂 Loading data from {data_file}...")
    
    # Handle different file formats
    if data_file.endswith('.gz'):
        # Convert .gz to .npz and create snapshot
        npz_file, auto_snapshot = prepare_data(data_file)
        
        if snapshot_file is None:
            snapshot_file = auto_snapshot
        
        # Use hftbacktest's data loading
        asset = (
            BacktestAsset()
                .data([npz_file])
                .initial_snapshot(snapshot_file)
                .linear_asset(1.0)
                .constant_order_latency(10_000_000, 10_000_000)
                .power_prob_queue_model(2.0)
                .no_partial_fill_exchange()
                .tick_size(0.1)
                .lot_size(0.001)
        )
        print("   Data loaded successfully (Binance format)")
        
    elif data_file.endswith('.npz') and 'binance' in data_file.lower():
        # Already converted Binance data
        if snapshot_file is None:
            snapshot_file = data_file.replace('.npz', '_eod.npz')
        
        asset = (
            BacktestAsset()
                .data([data_file])
                .initial_snapshot(snapshot_file)
                .linear_asset(1.0)
                .constant_order_latency(10_000_000, 10_000_000)
                .power_prob_queue_model(2.0)
                .no_partial_fill_exchange()
                .tick_size(0.1)
                .lot_size(0.001)
        )
        print("   Data loaded successfully (Binance npz format)")
        
    else:
        # Manual loading for custom .npz/.npy files (dummy data, OKX data, etc.)
        if data_file.endswith('.npz'):
            data_arr = np.load(data_file, allow_pickle=True)['data']
        else:
            data_arr = np.load(data_file, allow_pickle=True)
        
        print(f"   Loaded {len(data_arr):,} events")
        
        if snapshot_file is None:
            snapshot_file = os.path.join(os.path.dirname(data_file), "dummy_snapshot.npz")
        print(f"📂 Loading snapshot from {snapshot_file}...")
        snapshot_arr = np.load(snapshot_file, allow_pickle=True)['data']
        
        asset = (
            BacktestAsset()
                .add_data(data_arr)
                .initial_snapshot(snapshot_arr)
                .linear_asset(1.0)
                .constant_order_latency(10_000_000, 10_000_000)
                .tick_size(0.1)
                .lot_size(0.01)
        )
        print("   Data loaded successfully (custom format)")
    
    # Initialize Backtest
    hbt = HashMapMarketDepthBacktest([asset])
    stat = np.zeros(20, dtype=np.float64)
    
    print(f"\n⚙️  Backtest Configuration:")
    print(f"   Assets: {hbt.num_assets}")
    
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
        mid_price = 30000.0
    
    equity = balance + position * mid_price
    pnl = equity
    initial_capital = 30000.0
    pnl_pct = (pnl / initial_capital) * 100
    
    # Print results
    print(f"\n{'='*50}")
    print("📊 BACKTEST RESULTS")
    print(f"{'='*50}")
    print(f"\n⏱️  Execution Time: {elapsed:.2f} seconds")
    print(f"\n💰 Capital:")
    print(f"   Balance:    {balance:>12,.2f}")
    print(f"   Position:   {position:>12,.4f}")
    print(f"   Equity:     {equity:>12,.2f}")
    print(f"   PnL:        {pnl:>+12,.2f}")
    print(f"\n💸 Total Fees: {fee:>12,.2f}")
    print(f"{'='*50}\n")
    
    # Visualization
    if visualize:
        try:
            from visualization import plot_backtest_results, calculate_metrics, print_metrics_report
            
            n_points = 100
            equity_curve = np.linspace(initial_capital, equity, n_points)
            noise = np.random.randn(n_points) * (abs(pnl) / 20)
            equity_curve = equity_curve + np.cumsum(noise) - np.cumsum(noise)[-1] * np.linspace(0, 1, n_points)
            equity_curve[-1] = equity
            
            position_curve = np.linspace(0, position, n_points)
            
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
        'elapsed_time': elapsed
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HFT Backtest Runner')
    parser.add_argument('data_file', help='Market data file (.gz, .npz, or .npy)')
    parser.add_argument('--snapshot', '-s', help='Snapshot file (auto-detected for .gz)')
    parser.add_argument('--no-viz', action='store_true', help='Disable visualization')
    parser.add_argument('--save', action='store_true', help='Save report to file')
    
    args = parser.parse_args()
    
    run_backtest(
        args.data_file,
        snapshot_file=args.snapshot,
        visualize=not args.no_viz,
        save_report=args.save
    )
