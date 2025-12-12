"""
Strategy Comparison Test
========================
Compare baseline vs aggressive strategies.
"""

import numpy as np
import time
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hftbacktest import HashMapMarketDepthBacktest

# Import new modules
try:
    from .data_loader import create_asset, validate_data_file
    from .logger import setup_logger, get_logger
except ImportError:
    from data_loader import create_asset, validate_data_file
    from logger import setup_logger, get_logger

logger = get_logger(__name__)


def run_strategy(strategy_func, data_file, snapshot_file, strategy_name, backtest_config=None):
    """Run a strategy and return results"""
    
    try:
        # Validate data file
        validate_data_file(data_file)
        
        # Use default config if not provided
        if backtest_config is None:
            from config_loader import BacktestConfig
            backtest_config = BacktestConfig(
                tick_size=0.1,
                lot_size=0.001,
                contract_size=1.0,
                order_latency_ns=10_000_000,
                initial_capital=30000.0,
                queue_model="power_prob",
                queue_model_param=2.0,
                partial_fill=False
            )
        
        # Load data using unified loader
        asset = create_asset(
            data_file=data_file,
            snapshot_file=snapshot_file,
            tick_size=backtest_config.tick_size,
            lot_size=backtest_config.lot_size,
            order_latency_ns=backtest_config.order_latency_ns,
            queue_model=backtest_config.queue_model,
            queue_model_param=backtest_config.queue_model_param,
            partial_fill=backtest_config.partial_fill
        )
        
        hbt = HashMapMarketDepthBacktest([asset])
        stat = np.zeros(20, dtype=np.float64)
        
        logger.info(f"Running {strategy_name} strategy...")
        start_time = time.time()
        
        try:
            strategy_func(hbt, stat)
        except Exception as e:
            logger.error(f"Strategy {strategy_name} failed: {e}", exc_info=True)
            raise
        
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
            mid_price = backtest_config.initial_capital / 10.0
        
        equity_wo_fee = balance + position * mid_price * backtest_config.contract_size
        equity = equity_wo_fee - fee
        # PnL = current equity - initial capital
        pnl = equity - backtest_config.initial_capital
        
        return {
            'strategy': strategy_name,
            'balance': balance,
            'position': position,
            'fee': fee,
            'mid_price': mid_price,
            'equity_wo_fee': equity_wo_fee,
            'equity': equity,
            'pnl': pnl,
            'elapsed': elapsed
        }
        
    except Exception as e:
        logger.error(f"Failed to run strategy {strategy_name}: {e}", exc_info=True)
        raise


def print_comparison(baseline_result, aggressive_result):
    """Print comparison report"""
    
    baseline_pnl = baseline_result['pnl']
    aggressive_pnl = aggressive_result['pnl']
    
    if baseline_pnl != 0:
        improvement = (aggressive_pnl - baseline_pnl) / abs(baseline_pnl) * 100
    else:
        improvement = 0 if aggressive_pnl == 0 else float('inf')
    
    winner = "Aggressive" if aggressive_pnl > baseline_pnl else "Baseline"
    
    logger.info("\n" + "=" * 60)
    logger.info("STRATEGY COMPARISON REPORT")
    logger.info("=" * 60)
    
    logger.info("\n" + "-" * 60)
    logger.info("BASELINE (Original - Level 1 Only)")
    logger.info("-" * 60)
    logger.info(f"   Balance:      {baseline_result['balance']:>15,.2f}")
    logger.info(f"   Position:     {baseline_result['position']:>15,.4f}")
    logger.info(f"   Equity:       {baseline_result['equity']:>15,.2f}")
    logger.info(f"   PnL:          {baseline_result['pnl']:>+15,.2f}")
    logger.info(f"   Time:         {baseline_result['elapsed']:>15.2f}s")
    
    logger.info("\n" + "-" * 60)
    logger.info("AGGRESSIVE (Multi-Level OFI + Regime Detection)")
    logger.info("-" * 60)
    logger.info(f"   Balance:      {aggressive_result['balance']:>15,.2f}")
    logger.info(f"   Position:     {aggressive_result['position']:>15,.4f}")
    logger.info(f"   Equity:       {aggressive_result['equity']:>15,.2f}")
    logger.info(f"   PnL:          {aggressive_result['pnl']:>+15,.2f}")
    logger.info(f"   Time:         {aggressive_result['elapsed']:>15.2f}s")
    
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"   Baseline PnL:     {baseline_pnl:>+15,.2f}")
    logger.info(f"   Aggressive PnL:   {aggressive_pnl:>+15,.2f}")
    logger.info(f"   Difference:       {aggressive_pnl - baseline_pnl:>+15,.2f}")
    logger.info(f"   Improvement:      {improvement:>+14.2f}%")
    logger.info(f"   Winner:           {winner:>15}")
    logger.info("=" * 60)
    
    return {
        'baseline_pnl': baseline_pnl,
        'aggressive_pnl': aggressive_pnl,
        'difference': aggressive_pnl - baseline_pnl,
        'improvement_pct': improvement,
        'winner': winner
    }


def main():
    # Check for data files
    data_files = [
        ("../data/binance_usdm/btcusdt_20240808.npz", "../data/binance_usdm/btcusdt_20240808_eod.npz", "Binance BTCUSDT 2024-08-08"),
        ("../data/binance_usdm/btcusdt_20240809.npz", "../data/binance_usdm/btcusdt_20240809_eod.npz", "Binance BTCUSDT 2024-08-09"),
        ("dummy_data.npy", "dummy_snapshot.npz", "Dummy Data"),
    ]
    
    # Find available data
    available_data = None
    for data_file, snapshot_file, name in data_files:
        full_data_path = os.path.join(os.path.dirname(__file__), data_file)
        full_snapshot_path = os.path.join(os.path.dirname(__file__), snapshot_file)
        
        if os.path.exists(full_data_path) and os.path.exists(full_snapshot_path):
            available_data = (full_data_path, full_snapshot_path, name)
            break
    
    if available_data is None:
        logger.error("Error: No data files found!")
        return
    
    data_file, snapshot_file, data_name = available_data
    logger.info(f"\nUsing data: {data_name}")
    logger.info(f"File: {data_file}")
    
    # Load backtest config
    try:
        from config_loader import load_config
        _, backtest_config, _ = load_config()
    except FileNotFoundError:
        logger.warning("Config file not found, using defaults")
        backtest_config = None
    
    # Import strategies
    from strategy_baseline import market_making_algo as baseline_algo
    from strategy import market_making_algo as aggressive_algo
    
    # Run baseline
    logger.info("\nRunning Baseline strategy...")
    baseline_result = run_strategy(baseline_algo, data_file, snapshot_file, "Baseline", backtest_config)
    
    # Run aggressive
    logger.info("Running Aggressive strategy...")
    aggressive_result = run_strategy(aggressive_algo, data_file, snapshot_file, "Aggressive", backtest_config)
    
    # Compare
    summary = print_comparison(baseline_result, aggressive_result)
    
    return summary


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Comparison interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        sys.exit(1)
