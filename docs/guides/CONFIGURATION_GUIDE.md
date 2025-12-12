# 配置參數優化指南

本指南說明如何調整策略配置參數以優化性能。

## 📊 測試結果摘要

### 數據集 1: BTCUSDT 2024-08-08
- **Baseline PnL**: -28,879.05
- **Aggressive PnL**: -28,838.85
- **改進**: +40.20 (+0.14%)
- **執行時間**: Aggressive 更快 (0.78s vs 1.05s)

### 數據集 2: BTCUSDT 2024-08-09
- **PnL**: +358.60
- **執行時間**: 2.08 秒

---

## 🎯 核心參數調整

### 1. 風險厭惡係數 (gamma_base)

**當前值**: `0.05`

**作用**: 控制策略的積極程度
- **較低值** (0.01-0.03): 更積極，更大持倉，更多交易
- **較高值** (0.1-0.2): 更保守，較小持倉，較少交易

**調整建議**:
```yaml
parameters:
  gamma_base: 0.03  # 更積極（增加交易頻率）
  # 或
  gamma_base: 0.08  # 更保守（降低風險）
```

**影響**:
- 降低 `gamma_base` → 增加交易頻率，但可能增加風險
- 提高 `gamma_base` → 減少交易頻率，但可能錯失機會

---

### 2. 價差參數 (k_base)

**當前值**: `1.5`

**作用**: 控制基礎價差寬度
- **較低值** (1.0-1.2): 更緊的價差，更高成交率
- **較高值** (2.0-3.0): 更寬的價差，更高利潤但成交率低

**調整建議**:
```yaml
parameters:
  k_base: 1.2  # 更緊的價差（競爭性更強）
  # 或
  k_base: 2.0  # 更寬的價差（利潤更高）
```

**影響**:
- 降低 `k_base` → 更緊價差，更多成交，但利潤率可能降低
- 提高 `k_base` → 更寬價差，更少成交，但單筆利潤更高

---

### 3. Alpha 權重

**當前值**:
- `micro_weight: 0.2` (Micro Price)
- `mlofi_weight: 0.8` (Multi-Level OFI)
- `slope_weight: 0.0` (LOB Slope - 已禁用)

**作用**: 控制不同 Alpha 信號的權重

**調整建議**:
```yaml
parameters:
  # 更信任 Micro Price
  micro_weight: 0.4
  mlofi_weight: 0.6
  
  # 或啟用 LOB Slope（需謹慎）
  micro_weight: 0.2
  mlofi_weight: 0.6
  slope_weight: 0.2
```

**影響**:
- 增加 `mlofi_weight` → 更依賴多層級訂單流不平衡（推薦）
- 增加 `micro_weight` → 更依賴微觀價格
- 啟用 `slope_weight` → 可能導致雙重懲罰，需謹慎

---

### 4. 多層級深度 (num_levels)

**當前值**: `5`

**作用**: 使用多少層訂單簿深度計算 MLOFI

**調整建議**:
```yaml
parameters:
  num_levels: 3   # 只使用前 3 層（更快，但信息較少）
  # 或
  num_levels: 10  # 使用前 10 層（更準確，但計算更慢）
```

**影響**:
- 增加 `num_levels` → 更多信息，但計算成本更高
- 減少 `num_levels` → 更快，但可能錯失深層信息

---

### 5. OFI 衰減因子 (ofi_decay)

**當前值**: `0.7`

**作用**: 控制不同層級的權重衰減
- **較低值** (0.5): 更重視深層訂單簿
- **較高值** (0.9): 更重視淺層訂單簿

**調整建議**:
```yaml
parameters:
  ofi_decay: 0.5  # 更重視深層（適合大單市場）
  # 或
  ofi_decay: 0.9  # 更重視淺層（適合快速變化市場）
```

---

### 6. 最大持倉 (max_position)

**當前值**: `10.0`

**作用**: 允許的最大持倉量

**調整建議**:
```yaml
parameters:
  max_position: 5.0   # 更保守（降低風險）
  # 或
  max_position: 20.0  # 更積極（增加機會）
```

**影響**:
- 降低 `max_position` → 降低風險，但可能限制盈利
- 提高 `max_position` → 增加機會，但風險更高

---

## 🔄 體制特定參數

### Calm Regime (平靜市場)

**當前值**:
```yaml
calm:
  spread_mult: 1.0
  alpha_mult: 1.0
  gamma_mult: 1.0
  vol_threshold: 1.0
```

**調整建議**:
```yaml
calm:
  spread_mult: 0.9   # 更緊的價差（競爭性）
  alpha_mult: 1.1    # 稍微信任 Alpha
```

---

### Active Regime (活躍市場)

**當前值**:
```yaml
active:
  spread_mult: 0.95
  alpha_mult: 1.2
  vol_threshold: 2.0
```

**調整建議**:
```yaml
active:
  spread_mult: 0.9   # 更緊的價差
  alpha_mult: 1.3    # 更信任 Alpha
```

---

### Volatile Regime (波動市場)

**當前值**:
```yaml
volatile:
  spread_mult: 1.1
  alpha_mult: 1.5
  gamma_mult: 1.2
```

**調整建議**:
```yaml
volatile:
  spread_mult: 1.2   # 更寬的價差（保護）
  alpha_mult: 1.8    # 更信任 Alpha（捕捉趨勢）
  gamma_mult: 1.5   # 更保守（降低風險）
```

---

## 🚀 Alpha Boost 配置

**當前值**:
```yaml
alpha_boost:
  enabled: true
  extreme_threshold: 1.5
  extreme_mult: 2.0
  high_threshold: 1.0
  high_mult: 1.5
```

**調整建議**:
```yaml
alpha_boost:
  enabled: true
  extreme_threshold: 2.0  # 提高極端閾值（更謹慎）
  extreme_mult: 2.5       # 增加極端乘數（更積極）
```

---

## 🎯 優化策略示例

### 策略 1: 高頻交易（更積極）

```yaml
parameters:
  gamma_base: 0.03          # 降低風險厭惡
  k_base: 1.2               # 更緊的價差
  mlofi_weight: 0.9        # 更信任 MLOFI
  max_position: 15.0        # 更大的持倉
```

### 策略 2: 保守做市（更安全）

```yaml
parameters:
  gamma_base: 0.1           # 提高風險厭惡
  k_base: 2.0               # 更寬的價差
  mlofi_weight: 0.7        # 平衡權重
  max_position: 5.0         # 更小的持倉
```

### 策略 3: 趨勢捕捉（信任 Alpha）

```yaml
parameters:
  gamma_base: 0.05
  k_base: 1.5
  mlofi_weight: 0.9
  alpha_boost:
    extreme_mult: 2.5       # 更強的 Alpha boost
  regime:
    volatile:
      alpha_mult: 2.0       # 波動時更信任 Alpha
```

---

## 📝 測試流程

### 1. 創建測試配置

```bash
# 複製默認配置
cp config/strategy_aggressive.yaml config/strategy_test.yaml

# 編輯配置
vim config/strategy_test.yaml
```

### 2. 運行回測

```bash
cd src
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --config ../config/strategy_test.yaml
```

### 3. 對比結果

```bash
# 運行對比測試
python3 compare_strategies.py
```

### 4. 記錄結果

建議記錄：
- PnL
- Sharpe Ratio
- Max Drawdown
- 交易次數
- 執行時間

---

## ⚠️ 注意事項

1. **參數相互影響**: 調整一個參數可能影響其他參數的效果
2. **過度優化**: 避免針對單一數據集過度優化（過擬合）
3. **風險管理**: 降低 `gamma_base` 或提高 `max_position` 會增加風險
4. **回測 vs 實盤**: 回測結果可能與實盤有差異，需謹慎驗證

---

## 🔍 診斷工具

### 檢查當前配置

```bash
cat config/strategy_aggressive.yaml
```

### 查看日誌

```bash
tail -f logs/backtest.log
```

### 分析結果

查看 `result_viewer` 輸出的：
- Sharpe Ratio
- Max Drawdown
- Volatility by Tick
- Position History

---

## 📚 參考資料

- [如何運行策略](./HOW_TO_RUN.md)
- [策略對比報告](./strategy_comparison_report.md)
- [專案分析與改進報告](./專案分析與改進報告.md)

---

## 💡 優化建議

1. **從核心參數開始**: 先調整 `gamma_base` 和 `k_base`
2. **逐步調整**: 一次只調整一個參數，觀察效果
3. **多數據集測試**: 在不同數據集上測試，確保穩定性
4. **記錄變化**: 記錄每次調整的結果，便於回溯
5. **風險優先**: 優先考慮風險管理，再追求收益

