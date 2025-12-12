"""
Utility Modules
===============
工具類模組
"""

from .logger import setup_logger, get_logger

# Lazy imports to avoid circular dependencies
__all__ = [
    'setup_logger',
    'get_logger',
]

def __getattr__(name):
    """Lazy loading for optional imports"""
    if name == 'plot_pnl' or name == 'plot_drawdown':
        from .visualization import plot_pnl, plot_drawdown
        return plot_pnl if name == 'plot_pnl' else plot_drawdown
    elif name == 'ResultViewer' or name == 'create_simple_report':
        from .result_viewer import ResultViewer, create_simple_report
        return ResultViewer if name == 'ResultViewer' else create_simple_report
    elif name == 'Reconciler':
        from .reconciliation import Reconciler
        return Reconciler
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

