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
from pathlib import Path
from datetime import datetime
from hftbacktest import HashMapMarketDepthBacktest, Recorder

# Import strategy - can be changed to test different strategies
from strategy import market_making_algo

# Import new modules
try:
    # Try relative imports first (when used as module)
    from .data_loader import create_asset, validate_data_file
    from .config_loader import load_config, ConfigLoader
    from .logger import setup_logger, get_logger
    from .result_viewer import ResultViewer
except ImportError:
    # Fall back to absolute imports (when run as script)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import create_asset, validate_data_file
    from config_loader import load_config, ConfigLoader
    from logger import setup_logger, get_logger
    from result_viewer import ResultViewer

# 設置日誌（會在載入配置後重新配置）
logger = get_logger(__name__)


def run_backtest(
    data_file,
    snapshot_file=None,
    visualize=True,
    save_report=False,
    config_file=None
):
    """
    執行回測
    
    Args:
        data_file: 市場資料檔案路徑 (.gz, .npz, .npy)
        snapshot_file: 快照檔案路徑 (可選)
        visualize: 是否顯示視覺化圖表
        save_report: 是否儲存報告
        config_file: 配置檔案路徑 (可選，使用預設配置)
    """
    try:
        # 載入配置
        if config_file:
            strategy_config, backtest_config, logging_config = load_config(config_file)
        else:
            try:
                strategy_config, backtest_config, logging_config = load_config()
            except FileNotFoundError:
                # 如果沒有配置檔案，使用預設值
                logger.warning("Config file not found, using default values")
                from .config_loader import BacktestConfig
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
                logging_config = None
        
        # 設置日誌
        if logging_config:
            logger = setup_logger(
                'backtest',
                log_file=logging_config.file,
                level=logging_config.level,
                console=logging_config.console,
                format_string=logging_config.format
            )
        else:
            logger = setup_logger('backtest', console=True)
        
        logger.info("="*50)
        logger.info("HFT Backtest Runner")
        logger.info("="*50)
        
        # 驗證並載入資料
        logger.info(f"Loading data from {data_file}...")
        validate_data_file(data_file)
        
        # 使用統一的資料載入模組
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
        
        # Initialize Backtest
        hbt = HashMapMarketDepthBacktest([asset])
        stat = np.zeros(20, dtype=np.float64)
        
        logger.info(f"Backtest Configuration:")
        logger.info(f"   Assets: {hbt.num_assets}")
        logger.info(f"   Tick Size: {backtest_config.tick_size}")
        logger.info(f"   Lot Size: {backtest_config.lot_size}")
        logger.info(f"   Order Latency: {backtest_config.order_latency_ns / 1e6:.1f}ms")
        
        # Initialize Recorder for real data collection
        # Estimate record size: assume 100ms intervals, 24 hours = 864,000 records
        # Use a reasonable buffer (1M records should be enough for most backtests)
        record_size = 1_000_000
        recorder = Recorder(num_assets=1, record_size=record_size)
        
        logger.info("Running strategy...")
        start_time = time.time()
        
        # Initialize result viewer
        result_viewer = ResultViewer(tick_size=backtest_config.tick_size)
        initial_capital = backtest_config.initial_capital
        contract_size = backtest_config.contract_size
        
        # Record initial state
        initial_stat_val = hbt.state_values(0)
        initial_balance = initial_stat_val.balance
        initial_position = initial_stat_val.position
        initial_fee = initial_stat_val.fee
        
        initial_depth = hbt.depth(0)
        if initial_depth.best_bid > 0 and initial_depth.best_ask > 0:
            initial_mid_price = (initial_depth.best_bid + initial_depth.best_ask) / 2.0
        else:
            initial_mid_price = backtest_config.initial_capital / 10.0
        
        initial_equity = initial_balance + initial_position * initial_mid_price * contract_size - initial_fee
        
        logger.info(f"Initial State:")
        logger.info(f"   Balance: {initial_balance:,.2f}")
        logger.info(f"   Position: {initial_position:,.4f}")
        logger.info(f"   Mid Price: {initial_mid_price:,.2f}")
        logger.info(f"   Equity: {initial_equity:,.2f}")
        
        # Run Strategy with recording
        # Pass recorder.recorder to strategy for periodic recording
        try:
            market_making_algo(hbt, stat, recorder.recorder)
            step_count = int(stat[4]) if len(stat) > 4 else 0
            
            # Record final state
            try:
                recorder.recorder.record(hbt)
            except:
                pass  # Ignore if recorder is full
                
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}", exc_info=True)
            raise
        
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
            mid_price = backtest_config.initial_capital / 10.0  # Fallback
            logger.warning(f"No valid market depth, using fallback mid_price: {mid_price}")
        
        # Calculate equity
        equity_wo_fee = balance + position * mid_price * contract_size
        equity = equity_wo_fee - fee
        # PnL = current equity - initial equity (not initial_capital, which is just a config value)
        pnl = equity - initial_equity
        pnl_pct = (pnl / abs(initial_equity)) * 100 if initial_equity != 0 else 0
        
        logger.info(f"Final State:")
        logger.info(f"   Balance: {balance:,.2f} (change: {balance - initial_balance:+,.2f})")
        logger.info(f"   Position: {position:,.4f} (change: {position - initial_position:+,.4f})")
        logger.info(f"   Fee: {fee:,.2f} (accumulated: {fee - initial_fee:+,.2f})")
        logger.info(f"   Equity: {equity:,.2f} (change: {equity - initial_equity:+,.2f})")
        
        # Collect real data from recorder
        try:
            records = recorder.get(asset_no=0)
            num_records = len(records)
            logger.info(f"Collected {num_records} data points from recorder")
            
            if num_records > 0:
                # Fill result viewer with real data
                for record in records:
                    record_price = record['price']
                    record_position = record['position']
                    record_balance = record['balance']
                    record_fee = record['fee']
                    
                    # Calculate equity for this record
                    record_equity = record_balance + record_position * record_price * contract_size - record_fee
                    
                    result_viewer.record_step(
                        equity=record_equity,
                        position=record_position,
                        mid_price=record_price
                    )
            else:
                logger.warning("No records collected, using final state only")
                result_viewer.record_step(
                    equity=equity,
                    position=position,
                    mid_price=mid_price
                )
        except Exception as e:
            logger.warning(f"Failed to collect recorder data: {e}. Using final state only.")
            import traceback
            logger.debug(traceback.format_exc())
            # Fallback: record final state
            result_viewer.record_step(
                equity=equity,
                position=position,
                mid_price=mid_price
            )
        
        # Print results
        logger.info("="*50)
        logger.info("BACKTEST RESULTS")
        logger.info("="*50)
        logger.info(f"Execution Time: {elapsed:.2f} seconds")
        logger.info("Capital:")
        logger.info(f"   Balance:         {balance:>12,.2f}")
        logger.info(f"   Position:        {position:>12,.4f}")
        logger.info(f"   Mid Price:       {mid_price:>12,.2f}")
        logger.info(f"   Equity (no fee): {equity_wo_fee:>12,.2f}")
        logger.info(f"   Total Fees:      {fee:>12,.2f}")
        logger.info(f"   Equity (net):    {equity:>12,.2f}")
        logger.info(f"   PnL:             {pnl:>+12,.2f} ({pnl_pct:+.2f}%)")
        logger.info("="*50)
        
        # Use result viewer for visualization
        if visualize:
            try:
                # Result viewer already filled with real data from recorder
                # Generate report
                result_viewer.print_summary()
                
                # Plot with volatility by tick
                save_path = None
                if save_report:
                    save_path = f"results/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                
                result_viewer.plot_results(
                    title=f"Backtest: {os.path.basename(data_file)}",
                    save_path=save_path,
                    show=not save_report
                )
                    
            except ImportError:
                logger.warning("Visualization skipped (matplotlib not installed)")
            except Exception as e:
                logger.warning(f"Visualization skipped: {e}")
        
        return {
            'balance': balance,
            'position': position,
            'fee': fee,
            'equity': equity,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'elapsed_time': elapsed
        }
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HFT Backtest Runner')
    parser.add_argument('data_file', help='Market data file (.gz, .npz, or .npy)')
    parser.add_argument('--snapshot', '-s', help='Snapshot file (auto-detected for .gz)')
    parser.add_argument('--no-viz', action='store_true', help='Disable visualization')
    parser.add_argument('--save', action='store_true', help='Save report to file')
    parser.add_argument('--config', '-c', help='Configuration file path')
    
    args = parser.parse_args()
    
    try:
        run_backtest(
            args.data_file,
            snapshot_file=args.snapshot,
            visualize=not args.no_viz,
            save_report=args.save,
            config_file=args.config
        )
    except KeyboardInterrupt:
        logger.info("Backtest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        sys.exit(1)
