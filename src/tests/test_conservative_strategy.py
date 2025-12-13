"""
測試保守版本策略
================

比較 Aggressive 和 Conservative 版本的策略表現
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_loader import create_asset, validate_data_file
from core.config_loader import load_config
from utils.logger import get_logger
from hftbacktest import HashMapMarketDepthBacktest
import numpy as np

logger = get_logger(__name__)


def run_strategy(strategy_func, data_file, snapshot_file, strategy_name, backtest_config=None):
    """運行策略並返回結果"""
    
    try:
        validate_data_file(data_file)
        
        if backtest_config is None:
            try:
                from ..core.config_loader import BacktestConfig
            except ImportError:
                from core.config_loader import BacktestConfig
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
        
        logger.info(f"Running {strategy_name} strategy...")
        logger.info("This may take a few seconds...")
        start_time = time.time()
        
        try:
            strategy_func(hbt, stat)
        except Exception as e:
            logger.error(f"Strategy {strategy_name} failed: {e}", exc_info=True)
            raise
        
        elapsed = time.time() - start_time
        logger.info(f"{strategy_name} completed in {elapsed:.2f} seconds")
        
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


def print_comparison(aggressive_result, conservative_result):
    """打印對比報告"""
    
    aggressive_pnl = aggressive_result['pnl']
    conservative_pnl = conservative_result['pnl']
    
    if aggressive_pnl != 0:
        improvement = (conservative_pnl - aggressive_pnl) / abs(aggressive_pnl) * 100
    else:
        improvement = 0 if conservative_pnl == 0 else float('inf')
    
    winner = "Conservative" if conservative_pnl > aggressive_pnl else "Aggressive"
    
    logger.info("\n" + "="*60)
    logger.info("STRATEGY COMPARISON: Aggressive vs Conservative")
    logger.info("="*60)
    logger.info("")
    logger.info("-"*60)
    logger.info("AGGRESSIVE (Original)")
    logger.info("-"*60)
    logger.info(f"   Balance:       {aggressive_result['balance']:>15,.2f}")
    logger.info(f"   Position:      {aggressive_result['position']:>15,.4f}")
    logger.info(f"   Equity:        {aggressive_result['equity']:>15,.2f}")
    logger.info(f"   PnL:           {aggressive_result['pnl']:>+15,.2f}")
    logger.info(f"   Time:          {aggressive_result['elapsed']:>15,.2f}s")
    logger.info("")
    logger.info("-"*60)
    logger.info("CONSERVATIVE (Optimized)")
    logger.info("-"*60)
    logger.info(f"   Balance:       {conservative_result['balance']:>15,.2f}")
    logger.info(f"   Position:      {conservative_result['position']:>15,.4f}")
    logger.info(f"   Equity:        {conservative_result['equity']:>15,.2f}")
    logger.info(f"   PnL:           {conservative_result['pnl']:>+15,.2f}")
    logger.info(f"   Time:          {conservative_result['elapsed']:>15,.2f}s")
    logger.info("")
    logger.info("="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"   Aggressive PnL:    {aggressive_pnl:>+15,.2f}")
    logger.info(f"   Conservative PnL:  {conservative_pnl:>+15,.2f}")
    logger.info(f"   Difference:        {conservative_pnl - aggressive_pnl:>+15,.2f}")
    logger.info(f"   Improvement:       {improvement:>+15,.2f}%")
    logger.info(f"   Winner:            {winner:>15s}")
    logger.info("="*60)
    
    return {
        'aggressive_pnl': aggressive_pnl,
        'conservative_pnl': conservative_pnl,
        'difference': conservative_pnl - aggressive_pnl,
        'improvement': improvement,
        'winner': winner
    }


def main():
    # Find data files
    data_files = [
        ("data/binance_usdm/btcusdt_20240808.npz", "data/binance_usdm/btcusdt_20240808_eod.npz", "Binance BTCUSDT 2024-08-08"),
        ("data/dummy_data.npy", "data/dummy_snapshot.npz", "Dummy Data"),
    ]
    
    available_data = None
    for data_file, snapshot_file, name in data_files:
        full_data_path = Path(__file__).parent.parent.parent / data_file
        full_snapshot_path = Path(__file__).parent.parent.parent / snapshot_file
        
        if full_data_path.exists() and full_snapshot_path.exists():
            available_data = (str(full_data_path), str(full_snapshot_path), name)
            break
    
    if available_data is None:
        logger.error("Error: No data files found!")
        return
    
    data_file, snapshot_file, data_name = available_data
    logger.info(f"\nUsing data: {data_name}")
    logger.info(f"File: {data_file}")
    
    # Load config
    try:
        _, backtest_config, _ = load_config()
    except FileNotFoundError:
        logger.warning("Config file not found, using defaults")
        backtest_config = None
    
    # Import strategies
    try:
        from ..strategies.aggressive import market_making_algo as aggressive_algo
        from ..strategies.aggressive_conservative import market_making_algo as conservative_algo
    except ImportError:
        from strategies.aggressive import market_making_algo as aggressive_algo
        from strategies.aggressive_conservative import market_making_algo as conservative_algo
    
    # Run aggressive
    logger.info("\nRunning Aggressive strategy...")
    aggressive_result = run_strategy(aggressive_algo, data_file, snapshot_file, "Aggressive", backtest_config)
    
    # Run conservative
    logger.info("\nRunning Conservative strategy...")
    conservative_result = run_strategy(conservative_algo, data_file, snapshot_file, "Conservative", backtest_config)
    
    # Compare
    summary = print_comparison(aggressive_result, conservative_result)
    
    return summary


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)

