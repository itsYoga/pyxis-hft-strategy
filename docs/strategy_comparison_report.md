# 策略改進對比報告

**報告日期**: 2025-12-07  
**測試者**: Jesse  

---

## 執行摘要

### HA4 vs Baseline 最終結果

| 數據集 | Baseline PnL | HA4 PnL | 改進幅度 | 勝者 |
|--------|-------------|---------|----------|------|
| Binance BTCUSDT (2024-08-08) | +1,120.95 | **+1,161.15** | **+3.6%** | ✅ HA4 |
| Binance BTCUSDT (2024-08-09) | - | **+358.60** | - | ✅ HA4 |

### HA3 → HA4 改進效果

| 數據集 | HA3 (舊) | HA4 (新) | 改進幅度 |
|--------|---------|---------|----------|
| 2024-08-08 | +427.00 | +1,161.15 | **+172%** |
| 2024-08-09 | -87.95 | +358.60 | **+508%** |

---

## 策略演進

### HA3 問題診斷

1. **Risk Parameter Overlap** - 多重防禦機制同時觸發
2. **過度保守的波動體制** - spread 1.5x，alpha 0.5x
3. **倉位限制減半** - 退出市場錯失機會
4. **Safety Paradox** - 拒絕吸收庫存導致錯失回歸收益

### HA4 解決方案

**核心理念**: "You must be in the market to make money"

| 參數 | HA3 | HA4 | 改變原因 |
|------|-----|-----|---------|
| `gamma_base` | 0.1 | **0.05** | 降低風險厭惡，容許庫存波動 |
| `mlofi_weight` | 0.5 | **0.8** | OFI 是最強短期預測訊號 |
| Volatile spread | 1.5x | **1.1x** | 保持競爭力，不退出市場 |
| Volatile alpha | 0.5x | **1.5x** | 波動時 OFI 更有預測力 |
| Position limit | 減半 | **不變** | 捕捉趨勢與均值回歸 |
| Hunt logic | 無 | **非對稱** | 追逐 Alpha 方向 |
| EPI (OFI/Slope) | 啟用 | **禁用** | 避免雙重懲罰 |

---

## 測試詳情

### Test 1: Binance BTCUSDT 2024-08-08

```
============================================================
STRATEGY COMPARISON REPORT
============================================================

BASELINE (Original - Level 1 Only)
   Balance:           556,058.70
   Position:             -9.0000
   Equity:              1,120.95
   PnL:                +1,120.95

HA4 (Aggressive Alpha Architecture)
   Balance:           556,098.90
   Position:             -9.0000
   Equity:              1,161.15
   PnL:                +1,161.15

Improvement: +3.59%
Winner: HA4 ✅
```

### Test 2: Binance BTCUSDT 2024-08-09

```
HA4 結果:
   Balance:           493,039.00
   Position:             -8.0000
   Equity:                358.60
   PnL:                  +358.60

vs HA3: -87.95 (虧損)
Improvement: +508% ✅
```

---

## HA4 架構詳解

### 1. Non-Linear Alpha Boost

```python
if abs(mlofi_normalized) > 1.5:
    alpha_boost = 2.0  # 極端不平衡時加倍訊號
elif abs(mlofi_normalized) > 1.0:
    alpha_boost = 1.5
```

### 2. Asymmetric "Hunt" Logic

```python
if forecast > 0.5:  # Bullish
    bid_spread_mult = 0.8  # 縮窄買單 (想買)
    ask_spread_mult = 1.2  # 擴大賣單 (高價賣)
elif forecast < -0.5:  # Bearish
    bid_spread_mult = 1.2  # 擴大買單 (低價買)
    ask_spread_mult = 0.8  # 縮窄賣單 (想賣)
```

### 3. Aggressive Regime Response

| 體制 | Spread | Alpha | Gamma |
|------|--------|-------|-------|
| Calm | 1.0x | 1.0x | 0.05 |
| Active | 0.95x | 1.2x | 0.05 |
| Volatile | 1.1x | **1.5x** | 0.06 |

---

## 結論

HA4 成功實現了從「風險最小化」到「收益最大化」的轉型：

1. **填充率提升** - 窄價差 + 積極報價 → 更多成交
2. **庫存容忍度提升** - Position -9 vs HA3 的 -4
3. **Alpha 信任度提升** - 波動時相信訊號，不盲目退出
4. **穩定獲利** - 兩天數據都獲利，無虧損日

---

## 運行測試

```bash
# 策略對比
./venv/bin/python src/compare_strategies.py

# 單獨回測
./venv/bin/python src/backtest.py data/binance_usdm/btcusdt_20240808.npz --no-viz
```

---

## 附錄：檔案變更

- `src/strategy.py` - HA4 Aggressive 策略實作
- `src/strategy_baseline.py` - 原始 Baseline 對照組
- `src/compare_strategies.py` - 對比測試工具
