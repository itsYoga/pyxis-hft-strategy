"""
Data Loader Module
==================
統一的資料載入模組
"""

import os
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from hftbacktest import BacktestAsset
from hftbacktest.data.utils.binancefutures import convert
from hftbacktest.data.utils.snapshot import create_last_snapshot

try:
    from .logger import get_logger
except ImportError:
    from logger import get_logger

logger = get_logger(__name__)


def validate_data_file(data_file: str) -> bool:
    """
    驗證資料檔案
    
    Args:
        data_file: 資料檔案路徑
        
    Raises:
        FileNotFoundError: 檔案不存在
        ValueError: 檔案格式不支援或檔案為空
    """
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    if not data_file.endswith(('.gz', '.npz', '.npy')):
        raise ValueError(f"Unsupported file format: {data_file}. Supported: .gz, .npz, .npy")
    
    size = os.path.getsize(data_file)
    if size == 0:
        raise ValueError(f"Data file is empty: {data_file}")
    
    logger.debug(f"Data file validated: {data_file} ({size:,} bytes)")
    return True


def prepare_binance_data(data_file: str) -> Tuple[str, str]:
    """
    準備 Binance 資料：轉換 .gz 格式並建立 snapshot
    
    Args:
        data_file: .gz 資料檔案路徑
        
    Returns:
        (npz_file, snapshot_file) 路徑元組
    """
    if not data_file.endswith('.gz'):
        raise ValueError(f"Expected .gz file, got: {data_file}")
    
    npz_file = data_file.replace('.gz', '.npz')
    snapshot_file = data_file.replace('.gz', '_eod.npz')
    
    # 轉換 .gz 到 .npz
    if not os.path.exists(npz_file):
        logger.info(f"Converting {data_file} to .npz format...")
        try:
            convert(data_file, output_filename=npz_file)
            logger.info(f"Saved to {npz_file}")
        except Exception as e:
            logger.error(f"Failed to convert data file: {e}")
            raise
    else:
        logger.debug(f"Using existing {npz_file}")
    
    # 建立 snapshot
    if not os.path.exists(snapshot_file):
        logger.info(f"Creating snapshot...")
        try:
            create_last_snapshot(
                [npz_file],
                tick_size=0.1,
                lot_size=0.001,
                output_snapshot_filename=snapshot_file
            )
            logger.info(f"Saved to {snapshot_file}")
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise
    else:
        logger.debug(f"Using existing {snapshot_file}")
    
    return npz_file, snapshot_file


def load_binance_asset(
    data_file: str,
    snapshot_file: Optional[str] = None,
    tick_size: float = 0.1,
    lot_size: float = 0.001,
    order_latency_ns: int = 10_000_000,
    queue_model: str = "power_prob",
    queue_model_param: float = 2.0,
    partial_fill: bool = False
) -> BacktestAsset:
    """
    載入 Binance 格式資料並建立 Asset
    
    Args:
        data_file: 資料檔案路徑（.gz 或 .npz）
        snapshot_file: 快照檔案路徑（可選，自動偵測）
        tick_size: 最小價格變動單位
        lot_size: 最小交易單位
        order_latency_ns: 訂單延遲（奈秒）
        queue_model: 隊列模型類型
        queue_model_param: 隊列模型參數
        partial_fill: 是否允許部分成交
        
    Returns:
        BacktestAsset 實例
    """
    # 處理 .gz 檔案
    if data_file.endswith('.gz'):
        npz_file, auto_snapshot = prepare_binance_data(data_file)
        if snapshot_file is None:
            snapshot_file = auto_snapshot
        data_file = npz_file
    
    # 自動偵測 snapshot
    if snapshot_file is None:
        if data_file.endswith('.npz'):
            snapshot_file = data_file.replace('.npz', '_eod.npz')
        else:
            raise ValueError("Cannot auto-detect snapshot file. Please specify snapshot_file.")
    
    if not os.path.exists(snapshot_file):
        logger.warning(f"Snapshot file not found: {snapshot_file}. Creating...")
        try:
            create_last_snapshot(
                [data_file],
                tick_size=tick_size,
                lot_size=lot_size,
                output_snapshot_filename=snapshot_file
            )
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise
    
    # 建立 Asset
    asset = (
        BacktestAsset()
            .data([data_file])
            .initial_snapshot(snapshot_file)
            .linear_asset(1.0)
            .constant_order_latency(order_latency_ns, order_latency_ns)
    )
    
    # 設置隊列模型
    if queue_model == "power_prob":
        asset = asset.power_prob_queue_model(queue_model_param)
    # 可以添加其他隊列模型
    
    # 設置成交模式
    if not partial_fill:
        asset = asset.no_partial_fill_exchange()
    
    # 設置 tick size 和 lot size
    asset = asset.tick_size(tick_size).lot_size(lot_size)
    
    logger.info(f"Loaded Binance data: {data_file}")
    return asset


def load_custom_asset(
    data_file: str,
    snapshot_file: str,
    tick_size: float = 0.1,
    lot_size: float = 0.01,
    order_latency_ns: int = 10_000_000
) -> BacktestAsset:
    """
    載入自訂格式資料並建立 Asset
    
    Args:
        data_file: 資料檔案路徑（.npz 或 .npy）
        snapshot_file: 快照檔案路徑
        tick_size: 最小價格變動單位
        lot_size: 最小交易單位
        order_latency_ns: 訂單延遲（奈秒）
        
    Returns:
        BacktestAsset 實例
    """
    # 載入資料
    if data_file.endswith('.npz'):
        data_arr = np.load(data_file, allow_pickle=True)['data']
    elif data_file.endswith('.npy'):
        data_arr = np.load(data_file, allow_pickle=True)
    else:
        raise ValueError(f"Unsupported custom data format: {data_file}")
    
    logger.info(f"Loaded {len(data_arr):,} events from {data_file}")
    
    # 載入 snapshot
    if not os.path.exists(snapshot_file):
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")
    
    snapshot_arr = np.load(snapshot_file, allow_pickle=True)['data']
    logger.debug(f"Loaded snapshot from {snapshot_file}")
    
    # 建立 Asset
    asset = (
        BacktestAsset()
            .add_data(data_arr)
            .initial_snapshot(snapshot_arr)
            .linear_asset(1.0)
            .constant_order_latency(order_latency_ns, order_latency_ns)
            .tick_size(tick_size)
            .lot_size(lot_size)
    )
    
    logger.info(f"Loaded custom data: {data_file}")
    return asset


def create_asset(
    data_file: str,
    snapshot_file: Optional[str] = None,
    tick_size: float = 0.1,
    lot_size: float = 0.001,
    order_latency_ns: int = 10_000_000,
    queue_model: str = "power_prob",
    queue_model_param: float = 2.0,
    partial_fill: bool = False
) -> BacktestAsset:
    """
    智能載入資料：自動偵測格式並建立 Asset
    
    Args:
        data_file: 資料檔案路徑
        snapshot_file: 快照檔案路徑（可選）
        tick_size: 最小價格變動單位
        lot_size: 最小交易單位
        order_latency_ns: 訂單延遲（奈秒）
        queue_model: 隊列模型類型
        queue_model_param: 隊列模型參數
        partial_fill: 是否允許部分成交
        
    Returns:
        BacktestAsset 實例
    """
    # 驗證檔案
    validate_data_file(data_file)
    
    # 判斷資料格式
    if data_file.endswith('.gz') or ('binance' in data_file.lower() and data_file.endswith('.npz')):
        # Binance 格式
        return load_binance_asset(
            data_file=data_file,
            snapshot_file=snapshot_file,
            tick_size=tick_size,
            lot_size=lot_size,
            order_latency_ns=order_latency_ns,
            queue_model=queue_model,
            queue_model_param=queue_model_param,
            partial_fill=partial_fill
        )
    else:
        # 自訂格式
        if snapshot_file is None:
            # 嘗試自動偵測
            if data_file.endswith('.npz'):
                snapshot_file = data_file.replace('.npz', '_snapshot.npz')
            else:
                snapshot_file = os.path.join(os.path.dirname(data_file), "dummy_snapshot.npz")
        
        return load_custom_asset(
            data_file=data_file,
            snapshot_file=snapshot_file,
            tick_size=tick_size,
            lot_size=lot_size,
            order_latency_ns=order_latency_ns
        )

