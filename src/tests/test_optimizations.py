"""
Optimization Testing Script
============================
測試策略優化的效果

比較：
1. Baseline (原始策略)
2. Aggressive (優化前 - 關閉所有新優化)
3. Aggressive Optimized (優化後 - 啟用所有新優化)
"""

import numpy as np
import time
import sys
import os
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hftbacktest import HashMapMarketDepthBacktest

# Import modules
try:
    from ..core.data_loader import create_asset, validate_data_file
    from ..utils.logger import setup_logger, get_logger
    from ..core.config_loader import load_config, BacktestConfig
except ImportError:
    from core.data_loader import create_asset, validate_data_file
    from utils.logger import setup_logger, get_logger
    from core.config_loader import load_config, BacktestConfig

logger = get_logger(__name__)


def run_strategy_with_config(strategy_func, data_file, snapshot_file, strategy_name, 
                             backtest_config=None, enable_optimizations=True):
    """
    運行策略並返回結果
    
    Args:
        strategy_func: 策略函數
        data_file: 數據文件路徑
        snapshot_file: 快照文件路徑
        strategy_name: 策略名稱
        backtest_config: 回測配置
        enable_optimizations: 是否啟用優化（用於測試）
    """
    try:
        # Validate data file
        validate_data_file(data_file)
        
        # Use default config if not provided
        if backtest_config is None:
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
        
        # Load data
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
        
        logger.info(f"Running {strategy_name}...")
        start_time = time.time()
        
        # 如果策略支持優化開關，可以通過 stat 傳遞
        # 這裡我們直接運行策略函數
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
            mid_price = backtest_config.initial_capital / 10.0
        
        equity_wo_fee = balance + position * mid_price * backtest_config.contract_size
        equity = equity_wo_fee - fee
        pnl = equity - backtest_config.initial_capital
        
        # Calculate additional metrics
        max_position = abs(position)  # Simplified - would need tracking
        
        return {
            'strategy': strategy_name,
            'balance': balance,
            'position': position,
            'fee': fee,
            'mid_price': mid_price,
            'equity_wo_fee': equity_wo_fee,
            'equity': equity,
            'pnl': pnl,
            'elapsed': elapsed,
            'max_position': max_position
        }
        
    except Exception as e:
        logger.error(f"Failed to run strategy {strategy_name}: {e}", exc_info=True)
        raise


def create_pre_optimization_strategy():
    """
    創建優化前的策略版本（關閉所有新優化）
    這需要修改 aggressive.py 中的參數
    """
    # 注意：這需要在 aggressive.py 中臨時修改參數
    # 或者創建一個副本
    from strategies.aggressive import market_making_algo
    return market_making_algo


def print_optimization_comparison(results: List[Dict]):
    """打印優化對比報告"""
    
    print("\n" + "="*70)
    print("OPTIMIZATION COMPARISON REPORT")
    print("="*70)
    
    # 找出三個策略的結果
    baseline = next((r for r in results if 'Baseline' in r['strategy']), None)
    pre_opt = next((r for r in results if 'Pre-Optimization' in r['strategy']), None)
    optimized = next((r for r in results if 'Optimized' in r['strategy']), None)
    
    if not all([baseline, optimized]):
        logger.error("Missing required strategy results")
        return
    
    # 打印詳細結果
    strategies = [baseline]
    if pre_opt:
        strategies.append(pre_opt)
    strategies.append(optimized)
    
    print(f"\n{'Strategy':<20} {'PnL':>15} {'Fee':>15} {'Max Pos':>12} {'Time':>10}")
    print("-"*70)
    
    for r in strategies:
        print(f"{r['strategy']:<20} {r['pnl']:>15.2f} {r['fee']:>15.2f} "
              f"{r['max_position']:>12.2f} {r['elapsed']:>10.2f}s")
    
    # 計算改進
    print("\n" + "="*70)
    print("IMPROVEMENT ANALYSIS")
    print("="*70)
    
    # Baseline vs Optimized
    pnl_improvement = optimized['pnl'] - baseline['pnl']
    pnl_improvement_pct = (pnl_improvement / abs(baseline['pnl'])) * 100 if baseline['pnl'] != 0 else 0
    
    print(f"\nBaseline → Optimized:")
    print(f"  PnL Improvement: {pnl_improvement:+.2f} ({pnl_improvement_pct:+.2f}%)")
    print(f"  Fee Change: {optimized['fee'] - baseline['fee']:+.2f}")
    print(f"  Max Position: {optimized['max_position']:.2f} vs {baseline['max_position']:.2f}")
    
    if pre_opt:
        # Pre-Optimization vs Optimized
        pnl_improvement_pre = optimized['pnl'] - pre_opt['pnl']
        pnl_improvement_pre_pct = (pnl_improvement_pre / abs(pre_opt['pnl'])) * 100 if pre_opt['pnl'] != 0 else 0
        
        print(f"\nPre-Optimization → Optimized:")
        print(f"  PnL Improvement: {pnl_improvement_pre:+.2f} ({pnl_improvement_pre_pct:+.2f}%)")
        print(f"  Fee Change: {optimized['fee'] - pre_opt['fee']:+.2f}")
    
    # 判斷優勝者
    winner = max(strategies, key=lambda x: x['pnl'])
    print(f"\n{'='*70}")
    print(f"Winner: {winner['strategy']} (PnL: {winner['pnl']:+.2f})")
    print("="*70)
    
    return {
        'baseline_pnl': baseline['pnl'],
        'optimized_pnl': optimized['pnl'],
        'improvement': pnl_improvement,
        'improvement_pct': pnl_improvement_pct,
        'winner': winner['strategy']
    }


def main():
    """主測試函數"""
    
    # 查找數據文件
    data_files = [
        ("data/binance_usdm/btcusdt_20240808.npz", "data/binance_usdm/btcusdt_20240808_eod.npz", "Binance BTCUSDT 2024-08-08"),
        ("data/binance_usdm/btcusdt_20240809.npz", "data/binance_usdm/btcusdt_20240809_eod.npz", "Binance BTCUSDT 2024-08-09"),
        ("data/dummy_data.npy", "data/dummy_snapshot.npz", "Dummy Data"),
    ]
    
    # 找到可用的數據
    available_data = None
    for data_file, snapshot_file, name in data_files:
        full_data_path = Path(__file__).parent.parent.parent / data_file
        full_snapshot_path = Path(__file__).parent.parent.parent / snapshot_file
        
        if full_data_path.exists() and full_snapshot_path.exists():
            available_data = (str(full_data_path), str(full_snapshot_path), name)
            break
    
    if available_data is None:
        logger.error("Error: No data files found!")
        logger.info("Please ensure data files exist in the data/ directory")
        return
    
    data_file, snapshot_file, data_name = available_data
    logger.info(f"\nUsing data: {data_name}")
    logger.info(f"Data file: {data_file}")
    logger.info(f"Snapshot file: {snapshot_file}")
    
    # Load backtest config
    try:
        _, backtest_config, _ = load_config()
    except FileNotFoundError:
        logger.warning("Config file not found, using defaults")
        backtest_config = None
    
    # Import strategies
    from strategies.baseline import market_making_algo as baseline_algo
    from strategies.aggressive import market_making_algo as aggressive_algo
    
    results = []
    
    # 1. Run Baseline
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Baseline Strategy")
    logger.info("="*70)
    baseline_result = run_strategy_with_config(
        baseline_algo, data_file, snapshot_file, "Baseline", backtest_config
    )
    results.append(baseline_result)
    
    # 2. Run Aggressive (當前版本，已包含優化)
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Aggressive Strategy (Optimized)")
    logger.info("="*70)
    optimized_result = run_strategy_with_config(
        aggressive_algo, data_file, snapshot_file, "Aggressive Optimized", backtest_config
    )
    results.append(optimized_result)
    
    # 3. Print comparison
    summary = print_optimization_comparison(results)
    
    # 4. 建議
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    if summary['improvement'] > 0:
        print(f"[OK] Optimizations improved PnL by {summary['improvement']:.2f} ({summary['improvement_pct']:.2f}%)")
        print("[OK] Consider keeping all optimizations enabled")
    else:
        print(f"[WARN] Optimizations reduced PnL by {abs(summary['improvement']):.2f} ({abs(summary['improvement_pct']):.2f}%)")
        print("[WARN] Consider:")
        print("   - Testing individual optimizations separately")
        print("   - Adjusting optimization parameters")
        print("   - Testing on different datasets")
    
    print("\nNext steps:")
    print("1. Test on multiple datasets to verify consistency")
    print("2. Analyze inventory distribution and spread behavior")
    print("3. Check fill rates and trade frequency")
    print("4. Consider A/B testing individual optimizations")
    
    return summary


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

