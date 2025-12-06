"""
Backtest Visualization and Analysis Tools
==========================================
視覺化回測結果，包含 PnL 曲線、持倉、交易統計等
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def plot_backtest_results(equity_curve, positions=None, trades=None, title="Backtest Results"):
    """
    繪製完整的回測結果視覺化
    
    Args:
        equity_curve: list/array of equity values over time
        positions: list/array of position values (optional)
        trades: list of trade records (optional)
        title: plot title
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    # 1. Equity Curve
    ax1 = axes[0]
    equity = np.array(equity_curve)
    x = np.arange(len(equity))
    ax1.plot(x, equity, 'b-', linewidth=1.5, label='Equity')
    ax1.fill_between(x, equity[0], equity, alpha=0.3, 
                     where=(equity >= equity[0]), color='green', label='Profit')
    ax1.fill_between(x, equity[0], equity, alpha=0.3,
                     where=(equity < equity[0]), color='red', label='Loss')
    ax1.axhline(y=equity[0], color='gray', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Equity', fontsize=11)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Calculate and show key metrics
    pnl = equity[-1] - equity[0]
    max_equity = np.maximum.accumulate(equity)
    drawdown = (max_equity - equity) / max_equity * 100
    max_dd = np.max(drawdown)
    
    returns = np.diff(equity) / equity[:-1]
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 * 24 * 60) if np.std(returns) > 0 else 0
    
    metrics_text = f'PnL: {pnl:+.2f} | Max DD: {max_dd:.2f}% | Sharpe: {sharpe:.2f}'
    ax1.set_title(metrics_text, fontsize=10, loc='right')
    
    # 2. Drawdown
    ax2 = axes[1]
    ax2.fill_between(x, 0, -drawdown, color='red', alpha=0.5)
    ax2.set_ylabel('Drawdown (%)', fontsize=11)
    ax2.set_ylim([min(-max_dd * 1.1, -1), 0])
    ax2.grid(True, alpha=0.3)
    
    # 3. Position
    ax3 = axes[2]
    if positions is not None:
        positions = np.array(positions)
        ax3.plot(x[:len(positions)], positions, 'purple', linewidth=1)
        ax3.fill_between(x[:len(positions)], 0, positions, 
                        where=(positions >= 0), color='green', alpha=0.3)
        ax3.fill_between(x[:len(positions)], 0, positions,
                        where=(positions < 0), color='red', alpha=0.3)
        ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax3.set_ylabel('Position', fontsize=11)
    ax3.set_xlabel('Time Steps', fontsize=11)
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def calculate_metrics(equity_curve, positions=None):
    """
    計算詳細的績效指標
    
    Returns:
        dict: 包含各種績效指標
    """
    equity = np.array(equity_curve)
    initial_capital = equity[0]
    final_equity = equity[-1]
    
    # Basic metrics
    pnl = final_equity - initial_capital
    pnl_pct = (pnl / initial_capital) * 100
    
    # Drawdown
    max_equity = np.maximum.accumulate(equity)
    drawdown = (max_equity - equity) / max_equity
    max_drawdown = np.max(drawdown) * 100
    
    # Returns
    returns = np.diff(equity) / equity[:-1]
    avg_return = np.mean(returns) * 100
    return_std = np.std(returns) * 100
    
    # Sharpe Ratio (assuming 100ms steps, ~252 trading days)
    if return_std > 0:
        # Annualized: sqrt(steps_per_year) * mean/std
        steps_per_year = 252 * 24 * 60 * 60 * 10  # 100ms steps
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(steps_per_year)
    else:
        sharpe = 0
    
    # Win rate
    positive_returns = np.sum(returns > 0)
    total_returns = len(returns)
    win_rate = (positive_returns / total_returns * 100) if total_returns > 0 else 0
    
    # Position metrics
    position_metrics = {}
    if positions is not None:
        positions = np.array(positions)
        position_metrics = {
            'avg_position': np.mean(positions),
            'max_position': np.max(positions),
            'min_position': np.min(positions),
            'position_std': np.std(positions),
        }
    
    metrics = {
        'initial_capital': initial_capital,
        'final_equity': final_equity,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'max_drawdown_pct': max_drawdown,
        'sharpe_ratio': sharpe,
        'avg_return_pct': avg_return,
        'return_std_pct': return_std,
        'win_rate_pct': win_rate,
        'total_steps': len(equity),
        **position_metrics
    }
    
    return metrics


def print_metrics_report(metrics, title="=== Backtest Performance Report ==="):
    """
    打印格式化的績效報告
    """
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)
    
    print(f"\n📊 Capital")
    print(f"   Initial:      {metrics['initial_capital']:>12,.2f}")
    print(f"   Final:        {metrics['final_equity']:>12,.2f}")
    print(f"   PnL:          {metrics['pnl']:>+12,.2f} ({metrics['pnl_pct']:+.2f}%)")
    
    print(f"\n📈 Risk Metrics")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:>12.2f}")
    print(f"   Max Drawdown: {metrics['max_drawdown_pct']:>12.2f}%")
    print(f"   Win Rate:     {metrics['win_rate_pct']:>12.2f}%")
    
    print(f"\n📉 Returns")
    print(f"   Avg Return:   {metrics['avg_return_pct']:>12.4f}%")
    print(f"   Std Dev:      {metrics['return_std_pct']:>12.4f}%")
    
    if 'avg_position' in metrics:
        print(f"\n📦 Position")
        print(f"   Avg Position: {metrics['avg_position']:>12.4f}")
        print(f"   Max Long:     {metrics['max_position']:>12.4f}")
        print(f"   Max Short:    {metrics['min_position']:>12.4f}")
    
    print(f"\n⏱️  Total Steps:  {metrics['total_steps']:>12,}")
    print("=" * 50 + "\n")


def compare_strategies(results_dict, title="Strategy Comparison"):
    """
    比較多個策略的結果
    
    Args:
        results_dict: dict of {strategy_name: equity_curve}
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(results_dict)))
    
    # Equity curves
    ax1 = axes[0]
    for (name, equity), color in zip(results_dict.items(), colors):
        equity = np.array(equity)
        normalized = equity / equity[0] * 100  # Normalize to 100
        ax1.plot(normalized, label=name, color=color, linewidth=1.5)
    
    ax1.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Normalized Equity (%)', fontsize=11)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Drawdown comparison
    ax2 = axes[1]
    for (name, equity), color in zip(results_dict.items(), colors):
        equity = np.array(equity)
        max_equity = np.maximum.accumulate(equity)
        drawdown = (max_equity - equity) / max_equity * 100
        ax2.plot(-drawdown, label=name, color=color, linewidth=1.5)
    
    ax2.set_ylabel('Drawdown (%)', fontsize=11)
    ax2.set_xlabel('Time Steps', fontsize=11)
    ax2.legend(loc='lower left')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def save_report(metrics, equity_curve, positions=None, output_dir="reports"):
    """
    儲存完整的回測報告
    """
    import os
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save plot
    fig = plot_backtest_results(equity_curve, positions)
    fig.savefig(f"{output_dir}/backtest_{timestamp}.png", dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Save metrics to text
    with open(f"{output_dir}/metrics_{timestamp}.txt", 'w') as f:
        f.write("Backtest Performance Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 40 + "\n\n")
        for key, value in metrics.items():
            if isinstance(value, float):
                f.write(f"{key}: {value:.4f}\n")
            else:
                f.write(f"{key}: {value}\n")
    
    print(f"📁 Report saved to {output_dir}/")
    return f"{output_dir}/backtest_{timestamp}.png"


if __name__ == "__main__":
    # Demo with sample data
    np.random.seed(42)
    n_steps = 1000
    
    # Simulate equity curve
    returns = np.random.randn(n_steps) * 0.001 + 0.0001
    equity = 30000 * (1 + returns).cumprod()
    
    # Simulate positions
    positions = np.cumsum(np.random.randn(n_steps) * 0.5)
    positions = np.clip(positions, -10, 10)
    
    # Calculate and print metrics
    metrics = calculate_metrics(equity, positions)
    print_metrics_report(metrics)
    
    # Plot
    fig = plot_backtest_results(equity, positions, title="Demo Backtest Results")
    plt.show()
