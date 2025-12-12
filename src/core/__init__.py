"""
Core Modules
============
核心功能模組
"""

# Lazy imports to avoid circular dependencies
__all__ = [
    'run_backtest',
    'create_asset',
    'validate_data_file',
    'load_config',
    'ConfigLoader',
    'BacktestConfig',
    'StrategyConfig',
]

def __getattr__(name):
    """Lazy loading for imports"""
    if name == 'run_backtest':
        from .backtest import run_backtest
        return run_backtest
    elif name in ('create_asset', 'validate_data_file'):
        from .data_loader import create_asset, validate_data_file
        return create_asset if name == 'create_asset' else validate_data_file
    elif name in ('load_config', 'ConfigLoader', 'BacktestConfig', 'StrategyConfig'):
        from .config_loader import load_config, ConfigLoader, BacktestConfig, StrategyConfig
        if name == 'load_config':
            return load_config
        elif name == 'ConfigLoader':
            return ConfigLoader
        elif name == 'BacktestConfig':
            return BacktestConfig
        elif name == 'StrategyConfig':
            return StrategyConfig
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

