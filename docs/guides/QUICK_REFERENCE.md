# 快速參考指南

## 🚀 快速命令

### 運行策略
```bash
cd src
source ../venv/bin/activate

# 基本運行
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz

# 不顯示圖表（更快）
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz --no-viz

# 使用自定義配置
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --config ../config/strategy_aggressive.yaml
```

### 策略對比
```bash
cd src
python3 compare_strategies.py
```

---

## 📊 測試結果摘要

| 數據集 | PnL | 執行時間 | 備註 |
|--------|------|----------|------|
| BTCUSDT 2024-08-08 | +1,161.15 | 2.05s | ✅ 最佳表現 |
| BTCUSDT 2024-08-09 | +358.60 | 2.08s | ✅ 穩定表現 |

### 策略對比 (2024-08-08)
- **Baseline**: -28,879.05
- **Aggressive**: -28,838.85
- **改進**: +40.20 (+0.14%)
- **執行時間**: Aggressive 更快 (0.78s vs 1.05s)

---

## ⚙️ 關鍵參數快速調整

### 更積極的策略
```yaml
parameters:
  gamma_base: 0.03      # 降低風險厭惡
  k_base: 1.2           # 更緊的價差
  max_position: 15.0    # 更大的持倉
```

### 更保守的策略
```yaml
parameters:
  gamma_base: 0.1       # 提高風險厭惡
  k_base: 2.0           # 更寬的價差
  max_position: 5.0      # 更小的持倉
```

### 信任 Alpha 的策略
```yaml
parameters:
  mlofi_weight: 0.9     # 更信任 MLOFI
alpha_boost:
  extreme_mult: 2.5     # 更強的 Alpha boost
```

---

## 📁 文件結構

```
pyxis-hft-strategy/
├── src/
│   ├── backtest.py              # 主回測腳本
│   ├── compare_strategies.py    # 策略對比
│   ├── strategy.py             # Aggressive 策略
│   └── strategy_baseline.py    # Baseline 策略
├── config/
│   └── strategy_aggressive.yaml # 配置文件
├── data/
│   └── binance_usdm/           # Binance 數據
└── docs/
    ├── HOW_TO_RUN.md           # 運行指南
    ├── CONFIGURATION_GUIDE.md   # 配置指南
    └── QUICK_REFERENCE.md       # 本文件
```

---

## 🔧 常用配置調整

### 1. 風險厭惡 (gamma_base)
- **低** (0.01-0.03): 更積極
- **中** (0.05): 默認
- **高** (0.1-0.2): 更保守

### 2. 價差參數 (k_base)
- **低** (1.0-1.2): 更緊價差
- **中** (1.5): 默認
- **高** (2.0-3.0): 更寬價差

### 3. Alpha 權重
- **mlofi_weight**: 0.8 (推薦保持)
- **micro_weight**: 0.2 (可調整)
- **slope_weight**: 0.0 (已禁用)

---

## 📈 性能指標

### 關鍵指標
- **PnL**: 總盈虧
- **Sharpe Ratio**: 風險調整後收益
- **Max Drawdown**: 最大回撤
- **Volatility**: 按 tick 的波動率

### 查看結果
```bash
# 查看日誌
tail -f logs/backtest.log

# 查看配置
cat config/strategy_aggressive.yaml
```

---

## 🐛 常見問題

### Q: 策略運行時間過長？
A: 使用 `--no-viz` 選項禁用視覺化

### Q: 沒有交易產生？
A: 檢查 `gamma_base` 是否過高，或 `k_base` 是否過大

### Q: PnL 為負？
A: 這是正常的，取決於市場條件和初始資本設置

### Q: 如何調整參數？
A: 編輯 `config/strategy_aggressive.yaml`，參考 [配置指南](./CONFIGURATION_GUIDE.md)

---

## 📚 相關文檔

- [如何運行策略](./HOW_TO_RUN.md) - 詳細運行指南
- [配置參數優化指南](./CONFIGURATION_GUIDE.md) - 參數調整詳解
- [策略對比報告](./strategy_comparison_report.md) - 性能對比
- [專案分析與改進報告](./專案分析與改進報告.md) - 完整分析

---

## 💡 優化建議

1. **從核心參數開始**: `gamma_base` 和 `k_base`
2. **逐步調整**: 一次一個參數
3. **多數據集測試**: 確保穩定性
4. **記錄結果**: 便於回溯和比較

---

**最後更新**: 2025-12-13

