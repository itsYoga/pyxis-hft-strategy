"""
Strategy Comparison Test
========================
Compare baseline (Level 1 only) vs HA3 (MLOFI + Slope + Regime) strategies.
"""

import numpy as np
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hftbacktest import BacktestAsset, HashMapMarketDepthBacktest


def run_strategy(strategy_func, data_file, snapshot_file, strategy_name):
    """Run a strategy and return results"""
    
    # Load data
    if data_file.endswith('.npz') and 'binance' in data_file.lower():
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
    else:
        data_arr = np.load(data_file, allow_pickle=True)
        if data_file.endswith('.npz'):
            data_arr = data_arr['data']
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
    
    hbt = HashMapMarketDepthBacktest([asset])
    stat = np.zeros(20, dtype=np.float64)
    
    start_time = time.time()
    strategy_func(hbt, stat)
    elapsed = time.time() - start_time
    
    # Get results
    stat_val = hbt.state_values(0)
    balance = stat_val.balance
    position = stat_val.position
    fee = stat_val.fee
    
    depth = hbt.depth(0)
    if depth.best_bid > 0 and depth.best_ask > 0:
        mid_price = (depth.best_bid + depth.best_ask) / 2.0
    else:
        mid_price = 50000.0
    
    equity_wo_fee = balance + position * mid_price
    equity = equity_wo_fee - fee
    
    return {
        'strategy': strategy_name,
        'balance': balance,
        'position': position,
        'fee': fee,
        'mid_price': mid_price,
        'equity_wo_fee': equity_wo_fee,
        'equity': equity,
        'pnl': equity,
        'elapsed': elapsed
    }


def print_comparison(baseline_result, ha3_result):
    """Print comparison report"""
    
    baseline_pnl = baseline_result['pnl']
    ha3_pnl = ha3_result['pnl']
    
    if baseline_pnl != 0:
        improvement = (ha3_pnl - baseline_pnl) / abs(baseline_pnl) * 100
    else:
        improvement = 0 if ha3_pnl == 0 else float('inf')
    
    winner = "HA3" if ha3_pnl > baseline_pnl else "Baseline"
    
    print("\n" + "=" * 60)
    print("STRATEGY COMPARISON REPORT")
    print("=" * 60)
    
    print("\n" + "-" * 60)
    print("BASELINE (Original - Level 1 Only)")
    print("-" * 60)
    print(f"   Balance:      {baseline_result['balance']:>15,.2f}")
    print(f"   Position:     {baseline_result['position']:>15,.4f}")
    print(f"   Equity:       {baseline_result['equity']:>15,.2f}")
    print(f"   PnL:          {baseline_result['pnl']:>+15,.2f}")
    print(f"   Time:         {baseline_result['elapsed']:>15.2f}s")
    
    print("\n" + "-" * 60)
    print("HA3 (MLOFI + LOB Slope + Regime Detection)")
    print("-" * 60)
    print(f"   Balance:      {ha3_result['balance']:>15,.2f}")
    print(f"   Position:     {ha3_result['position']:>15,.4f}")
    print(f"   Equity:       {ha3_result['equity']:>15,.2f}")
    print(f"   PnL:          {ha3_result['pnl']:>+15,.2f}")
    print(f"   Time:         {ha3_result['elapsed']:>15.2f}s")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"   Baseline PnL:     {baseline_pnl:>+15,.2f}")
    print(f"   HA3 PnL:          {ha3_pnl:>+15,.2f}")
    print(f"   Difference:       {ha3_pnl - baseline_pnl:>+15,.2f}")
    print(f"   Improvement:      {improvement:>+14.2f}%")
    print(f"   Winner:           {winner:>15}")
    print("=" * 60)
    
    return {
        'baseline_pnl': baseline_pnl,
        'ha3_pnl': ha3_pnl,
        'difference': ha3_pnl - baseline_pnl,
        'improvement_pct': improvement,
        'winner': winner
    }


def main():
    # Check for data files
    data_files = [
        ("data/binance_usdm/btcusdt_20240808.npz", "data/binance_usdm/btcusdt_20240808_eod.npz", "Binance BTCUSDT 2024-08-08"),
        ("data/binance_usdm/btcusdt_20240809.npz", "data/binance_usdm/btcusdt_20240809_eod.npz", "Binance BTCUSDT 2024-08-09"),
        ("src/dummy_data.npy", "src/dummy_snapshot.npz", "Dummy Data"),
    ]
    
    # Find available data
    available_data = None
    for data_file, snapshot_file, name in data_files:
        if os.path.exists(data_file) and os.path.exists(snapshot_file):
            available_data = (data_file, snapshot_file, name)
            break
    
    if available_data is None:
        print("Error: No data files found!")
        return
    
    data_file, snapshot_file, data_name = available_data
    print(f"\nUsing data: {data_name}")
    print(f"File: {data_file}")
    
    # Import strategies
    from strategy_baseline import market_making_algo as baseline_algo
    from strategy import market_making_algo as ha3_algo
    
    # Run baseline
    print("\nRunning Baseline strategy...")
    baseline_result = run_strategy(baseline_algo, data_file, snapshot_file, "Baseline")
    
    # Run HA3
    print("Running HA3 strategy...")
    ha3_result = run_strategy(ha3_algo, data_file, snapshot_file, "HA3")
    
    # Compare
    summary = print_comparison(baseline_result, ha3_result)
    
    return summary


if __name__ == '__main__':
    main()
