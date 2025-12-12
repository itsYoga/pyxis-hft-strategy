"""
Result Viewer Module
====================
簡單的方式來展示回測結果，包含按 tick 顯示波動
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

try:
    from .logger import get_logger
except ImportError:
    from logger import get_logger

logger = get_logger(__name__)


class ResultViewer:
    """結果展示器"""
    
    def __init__(self, tick_size: float = 0.1):
        """
        初始化結果展示器
        
        Args:
            tick_size: 最小價格變動單位
        """
        self.tick_size = tick_size
        self.equity_history: List[float] = []
        self.position_history: List[float] = []
        self.price_history: List[float] = []
        self.volatility_history: List[float] = []
        self.timestamps: List[int] = []
        self.trades: List[Dict] = []
    
    def record_step(
        self,
        equity: float,
        position: float,
        mid_price: float,
        volatility: Optional[float] = None,
        timestamp: Optional[int] = None
    ):
        """
        記錄每個時間步的數據
        
        Args:
            equity: 當前權益
            position: 當前持倉
            mid_price: 中間價
            volatility: 波動率（可選）
            timestamp: 時間戳（可選）
        """
        self.equity_history.append(equity)
        self.position_history.append(position)
        self.price_history.append(mid_price)
        if volatility is not None:
            self.volatility_history.append(volatility)
        if timestamp is not None:
            self.timestamps.append(timestamp)
    
    def record_trade(self, trade_info: Dict):
        """記錄交易"""
        self.trades.append(trade_info)
    
    def calculate_volatility_by_tick(self, window: int = 100) -> np.ndarray:
        """
        計算按 tick 的波動率
        
        Args:
            window: 滑動窗口大小
            
        Returns:
            波動率陣列（以 tick 為單位）
        """
        if len(self.price_history) < 2:
            return np.array([])
        
        prices = np.array(self.price_history)
        # Clean prices: replace NaN/Inf
        prices = np.nan_to_num(prices, nan=0.0, posinf=0.0, neginf=0.0)
        
        # 計算價格變化（以 tick 為單位）
        if self.tick_size > 0:
            with np.errstate(divide='ignore', invalid='ignore'):
                price_changes = np.diff(prices) / self.tick_size
            price_changes = np.nan_to_num(price_changes, nan=0.0, posinf=0.0, neginf=0.0)
        else:
            price_changes = np.diff(prices)
        
        # 計算滑動窗口的標準差（波動率）
        volatility_ticks = []
        for i in range(len(price_changes)):
            start_idx = max(0, i - window + 1)
            window_changes = price_changes[start_idx:i+1]
            if len(window_changes) > 0:
                vol = np.std(window_changes)
                if np.isfinite(vol):
                    volatility_ticks.append(vol)
                else:
                    volatility_ticks.append(0.0)
            else:
                volatility_ticks.append(0.0)
        
        return np.array(volatility_ticks)
    
    def plot_results(
        self,
        title: str = "Backtest Results",
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        繪製完整的結果圖表
        
        Args:
            title: 圖表標題
            save_path: 儲存路徑（可選）
            show: 是否顯示圖表
        """
        if len(self.equity_history) == 0:
            logger.warning("No data to plot")
            return
        
        n_plots = 4
        fig, axes = plt.subplots(n_plots, 1, figsize=(14, 12), sharex=True)
        fig.suptitle(title, fontsize=14, fontweight='bold')
        
        time_steps = np.arange(len(self.equity_history))
        
        # 1. Equity Curve
        ax1 = axes[0]
        equity = np.array(self.equity_history)
        # Clean equity values: replace NaN/Inf with 0
        equity = np.nan_to_num(equity, nan=0.0, posinf=0.0, neginf=0.0)
        initial = equity[0] if len(equity) > 0 else 0
        pnl = equity - initial
        
        ax1.plot(time_steps, equity, 'b-', linewidth=1.5, label='Equity')
        ax1.fill_between(time_steps, initial, equity, alpha=0.3,
                         where=(equity >= initial), color='green', label='Profit')
        ax1.fill_between(time_steps, initial, equity, alpha=0.3,
                         where=(equity < initial), color='red', label='Loss')
        ax1.axhline(y=initial, color='gray', linestyle='--', alpha=0.5)
        ax1.set_ylabel('Equity', fontsize=11)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # 計算並顯示關鍵指標
        if len(equity) > 1:
            max_equity = np.maximum.accumulate(equity)
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                drawdown = np.where(max_equity > 0, (max_equity - equity) / max_equity * 100, 0)
            max_dd = np.nanmax(drawdown) if len(drawdown) > 0 else 0.0
            
            # Calculate returns, avoiding division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                returns = np.where(equity[:-1] != 0, np.diff(equity) / equity[:-1], 0)
            returns = returns[np.isfinite(returns)]
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 * 24 * 60) if len(returns) > 0 and np.std(returns) > 0 else 0.0
            
            metrics_text = f'PnL: {pnl[-1]:+.2f} | Max DD: {max_dd:.2f}% | Sharpe: {sharpe:.2f}'
            ax1.set_title(metrics_text, fontsize=10, loc='right')
        
        # 2. Drawdown
        ax2 = axes[1]
        if len(equity) > 1:
            max_equity = np.maximum.accumulate(equity)
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                drawdown = np.where(max_equity > 0, (max_equity - equity) / max_equity * 100, 0)
            drawdown = np.nan_to_num(drawdown, nan=0.0, posinf=0.0, neginf=0.0)
            ax2.fill_between(time_steps, 0, -drawdown, color='red', alpha=0.5)
            ax2.set_ylabel('Drawdown (%)', fontsize=11)
            if len(drawdown) > 0:
                max_dd = np.nanmax(drawdown)
                if np.isfinite(max_dd) and max_dd > 0:
                    y_min = min(-max_dd * 1.1, -1)
                    if np.isfinite(y_min):
                        ax2.set_ylim([y_min, 0])
        ax2.grid(True, alpha=0.3)
        
        # 3. Position
        ax3 = axes[2]
        if len(self.position_history) > 0:
            positions = np.array(self.position_history)
            # Clean position values: replace NaN/Inf with 0
            positions = np.nan_to_num(positions, nan=0.0, posinf=0.0, neginf=0.0)
            ax3.plot(time_steps[:len(positions)], positions, 'purple', linewidth=1)
            ax3.fill_between(time_steps[:len(positions)], 0, positions,
                           where=(positions >= 0), color='green', alpha=0.3)
            ax3.fill_between(time_steps[:len(positions)], 0, positions,
                           where=(positions < 0), color='red', alpha=0.3)
            ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax3.set_ylabel('Position', fontsize=11)
        ax3.grid(True, alpha=0.3)
        
        # 4. Volatility by Tick
        ax4 = axes[3]
        volatility_ticks = self.calculate_volatility_by_tick()
        if len(volatility_ticks) > 0:
            # Clean volatility values: replace NaN/Inf with 0
            volatility_ticks = np.nan_to_num(volatility_ticks, nan=0.0, posinf=0.0, neginf=0.0)
            vol_time_steps = time_steps[1:len(volatility_ticks)+1]
            ax4.plot(vol_time_steps, volatility_ticks, 'orange', linewidth=1.5, label='Volatility (ticks)')
            ax4.fill_between(vol_time_steps, 0, volatility_ticks, alpha=0.3, color='orange')
            
            # 顯示平均波動率
            avg_vol = np.mean(volatility_ticks)
            if np.isfinite(avg_vol):
                ax4.axhline(y=avg_vol, color='red', linestyle='--', alpha=0.7, 
                           label=f'Avg: {avg_vol:.2f} ticks')
            ax4.legend(loc='upper right')
        ax4.set_ylabel('Volatility (ticks)', fontsize=11)
        ax4.set_xlabel('Time Steps', fontsize=11)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Results saved to {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close(fig)
    
    def print_summary(self):
        """打印結果摘要"""
        if len(self.equity_history) == 0:
            logger.warning("No data to summarize")
            return
        
        equity = np.array(self.equity_history)
        initial = equity[0]
        final = equity[-1]
        pnl = final - initial
        pnl_pct = (pnl / initial * 100) if initial > 0 else 0
        
        # 計算最大回撤
        if len(equity) > 1:
            max_equity = np.maximum.accumulate(equity)
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                drawdown = np.where(max_equity > 0, (max_equity - equity) / max_equity * 100, 0)
            drawdown = np.nan_to_num(drawdown, nan=0.0, posinf=0.0, neginf=0.0)
            max_dd = np.nanmax(drawdown) if len(drawdown) > 0 else 0.0
            
            # Calculate returns, avoiding division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                returns = np.where(equity[:-1] != 0, np.diff(equity) / equity[:-1], 0)
            returns = returns[np.isfinite(returns)]
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 * 24 * 60) if len(returns) > 0 and np.std(returns) > 0 else 0.0
        else:
            max_dd = 0.0
            sharpe = 0.0
        
        # 計算波動率統計
        volatility_ticks = self.calculate_volatility_by_tick()
        avg_vol = np.mean(volatility_ticks) if len(volatility_ticks) > 0 else 0.0
        max_vol = np.max(volatility_ticks) if len(volatility_ticks) > 0 else 0.0
        
        # 持倉統計
        if len(self.position_history) > 0:
            positions = np.array(self.position_history)
            avg_position = np.mean(positions)
            max_position = np.max(positions)
            min_position = np.min(positions)
        else:
            avg_position = max_position = min_position = 0.0
        
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"\nCapital:")
        print(f"   Initial Equity:  {initial:>15,.2f}")
        print(f"   Final Equity:    {final:>15,.2f}")
        print(f"   PnL:             {pnl:>+15,.2f} ({pnl_pct:+.2f}%)")
        
        print(f"\nRisk Metrics:")
        print(f"   Sharpe Ratio:    {sharpe:>15.2f}")
        print(f"   Max Drawdown:    {max_dd:>15.2f}%")
        
        print(f"\nVolatility (by tick):")
        print(f"   Average:         {avg_vol:>15.2f} ticks")
        print(f"   Maximum:         {max_vol:>15.2f} ticks")
        
        print(f"\nPosition:")
        print(f"   Average:         {avg_position:>15.4f}")
        print(f"   Maximum Long:    {max_position:>15.4f}")
        print(f"   Maximum Short:   {min_position:>15.4f}")
        
        print(f"\nTrades:")
        print(f"   Total Trades:    {len(self.trades):>15}")
        
        print("=" * 60 + "\n")
    
    def save_to_file(self, filepath: str):
        """
        儲存結果到檔案
        
        Args:
            filepath: 儲存路徑
        """
        data = {
            'equity_history': self.equity_history,
            'position_history': self.position_history,
            'price_history': self.price_history,
            'volatility_history': self.volatility_history,
            'trades': self.trades,
            'tick_size': self.tick_size
        }
        
        np.savez_compressed(filepath, **data)
        logger.info(f"Results saved to {filepath}")


def create_simple_report(
    equity_history: List[float],
    position_history: List[float],
    price_history: List[float],
    tick_size: float = 0.1,
    title: str = "Backtest Results",
    save_path: Optional[str] = None
):
    """
    簡單的報告生成函數
    
    Args:
        equity_history: 權益歷史
        position_history: 持倉歷史
        price_history: 價格歷史
        tick_size: 最小價格變動單位
        title: 報告標題
        save_path: 儲存路徑（可選）
    """
    viewer = ResultViewer(tick_size=tick_size)
    
    # 填充數據
    for i in range(len(equity_history)):
        viewer.record_step(
            equity=equity_history[i],
            position=position_history[i] if i < len(position_history) else 0.0,
            mid_price=price_history[i] if i < len(price_history) else 0.0
        )
    
    # 打印摘要
    viewer.print_summary()
    
    # 繪製圖表
    viewer.plot_results(title=title, save_path=save_path, show=True)


if __name__ == "__main__":
    # 測試範例
    np.random.seed(42)
    n_steps = 1000
    
    # 模擬數據
    returns = np.random.randn(n_steps) * 0.001 + 0.0001
    equity = 30000 * (1 + returns).cumprod()
    positions = np.cumsum(np.random.randn(n_steps) * 0.5)
    positions = np.clip(positions, -10, 10)
    prices = 50000 + np.cumsum(np.random.randn(n_steps) * 10)
    
    viewer = ResultViewer(tick_size=0.1)
    for i in range(n_steps):
        viewer.record_step(
            equity=equity[i],
            position=positions[i],
            mid_price=prices[i]
        )
    
    viewer.print_summary()
    viewer.plot_results(title="Test Results")

