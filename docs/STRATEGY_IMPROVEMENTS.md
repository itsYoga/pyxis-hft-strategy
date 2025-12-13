# 策略改進記錄

> 統一的策略改進實施記錄和狀態

---

## 改進概述

### 核心理念

**"You must be in the market to make money"**
- 優先考慮填充率而非每筆交易利潤
- 信任 alpha 信號，特別是在波動期間
- 最大化庫存周轉，而非最小化風險
- 防禦掠奪性算法和流動性毒性

---

## ✅ 已完成的改進

### Phase 1: 防禦機制 (2025-12-07)

#### 1.1 二次庫存懲罰 (Quadratic Inventory Penalty) ✅

**實現位置**: `src/strategies/aggressive.py`

**變更**:
- 將線性庫存偏斜改為二次懲罰
- 當庫存接近限制時，價差會更激進地擴大

**代碼變更**:
```python
# 舊版本（線性）
inventory_adjustment = position * regime_gamma * (volatility ** 2)

# 新版本（二次）
position_factor = abs(position) / max_position
inventory_adjustment = position * regime_gamma * (volatility ** 2) * (1.0 + position_factor)
```

**參數**:
- `use_quadratic_penalty = True` (可切換)

**預期效果**:
- 更嚴格的庫存邊界控制
- 減少"bag holder"風險
- 更快的庫存清算速度

---

#### 1.2 反嗅探邏輯 (Anti-Sniffing Logic) ✅

**實現位置**: `src/strategies/aggressive.py`

**機制**:
- 當庫存偏斜過於明顯時，將報價稍微拉回中間價
- 減少被"價格讀取"算法識別的風險

**代碼變更**:
```python
# 計算反嗅探調整
normalized_position = position / max_position
obvious_skew = abs(skew)
sniff_penalty = lambda_read * obvious_skew * tick_size
sniff_penalty = max(-max_skew_penalty * tick_size, min(max_skew_penalty * tick_size, sniff_penalty))

# 應用調整
bid_price = reservation_price - half_spread * bid_spread_mult * (1 + skew) + bid_sniff_adjust
ask_price = reservation_price + half_spread * ask_spread_mult * (1 - skew) + ask_sniff_adjust
```

**參數**:
- `use_anti_sniffing = True` (可切換)
- `lambda_read = 0.3` (反嗅探懲罰係數)
- `max_skew_penalty = 0.5` (最大偏斜調整，以 tick 為單位)

**預期效果**:
- 減少被掠奪性交易者識別的風險
- 降低被 front-run 的概率
- 略微減慢庫存清算速度（權衡）

---

### Phase 3: 優化 MLOFI (2025-12-07)

#### 3.1 指數衰減 MLOFI ✅

**實現位置**: `src/strategies/aggressive.py`

**變更**:
- 將 MLOFI 的權重衰減從冪次衰減改為指數衰減
- 給 Level 1-2 更高權重，同時仍考慮深層訂單簿壓力

**代碼變更**:
```python
# 舊版本（冪次衰減）
weight = ofi_decay ** i  # 0.7^i

# 新版本（指數衰減）
weight = np.exp(-alpha_decay * i)  # e^(-0.5*i)
```

**參數**:
- `use_exponential_decay_mlofi = True` (可切換)
- `alpha_decay = 0.5` (指數衰減係數)

**預期效果**:
- 提高預測準確度
- 降低深層訂單簿的"欺騙"影響
- 更好的信噪比

---

### Phase 4: 風險管理增強 (2025-12-13)

#### 4.1 止損機制 ✅

**實現位置**: `src/strategies/aggressive_enhanced.py`

**機制**:
- 限制單筆交易最大虧損
- 限制總虧損閾值
- 動態價差調整

**參數**:
- `max_loss_per_trade = 50.0` (單筆交易最大虧損)
- `max_total_loss = 200.0` (最大總虧損)
- `stop_loss_enabled = True` (可切換)

---

#### 4.2 市場狀態過濾 ✅

**實現位置**: `src/strategies/aggressive_enhanced.py`

**機制**:
- 高波動率時暫停交易
- 最小價差比例檢查
- 只在有利的市場條件下交易

**參數**:
- `high_volatility_threshold = 3.0` (波動率閾值)
- `min_spread_ratio = 0.5` (最小價差比例)
- `market_state_filter_enabled = True` (可切換)

---

## ⏳ 計劃中的改進

### Phase 2: 流動性毒性檢測

#### 2.1 VPIN 計算器 ⏳

**狀態**: 已創建工具，待集成到策略

**文件**: `src/utils/vpin.py`

**下一步**:
- 創建 numba 兼容的 VPIN 計算函數
- 在策略主循環中集成毒性檢測
- 實現毒性響應邏輯（擴大價差或取消訂單）

---

### Phase 5: 隊列位置模擬

**狀態**: 未開始

**需求**:
- 需要修改 hftbacktest 引擎或自定義訂單填充邏輯
- 實現概率隊列位置追蹤
- 添加 reduce ratio 邏輯

---

### Phase 6: DRL 架構

**狀態**: 未開始

**需求**:
- 設計狀態空間
- 實現獎勵函數
- 訓練和評估 RL 代理

---

### Phase 7: HMM 體制檢測

**狀態**: 未開始

**需求**:
- 實現 HMM 模型
- 替換硬編碼的波動率閾值
- 訓練體制分類器

---

## 策略版本對比

### Baseline vs Aggressive

| 參數 | Baseline | Aggressive | 改變原因 |
|------|----------|------------|---------|
| `gamma_base` | 0.1 | **0.05** | 降低風險厭惡，容許庫存波動 |
| `mlofi_weight` | 0.5 | **0.8** | OFI 是最強短期預測訊號 |
| Volatile spread | 1.5x | **1.1x** | 保持競爭力，不退出市場 |
| Volatile alpha | 0.5x | **1.5x** | 波動時 OFI 更有預測力 |
| Position limit | 減半 | **不變** | 捕捉趨勢與均值回歸 |
| Hunt logic | 無 | **非對稱** | 追逐 Alpha 方向 |
| EPI (OFI/Slope) | 啟用 | **禁用** | 避免雙重懲罰 |

---

## 配置選項

所有優化都可以通過策略參數開關：

```python
# Phase 1: 防禦機制
use_quadratic_penalty = True      # 二次庫存懲罰
use_anti_sniffing = True          # 反嗅探邏輯
lambda_read = 0.3                 # 反嗅探係數
max_skew_penalty = 0.5            # 最大偏斜調整

# Phase 3: MLOFI 優化
use_exponential_decay_mlofi = True  # 指數衰減
alpha_decay = 0.5                   # 衰減係數

# Phase 4: 風險管理
stop_loss_enabled = True            # 止損機制
market_state_filter_enabled = True  # 市場狀態過濾
```

---

## 測試建議

### 單元測試
- [ ] 測試二次庫存懲罰計算
- [ ] 測試反嗅探邏輯調整
- [ ] 測試指數衰減 MLOFI
- [ ] 測試止損機制
- [ ] 測試市場狀態過濾

### 回測驗證
- [x] 比較優化前後的 PnL ✅
- [ ] 測量庫存分佈變化
- [ ] 評估價差行為
- [ ] 檢查填充率影響

### 性能指標
- [x] PnL ✅
- [ ] Sharpe Ratio
- [ ] Max Drawdown
- [ ] Win Rate
- [ ] Fill Rate
- [ ] Inventory Distribution

---

## 版本歷史

- **2025-12-13**: 
  - ✅ 止損機制實施
  - ✅ 市場狀態過濾實施
  - ✅ PnL 計算修復
  - ✅ 保守版本策略創建
  - ✅ 參數掃描工具創建

- **2025-12-07**: 
  - ✅ Phase 1: 二次庫存懲罰實施
  - ✅ Phase 1: 反嗅探邏輯實施
  - ✅ Phase 3: 指數衰減 MLOFI 實施

---

*最後更新: 2025-12-13*

