"""
參數掃描腳本
============

掃描不同參數組合，找出最優參數
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_loader import create_asset, validate_data_file
from core.config_loader import BacktestConfig
from utils.logger import get_logger
from hftbacktest import HashMapMarketDepthBacktest

logger = get_logger(__name__)


def run_strategy_with_params(
    strategy_func, 
    data_file, 
    snapshot_file, 
    k_base: float,
    gamma_base: float,
    max_position: float,
    backtest_config=None
):
    """運行策略並返回結果"""
    
    try:
        validate_data_file(data_file)
        
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
        
        # Store parameters in stat array for strategy to use
        stat[10] = k_base
        stat[11] = gamma_base
        stat[12] = max_position
        
        # Get initial state
        initial_stat_val = hbt.state_values(0)
        initial_balance = initial_stat_val.balance
        initial_position = initial_stat_val.position
        initial_fee = initial_stat_val.fee
        
        initial_depth = hbt.depth(0)
        if initial_depth.best_bid > 0 and initial_depth.best_ask > 0:
            initial_mid_price = (initial_depth.best_bid + initial_depth.best_ask) / 2.0
        else:
            initial_mid_price = backtest_config.initial_capital / 10.0
        
        initial_equity = initial_balance + initial_position * initial_mid_price * backtest_config.contract_size - initial_fee
        
        start_time = time.time()
        
        try:
            strategy_func(hbt, stat)
        except Exception as e:
            logger.error(f"Strategy failed with params k={k_base}, gamma={gamma_base}, max_pos={max_position}: {e}")
            return None
        
        elapsed = time.time() - start_time
        
        # Get final results
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
        pnl = equity - initial_equity
        
        return {
            'k_base': k_base,
            'gamma_base': gamma_base,
            'max_position': max_position,
            'pnl': pnl,
            'equity': equity,
            'balance': balance,
            'position': position,
            'fee': fee,
            'elapsed': elapsed
        }
        
    except Exception as e:
        logger.error(f"Failed with params k={k_base}, gamma={gamma_base}, max_pos={max_position}: {e}")
        return None


def parameter_sweep(
    strategy_func,
    data_file: str,
    snapshot_file: str,
    k_values: List[float] = [1.5, 2.0, 2.5, 3.0],
    gamma_values: List[float] = [0.05, 0.08, 0.10, 0.12],
    max_position_values: List[float] = [8.0, 10.0, 12.0],
    backtest_config=None
) -> List[Dict]:
    """
    參數掃描
    
    Args:
        strategy_func: 策略函數
        data_file: 數據文件路徑
        snapshot_file: 快照文件路徑
        k_values: k_base 參數值列表
        gamma_values: gamma_base 參數值列表
        max_position_values: max_position 參數值列表
        backtest_config: 回測配置
    
    Returns:
        結果列表，每個結果包含參數和性能指標
    """
    
    results = []
    total_combinations = len(k_values) * len(gamma_values) * len(max_position_values)
    current = 0
    
    logger.info(f"\n開始參數掃描...")
    logger.info(f"總組合數: {total_combinations}")
    logger.info(f"k_values: {k_values}")
    logger.info(f"gamma_values: {gamma_values}")
    logger.info(f"max_position_values: {max_position_values}")
    logger.info("")
    
    for k_base in k_values:
        for gamma_base in gamma_values:
            for max_position in max_position_values:
                current += 1
                logger.info(f"[{current}/{total_combinations}] Testing k={k_base:.2f}, gamma={gamma_base:.2f}, max_pos={max_position:.1f}...")
                
                result = run_strategy_with_params(
                    strategy_func,
                    data_file,
                    snapshot_file,
                    k_base,
                    gamma_base,
                    max_position,
                    backtest_config
                )
                
                if result:
                    results.append(result)
                    logger.info(f"  PnL: {result['pnl']:+,.2f}, Equity: {result['equity']:,.2f}")
                else:
                    logger.warning(f"  Failed to run with these parameters")
    
    return results


def find_best_parameters(results: List[Dict]) -> Tuple[Dict, Dict]:
    """
    找出最優參數
    
    Returns:
        (best_result, best_params)
    """
    
    if not results:
        return None, None
    
    # 按 PnL 排序
    sorted_results = sorted(results, key=lambda x: x['pnl'], reverse=True)
    best_result = sorted_results[0]
    
    best_params = {
        'k_base': best_result['k_base'],
        'gamma_base': best_result['gamma_base'],
        'max_position': best_result['max_position']
    }
    
    return best_result, best_params


def print_sweep_results(results: List[Dict]):
    """打印掃描結果"""
    
    if not results:
        logger.error("No results to display")
        return
    
    logger.info("\n" + "="*80)
    logger.info("PARAMETER SWEEP RESULTS")
    logger.info("="*80)
    
    # 排序結果
    sorted_results = sorted(results, key=lambda x: x['pnl'], reverse=True)
    
    # 顯示前 10 名
    logger.info("\nTop 10 Results:")
    logger.info("-"*80)
    logger.info(f"{'Rank':<6} {'k_base':<8} {'gamma_base':<12} {'max_pos':<10} {'PnL':<15} {'Equity':<15}")
    logger.info("-"*80)
    
    for i, result in enumerate(sorted_results[:10], 1):
        logger.info(
            f"{i:<6} {result['k_base']:<8.2f} {result['gamma_base']:<12.2f} "
            f"{result['max_position']:<10.1f} {result['pnl']:<+15,.2f} {result['equity']:<15,.2f}"
        )
    
    # 找出最優參數
    best_result, best_params = find_best_parameters(results)
    
    logger.info("\n" + "="*80)
    logger.info("BEST PARAMETERS")
    logger.info("="*80)
    logger.info(f"k_base:       {best_params['k_base']:.2f}")
    logger.info(f"gamma_base:    {best_params['gamma_base']:.2f}")
    logger.info(f"max_position:  {best_params['max_position']:.1f}")
    logger.info(f"\nPerformance:")
    logger.info(f"  PnL:         {best_result['pnl']:+,.2f}")
    logger.info(f"  Equity:      {best_result['equity']:,.2f}")
    logger.info(f"  Balance:     {best_result['balance']:,.2f}")
    logger.info(f"  Position:    {best_result['position']:,.4f}")
    logger.info(f"  Fee:         {best_result['fee']:,.2f}")
    logger.info("="*80)


def save_results(results: List[Dict], output_file: str = "parameter_sweep_results.json"):
    """保存結果到 JSON 文件"""
    
    output_path = Path(__file__).parent.parent.parent / "docs" / "results" / output_file
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_path}")


def main():
    # Find data files
    data_files = [
        ("data/binance_usdm/btcusdt_20240808.npz", "data/binance_usdm/btcusdt_20240808_eod.npz"),
        ("data/dummy_data.npy", "data/dummy_snapshot.npz"),
    ]
    
    available_data = None
    for data_file, snapshot_file in data_files:
        full_data_path = Path(__file__).parent.parent.parent / data_file
        full_snapshot_path = Path(__file__).parent.parent.parent / snapshot_file
        
        if full_data_path.exists() and full_snapshot_path.exists():
            available_data = (str(full_data_path), str(full_snapshot_path))
            break
    
    if available_data is None:
        logger.error("Error: No data files found!")
        return
    
    data_file, snapshot_file = available_data
    logger.info(f"\nUsing data: {data_file}")
    
    # Import strategy
    try:
        from ..strategies.aggressive import market_making_algo as strategy_func
    except ImportError:
        from strategies.aggressive import market_making_algo as strategy_func
    
    # 參數範圍（可以根據需要調整）
    k_values = [1.5, 2.0, 2.5]
    gamma_values = [0.05, 0.08, 0.10]
    max_position_values = [8.0, 10.0]
    
    # 運行參數掃描
    results = parameter_sweep(
        strategy_func,
        data_file,
        snapshot_file,
        k_values=k_values,
        gamma_values=gamma_values,
        max_position_values=max_position_values
    )
    
    # 顯示結果
    print_sweep_results(results)
    
    # 保存結果
    save_results(results)
    
    return results


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nParameter sweep interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Parameter sweep failed: {e}", exc_info=True)
        sys.exit(1)

