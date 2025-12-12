"""
Test Result Viewer
==================
簡單測試結果展示工具
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.result_viewer import ResultViewer, create_simple_report
import numpy as np

def test_result_viewer():
    """測試結果展示器"""
    print("Testing Result Viewer...")
    print("=" * 60)
    
    # 模擬數據
    np.random.seed(42)
    n_steps = 1000
    tick_size = 0.1
    
    # 生成模擬的權益曲線
    returns = np.random.randn(n_steps) * 0.001 + 0.0001
    equity = 30000 * (1 + returns).cumprod()
    
    # 生成模擬的持倉
    positions = np.cumsum(np.random.randn(n_steps) * 0.5)
    positions = np.clip(positions, -10, 10)
    
    # 生成模擬的價格（帶波動）
    base_price = 50000
    price_changes = np.random.randn(n_steps) * 10
    prices = base_price + np.cumsum(price_changes)
    
    # 建立結果展示器
    viewer = ResultViewer(tick_size=tick_size)
    
    # 記錄每個時間步
    for i in range(n_steps):
        viewer.record_step(
            equity=equity[i],
            position=positions[i],
            mid_price=prices[i]
        )
    
    # 打印摘要
    viewer.print_summary()
    
    # 繪製圖表
    print("\nGenerating plots...")
    viewer.plot_results(
        title="Test Backtest Results",
        save_path="test_results.png",
        show=True
    )
    
    print("\n✓ Test completed!")

if __name__ == "__main__":
    test_result_viewer()

