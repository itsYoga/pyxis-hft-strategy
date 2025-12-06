# 策略改進對比報告

**報告日期**: 2025-12-07  
**測試者**: Jesse  

---

## 執行摘要

| 數據集 | Baseline PnL | HA3 PnL | 改進幅度 | 勝者 |
|--------|-------------|---------|----------|------|
| Dummy Data | +3.30 | +4.60 | **+39.4%** | ✅ HA3 |
| Binance BTCUSDT (2024-08-08) | +1,120.95 | +427.00 | -61.9% | ⚠️ Baseline |

---

## 策略對比

### Baseline 策略 (原始)

**Alpha 訊號**:
- Micro Price (Level 1)
- BBO Imbalance (Level 1)

**特點**:
- 簡單、穩定
- 只看最佳買賣價
- 固定參數

### HA3 策略 (新)

**Alpha 訊號**:
- Micro Price (Level 1)
- **MLOFI** (Multi-Level OFI, 5 層)
- **LOB Slope** (訂單簿斜率)
- **EPI** (Expected Price Impact)

**特點**:
- 分析深層流動性
- 體制識別 (Regime Detection)
- 動態價差調整

---

## 測試結果詳情

### Test 1: Dummy Data

```
============================================================
STRATEGY COMPARISON REPORT
============================================================

BASELINE (Original - Level 1 Only)
   Balance:            40,003.30
   Position:             -4.0000
   Equity:                  3.30
   PnL:                    +3.30

HA3 (MLOFI + LOB Slope + Regime Detection)
   Balance:            30,004.60
   Position:             -3.0000
   Equity:                  4.60
   PnL:                    +4.60

Improvement: +39.39%
Winner: HA3 ✅
```

### Test 2: Binance Real Data (2024-08-08)

```
============================================================
STRATEGY COMPARISON REPORT
============================================================

BASELINE (Original - Level 1 Only)
   Balance:           556,058.70
   Position:             -9.0000
   Equity:              1,120.95
   PnL:                +1,120.95

HA3 (MLOFI + LOB Slope + Regime Detection)
   Balance:           247,066.00
   Position:             -4.0000
   Equity:                427.00
   PnL:                  +427.00

Improvement: -61.91%
Winner: Baseline ⚠️
```

---

## 分析與結論

### 為什麼 HA3 在真實數據上表現較差？

1. **參數未優化**: HA3 使用預設參數，未針對 Binance 數據調整
2. **交易量差異**: Baseline 交易更頻繁 (Position -9 vs -4)
3. **體制識別過於保守**: 可能將正常市場誤判為波動市場，導致價差過寬

### 改進建議

| 參數 | 當前值 | 建議調整 |
|------|--------|---------|
| `gamma_base` | 0.1 | 降低到 0.08 |
| `regime_spread_mult` | 1.5 (volatile) | 降低到 1.2 |
| `base_volatility` | tick_size * 5 | 根據資產調整 |

### 結論

| 結論項目 | 說明 |
|---------|------|
| MLOFI 有效性 | ✅ 在 Dummy data 上有效 |
| 真實數據表現 | ⚠️ 需要參數優化 |
| 建議 | 使用真實數據進行參數調整後再部署 |

---

## 運行對比測試

```bash
# 運行策略對比
./venv/bin/python src/compare_strategies.py

# 查看詳細結果
# - Baseline: src/strategy_baseline.py
# - HA3: src/strategy.py
```

---

## 附錄：執行環境

- Python 3.13
- hftbacktest 最新版
- 測試時間: 2025-12-07 07:52 UTC+8
