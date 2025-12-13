# 測試策略優化效果指南

## 概述

本指南說明如何測試和驗證策略優化的效果。

---

## 快速測試

### 方法 1: 使用自動化測試腳本（推薦）

```bash
# 運行優化測試
python src/tests/test_optimizations.py
```

這個腳本會：
1. 運行 Baseline 策略
2. 運行優化後的 Aggressive 策略
3. 對比結果並生成報告

---

## 詳細測試步驟

### 步驟 1: 準備測試環境

```bash
# 確保虛擬環境已激活
source venv/bin/activate

# 確認數據文件存在
ls data/binance_usdm/btcusdt_20240808.npz
ls data/binance_usdm/btcusdt_20240808_eod.npz
```

### 步驟 2: 運行單個策略回測

#### 測試 Baseline 策略

```bash
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz \
    --no-viz
```

記錄結果：
- PnL
- 手續費
- 最大持倉
- 執行時間

#### 測試優化後的策略

```bash
# 優化後的策略（默認啟用所有優化）
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz \
    --no-viz
```

### 步驟 3: 使用策略對比工具

```bash
# 運行對比測試
python src/tests/compare_strategies.py
```

這會自動比較：
- Baseline vs Aggressive (優化後)

---

## 測試個別優化

### 測試二次庫存懲罰

1. **編輯策略文件** `src/strategies/aggressive.py`：

```python
# 啟用二次庫存懲罰
use_quadratic_penalty = True

# 禁用其他優化（用於對比）
use_anti_sniffing = False
use_exponential_decay_mlofi = False
```

2. **運行回測**：

```bash
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz \
    --no-viz
```

3. **記錄結果**，然後禁用二次庫存懲罰：

```python
use_quadratic_penalty = False
```

4. **再次運行回測**並對比結果

### 測試反嗅探邏輯

類似地，可以單獨測試反嗅探邏輯：

```python
use_quadratic_penalty = False
use_anti_sniffing = True  # 只啟用這個
use_exponential_decay_mlofi = False
```

### 測試指數衰減 MLOFI

```python
use_quadratic_penalty = False
use_anti_sniffing = False
use_exponential_decay_mlofi = True  # 只啟用這個
```

---

## 關鍵指標分析

### 1. PnL（損益）

**目標：** 優化後 PnL 應該提高或至少不降低

```python
improvement = optimized_pnl - baseline_pnl
improvement_pct = (improvement / abs(baseline_pnl)) * 100
```

**判斷標準：**
- ✅ 改進 > 5%：優化有效
- ⚠️ 改進 0-5%：需要更多測試
- ❌ 改進 < 0%：需要調整參數或禁用該優化

### 2. 庫存分佈

**檢查點：**
- 最大持倉是否降低（二次懲罰的效果）
- 庫存是否更接近零（更好的庫存管理）

**分析方法：**
在回測中添加庫存追蹤，繪製庫存分佈圖

### 3. 價差行為

**檢查點：**
- 平均價差是否合理
- 價差是否在庫存接近限制時擴大（二次懲罰）
- 價差是否更對稱（反嗅探的效果）

### 4. 填充率（Fill Rate）

**目標：** 優化不應顯著降低填充率

**計算：**
```
fill_rate = filled_orders / total_orders
```

### 5. 風險指標

- **Sharpe Ratio**: 應該提高或保持
- **Max Drawdown**: 應該降低或保持
- **Win Rate**: 應該提高或保持

---

## 多數據集測試

### 測試多個日期

```bash
# 測試第一天
python src/tests/test_optimizations.py

# 手動測試第二天
python src/core/backtest.py data/binance_usdm/btcusdt_20240809.npz \
    --snapshot data/binance_usdm/btcusdt_20240809_eod.npz \
    --no-viz
```

### 測試不同市場條件

- **平靜市場**：低波動率
- **活躍市場**：中等波動率
- **波動市場**：高波動率

---

## 統計顯著性測試

### 運行多次回測

```python
# 運行 N 次回測並計算統計量
results_baseline = []
results_optimized = []

for i in range(10):
    baseline_result = run_backtest(...)
    optimized_result = run_backtest(...)
    results_baseline.append(baseline_result['pnl'])
    results_optimized.append(optimized_result['pnl'])

# 計算統計量
from scipy import stats
t_stat, p_value = stats.ttest_rel(results_optimized, results_baseline)

if p_value < 0.05:
    print("✅ 改進具有統計顯著性")
else:
    print("⚠️  改進不顯著，需要更多數據")
```

---

## 參數敏感性測試

### 測試不同參數值

```python
# 測試不同的 lambda_read 值
for lambda_read in [0.1, 0.3, 0.5, 0.7]:
    # 修改策略參數
    # 運行回測
    # 記錄結果
```

### 參數網格搜索

創建參數組合並測試：

```python
param_grid = {
    'lambda_read': [0.2, 0.3, 0.4],
    'max_skew_penalty': [0.3, 0.5, 0.7],
    'alpha_decay': [0.3, 0.5, 0.7]
}
```

---

## 結果記錄模板

### 測試結果表格

| 策略版本 | PnL | 手續費 | 最大持倉 | Sharpe | Max DD | Win Rate | 執行時間 |
|---------|-----|--------|----------|--------|--------|----------|----------|
| Baseline | | | | | | | |
| Optimized | | | | | | | |
| 改進 | | | | | | | |

### 優化效果總結

```
測試日期: YYYY-MM-DD
數據集: BTCUSDT 2024-08-08

Baseline PnL: XXX.XX
Optimized PnL: XXX.XX
改進: +XX.XX (+XX.XX%)

關鍵發現:
1. [觀察 1]
2. [觀察 2]
3. [觀察 3]

建議:
- [建議 1]
- [建議 2]
```

---

## 常見問題

### Q: 優化後 PnL 降低了怎麼辦？

**A:** 
1. 檢查是否所有優化都應該啟用
2. 測試個別優化，找出問題所在
3. 調整參數（如降低 lambda_read）
4. 測試不同數據集

### Q: 如何知道哪個優化最有效？

**A:** 
1. 單獨測試每個優化
2. 記錄每個優化的獨立效果
3. 測試優化組合

### Q: 需要測試多少數據才足夠？

**A:** 
- 至少 2-3 個不同的交易日
- 涵蓋不同的市場條件（平靜/活躍/波動）
- 如果可能，測試 1-2 週的數據

---

## 自動化測試腳本

創建一個完整的測試套件：

```bash
# 運行完整測試套件
python src/tests/test_optimizations.py --full

# 測試特定優化
python src/tests/test_optimizations.py --optimization quadratic_penalty

# 多數據集測試
python src/tests/test_optimizations.py --all-datasets
```

---

## 下一步

1. ✅ 運行基本對比測試
2. ✅ 分析關鍵指標
3. ✅ 測試個別優化
4. ⏳ 多數據集驗證
5. ⏳ 參數調優
6. ⏳ 生產環境部署

---

*最後更新: 2025-12-07*

