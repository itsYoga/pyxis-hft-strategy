# 如何測試優化效果

## 🎯 三種測試方法（從簡單到詳細）

---

## 方法 1: 最簡單 - 使用對比腳本 ⭐ 推薦

### 一步完成測試

```bash
# 運行自動對比測試
python src/tests/compare_strategies.py
```

**這會自動：**
- ✅ 運行 Baseline 策略
- ✅ 運行優化後的 Aggressive 策略  
- ✅ 對比結果並顯示改進百分比

**輸出示例：**
```
============================================================
STRATEGY COMPARISON REPORT
============================================================

BASELINE (Original - Level 1 Only)
------------------------------------------------------------
   PnL:          +1,120.95
   Time:              2.05s

AGGRESSIVE (Multi-Level OFI + Regime Detection)
------------------------------------------------------------
   PnL:          +1,250.30
   Time:              2.12s

SUMMARY
============================================================
   Baseline PnL:     +1,120.95
   Aggressive PnL:   +1,250.30
   Improvement:      +11.54%
   Winner:           Aggressive
```

**判斷標準：**
- ✅ **優化成功**：如果 Aggressive PnL > Baseline PnL
- ⚠️ **需要調整**：如果 Aggressive PnL < Baseline PnL

---

## 方法 2: 手動對比兩個回測

### 步驟 1: 測試 Baseline

```bash
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz \
    --no-viz
```

**記錄關鍵數字：**
- PnL: `_______`
- Fee: `_______`
- Position: `_______`

### 步驟 2: 測試優化後的策略

```bash
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz \
    --no-viz
```

**記錄關鍵數字：**
- PnL: `_______`
- Fee: `_______`
- Position: `_______`

### 步驟 3: 計算改進

```
改進 = Optimized PnL - Baseline PnL
改進百分比 = (改進 / |Baseline PnL|) × 100%
```

**示例：**
```
Baseline PnL: +1,120.95
Optimized PnL: +1,250.30
改進: +129.35
改進百分比: +11.54%
```

---

## 方法 3: 詳細分析（使用測試腳本）

### 運行詳細測試

```bash
python src/tests/test_optimizations.py
```

**這會提供：**
- ✅ 詳細的對比報告
- ✅ 改進分析
- ✅ 建議和下一步

---

## 📊 關鍵指標檢查

### 1. PnL（最重要）

**目標：** Optimized PnL > Baseline PnL

```
改進 > 5%: ✅ 優化有效
改進 0-5%: ⚠️ 需要更多測試
改進 < 0%: ❌ 需要調整參數
```

### 2. 庫存管理

**檢查：**
- 最大持倉是否降低？（二次懲罰的效果）
- 庫存是否更接近零？（更好的管理）

**查看方法：**
```bash
# 啟用視覺化查看庫存曲線
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz
```

### 3. 風險指標

**理想情況：**
- Sharpe Ratio ↑（提高）
- Max Drawdown ↓（降低）
- Win Rate ↑（提高）

---

## 🧪 測試個別優化

如果想測試每個優化的獨立效果：

### 測試二次庫存懲罰

1. **編輯** `src/strategies/aggressive.py`：

```python
# 只啟用二次庫存懲罰
use_quadratic_penalty = True
use_anti_sniffing = False
use_exponential_decay_mlofi = False
```

2. **運行回測**並記錄結果

3. **禁用**並再次測試：

```python
use_quadratic_penalty = False
```

4. **對比結果**

### 測試反嗅探邏輯

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

## 📈 多數據集驗證

### 測試多個日期

```bash
# 第一天
python src/tests/compare_strategies.py

# 手動測試第二天（修改數據路徑）
python src/core/backtest.py data/binance_usdm/btcusdt_20240809.npz \
    --snapshot data/binance_usdm/btcusdt_20240809_eod.npz \
    --no-viz
```

**目標：** 優化在多個數據集上都表現更好

---

## ✅ 判斷標準

### 優化成功的標準

| 改進幅度 | 建議 |
|---------|------|
| **> 10%** | ✅ 強烈建議啟用所有優化 |
| **5-10%** | ✅ 建議啟用，但需要多數據集驗證 |
| **0-5%** | ⚠️ 可以啟用，但需要更多測試 |
| **< 0%** | ❌ 需要調整參數或禁用某些優化 |

---

## 📝 測試結果記錄

### 簡單記錄模板

```
測試日期: 2025-12-07
數據集: BTCUSDT 2024-08-08

Baseline:
- PnL: +1,120.95

Optimized:
- PnL: +1,250.30

改進: +129.35 (+11.54%)
結論: ✅ 優化有效
```

### 詳細記錄模板

```
測試日期: 2025-12-07
數據集: BTCUSDT 2024-08-08

Baseline 結果:
- PnL: +1,120.95
- Fee: 150.23
- Max Position: 8.5
- Execution Time: 2.05s

Optimized 結果:
- PnL: +1,250.30
- Fee: 145.67
- Max Position: 7.2
- Execution Time: 2.12s

改進分析:
- PnL 改進: +129.35 (+11.54%) ✅
- Fee 減少: -4.56 ✅
- Max Position 降低: -1.3 ✅ (更好的庫存控制)
- 執行時間: +0.07s (可接受)

結論:
✅ 優化有效，建議啟用所有優化
```

---

## 🚀 快速開始

### 最簡單的方法（推薦）

```bash
# 一步完成測試
python src/tests/compare_strategies.py
```

**如果結果顯示 Aggressive PnL > Baseline PnL，優化就成功了！**

---

## 📚 相關文檔

- [完整測試指南](TESTING_OPTIMIZATIONS.md) - 詳細的測試方法
- [快速測試指南](QUICK_TEST_GUIDE.md) - 快速參考
- [優化狀態](../reports/OPTIMIZATION_STATUS.md) - 當前實施狀態

---

*最後更新: 2025-12-07*

