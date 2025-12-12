"""
Configuration Loader Module
===========================
載入和管理策略配置檔案
"""

import yaml
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RegimeConfig:
    """體制配置"""
    spread_mult: float
    alpha_mult: float
    gamma_mult: float
    vol_threshold: float


@dataclass
class AlphaBoostConfig:
    """Alpha 增強配置"""
    enabled: bool
    extreme_threshold: float
    extreme_mult: float
    high_threshold: float
    high_mult: float


@dataclass
class HuntLogicConfig:
    """非對稱報價邏輯配置"""
    enabled: bool
    bullish_threshold: float
    bearish_threshold: float
    bid_tighten_mult: float
    ask_widen_mult: float
    bid_widen_mult: float
    ask_tighten_mult: float


@dataclass
class SlopeAdjustmentConfig:
    """斜率調整配置"""
    enabled: bool
    min_mult: float
    max_mult: float


@dataclass
class StrategyConfig:
    """策略配置"""
    # Core Parameters
    gamma_base: float
    k_base: float
    
    # Alpha Weights
    micro_weight: float
    mlofi_weight: float
    slope_weight: float
    
    # Multi-level Depth
    num_levels: int
    ofi_decay: float
    
    # Volatility
    window_size: int
    base_volatility_mult: float
    vol_smoothing: float
    
    # Order Management
    order_qty: float
    max_position: float
    
    # Timing
    elapse_interval_ns: int
    
    # Regime Parameters
    regime_calm: RegimeConfig
    regime_active: RegimeConfig
    regime_volatile: RegimeConfig
    
    # Alpha Boost
    alpha_boost: AlphaBoostConfig
    
    # Hunt Logic
    hunt_logic: HuntLogicConfig
    
    # Slope Adjustment
    slope_adjustment: SlopeAdjustmentConfig
    
    @classmethod
    def from_dict(cls, data: Dict):
        """從字典建立配置"""
        strategy_data = data['strategy']
        params = strategy_data['parameters']
        regime_data = strategy_data['regime']
        
        return cls(
            gamma_base=params['gamma_base'],
            k_base=params['k_base'],
            micro_weight=params['micro_weight'],
            mlofi_weight=params['mlofi_weight'],
            slope_weight=params['slope_weight'],
            num_levels=params['num_levels'],
            ofi_decay=params['ofi_decay'],
            window_size=params['window_size'],
            base_volatility_mult=params['base_volatility_mult'],
            vol_smoothing=params['vol_smoothing'],
            order_qty=params['order_qty'],
            max_position=params['max_position'],
            elapse_interval_ns=params['elapse_interval_ns'],
            regime_calm=RegimeConfig(**regime_data['calm']),
            regime_active=RegimeConfig(**regime_data['active']),
            regime_volatile=RegimeConfig(**regime_data['volatile']),
            alpha_boost=AlphaBoostConfig(**strategy_data['alpha_boost']),
            hunt_logic=HuntLogicConfig(**strategy_data['hunt_logic']),
            slope_adjustment=SlopeAdjustmentConfig(**strategy_data['slope_adjustment']),
        )


@dataclass
class BacktestConfig:
    """回測配置"""
    tick_size: float
    lot_size: float
    contract_size: float
    order_latency_ns: int
    initial_capital: float
    queue_model: str
    queue_model_param: float
    partial_fill: bool
    
    @classmethod
    def from_dict(cls, data: Dict):
        """從字典建立配置"""
        backtest_data = data['backtest']
        return cls(**backtest_data)


@dataclass
class LoggingConfig:
    """日誌配置"""
    level: str
    file: str
    console: bool
    format: str
    
    @classmethod
    def from_dict(cls, data: Dict):
        """從字典建立配置"""
        logging_data = data.get('logging', {})
        return cls(
            level=logging_data.get('level', 'INFO'),
            file=logging_data.get('file', 'logs/backtest.log'),
            console=logging_data.get('console', True),
            format=logging_data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )


class ConfigLoader:
    """配置載入器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            self.config_dir = Path(__file__).parent.parent / config_dir
    
    def load(self, config_file: str) -> Dict:
        """
        載入配置檔案
        
        Args:
            config_file: 配置檔案名稱（相對於 config 目錄）
            
        Returns:
            完整的配置字典
        """
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def load_strategy_config(self, config_file: str = "strategy_aggressive.yaml") -> StrategyConfig:
        """載入策略配置"""
        config = self.load(config_file)
        return StrategyConfig.from_dict(config)
    
    def load_backtest_config(self, config_file: str = "strategy_aggressive.yaml") -> BacktestConfig:
        """載入回測配置"""
        config = self.load(config_file)
        return BacktestConfig.from_dict(config)
    
    def load_logging_config(self, config_file: str = "strategy_aggressive.yaml") -> LoggingConfig:
        """載入日誌配置"""
        config = self.load(config_file)
        return LoggingConfig.from_dict(config)
    
    def load_all(self, config_file: str = "strategy_aggressive.yaml") -> tuple:
        """載入所有配置"""
        config = self.load(config_file)
        return (
            StrategyConfig.from_dict(config),
            BacktestConfig.from_dict(config),
            LoggingConfig.from_dict(config)
        )


# 預設配置載入器實例
_default_loader = ConfigLoader()


def load_config(config_file: str = "strategy_aggressive.yaml") -> tuple:
    """
    便捷函數：載入配置
    
    Args:
        config_file: 配置檔案名稱
        
    Returns:
        (strategy_config, backtest_config, logging_config)
    """
    return _default_loader.load_all(config_file)

