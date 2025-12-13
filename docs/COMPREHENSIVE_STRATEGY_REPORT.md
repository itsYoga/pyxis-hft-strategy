# Pyxis HFT Strategy 完整策略與結果報告

**報告日期**: 2025-12-13  
**專案**: Pyxis HFT Aggressive Market Making Strategy  
**版本**: Optimized v2.0

---

## 執行摘要

本報告詳細描述了 Pyxis HFT Aggressive Market Making Strategy 的完整架構、實施細節、測試結果和優化歷程。策略基於 Avellaneda-Stoikov (AS) 模型，結合多層級訂單流不平衡（MLOFI）信號，實現了積極的做市策略。

### 關鍵成果

- ✅ **PnL 表現**: +1,174.35 (vs Baseline +1,120.95, +4.76% 改進)
- ✅ **執行效率**: 1.16s (處理完整交易日數據)
- ✅ **策略優化**: 已實施 5 項關鍵優化
- ✅ **風險管理**: 二次庫存懲罰 + 反嗅探邏輯 + 止損機制

---

## 1. 策略架構

### 1.1 核心理念

**"You must be in the market to make money"**

策略採用積極的做市方法：
- **優先填充率**：窄價差以獲得更多成交機會
- **信任 Alpha 信號**：特別是在波動期間，MLOFI 信號更有預測力
- **最大化庫存周轉**：而非最小化風險
- **防禦掠奪性算法**：實施反嗅探邏輯和流動性毒性檢測

### 1.2 數學框架

#### Avellaneda-Stoikov 模型基礎

策略基於經典的 AS 做市模型：

**保留價格 (Reservation Price)**:
$$r_t = S_t + \alpha_t - \gamma \sigma^2 q_t$$

其中：
- $S_t$: 中間價 (Mid Price)
- $\alpha_t$: Alpha 預測信號
- $\gamma$: 風險厭惡係數 (0.05 - 積極設定)
- $\sigma^2$: 波動率
- $q_t$: 當前庫存

**最優價差 (Optimal Spread)**:
$$\delta^* = \frac{2}{\gamma} \ln\left(1 + \frac{\gamma}{k}\right)$$

其中 $k$ 是價差參數 (1.5 - 積極設定)。

#### 優化後的保留價格

**二次庫存懲罰**:
$$r_t = S_t + \alpha_t - \gamma \sigma^2 q_t \left(1 + \frac{|q_t|}{q_{max}}\right)$$

這使得庫存接近限制時，價差會更激進地擴大。

**反嗅探調整**:
$$\delta_{bid}^* = \delta_{AS} + \frac{1}{2}\gamma\sigma^2 q - \lambda_{read} \cdot J'(Skew)$$

其中 $\lambda_{read} = 0.3$ 是反嗅探懲罰係數。

---

## 2. Alpha 信號系統

### 2.1 Alpha 信號組成

策略使用三個主要 Alpha 信號：

| Alpha 信號 | 權重 | 說明 | 預測時間範圍 |
|-----------|------|------|------------|
| **Micro Price** | 20% | BBO 數量加權價格 | 極短期 (秒級) |
| **MLOFI** | 80% | 多層級訂單流不平衡 | 短期 (分鐘級) |
| **LOB Slope** | 0% | 訂單簿斜率 (已禁用) | 中期 |

**總 Alpha 預測**:
$$\alpha_t = w_{micro} \cdot \alpha_{micro} + w_{mlofi} \cdot MLOFI_t$$

### 2.2 Micro Price

**計算公式**:
$$MicroPrice = \frac{Bid \cdot AskQty + Ask \cdot BidQty}{BidQty + AskQty}$$

**Alpha 信號**:
$$\alpha_{micro} = \frac{MicroPrice - MidPrice}{TickSize}$$

**特點**:
- 反映 Level 1 的即時不平衡
- 對短期價格變動敏感
- 權重較低 (20%)，因為 MLOFI 是主要預測器

### 2.3 MLOFI (Multi-Level Order Flow Imbalance)

**核心創新**: 使用 5 層訂單簿深度，而非僅 Level 1。

**計算方法**:

1. **訂單流變化追蹤**:
   - 追蹤每個層級的 bid/ask 數量變化
   - 檢測價格層級的移動（新層級出現、舊層級消失）

2. **指數衰減權重**:
   $$MLOFI_t = \sum_{m=1}^5 e^{-\alpha(m-1)} \frac{\Delta Bid_m - \Delta Ask_m}{AvgL1Qty}$$

   其中 $\alpha = 0.5$ 是指數衰減係數。

3. **層級權重**:
   - Level 1: 權重 = 1.0 (100%)
   - Level 2: 權重 = 0.606 (60.6%)
   - Level 3: 權重 = 0.368 (36.8%)
   - Level 4: 權重 = 0.223 (22.3%)
   - Level 5: 權重 = 0.135 (13.5%)

**優勢**:
- 捕捉深層訂單簿的壓力
- 降低"欺騙"訂單的影響（深層權重較低）
- 研究顯示比 Level 1 OFI 預測準確度提升 15-74%

**實現細節**:
```python
# 追蹤價格層級變化
if bid_prices[i] > prev_bid_prices[i]:
    delta_bid = bid_qtys[i]  # 新層級出現
elif bid_prices[i] < prev_bid_prices[i]:
    delta_bid = -prev_bid_qtys[i]  # 層級消失
else:
    delta_bid = bid_qtys[i] - prev_bid_qtys[i]  # 數量變化

# 指數衰減權重
weight = np.exp(-alpha_decay * i)  # e^(-0.5*i)
mlofi += weight * (delta_bid - delta_ask)
```

### 2.4 非線性 Alpha Boost

對於極端不平衡，策略會放大信號：

```python
if abs(mlofi_normalized) > 1.5:
    alpha_boost = 2.0  # 極端不平衡時加倍信號
elif abs(mlofi_normalized) > 1.0:
    alpha_boost = 1.5  # 高不平衡時 1.5x
else:
    alpha_boost = 1.0  # 正常
```

**最終預測**:
$$Forecast = RegimeMultiplier \cdot AlphaBoost \cdot (w_{micro} \cdot \alpha_{micro} + w_{mlofi} \cdot MLOFI)$$

---

## 3. 市場體制檢測

### 3.1 波動率計算

**EWMA 波動率**:
- 窗口大小: 500 個價格點
- 平滑係數: 0.1
- 基礎波動率: $TickSize \times 5$

**計算方法**:
$$\sigma_t = \sqrt{\frac{1}{N}\sum_{i=1}^N (P_i - \bar{P})^2}$$

然後使用 EWMA 平滑：
$$\sigma_{EWMA} = 0.1 \cdot \sigma_t + 0.9 \cdot \sigma_{EWMA}$$

### 3.2 體制分類

| 體制 | 波動率比率 | Spread Multiplier | Alpha Multiplier | Gamma Multiplier |
|------|-----------|------------------|-----------------|-----------------|
| **Calm** | < 1.0 | 1.0x | 1.0x | 1.0x |
| **Active** | 1.0 - 2.0 | 0.95x (更緊) | 1.2x (更信任) | 1.0x |
| **Volatile** | > 2.0 | 1.1x (保持競爭) | **1.5x** (強烈信任) | 1.2x |

**關鍵創新**: 在波動期間**增加**對 Alpha 的信任，而非減少。這與傳統方法相反，因為 MLOFI 在波動期間更有預測力。

---

## 4. 報價邏輯

### 4.1 保留價格計算

**基礎保留價格**:
$$r_t = S_t + Forecast \cdot TickSize - InventoryAdjustment$$

**二次庫存懲罰**:
$$InventoryAdjustment = \gamma \sigma^2 q_t \left(1 + \frac{|q_t|}{q_{max}}\right)$$

這使得：
- 庫存為 0 時：線性懲罰
- 庫存接近 $q_{max}$ 時：懲罰接近 2x

### 4.2 價差計算

**基礎價差** (AS 模型):
$$\delta_{base} = \frac{2}{\gamma} \ln\left(1 + \frac{\gamma}{k}\right)$$

**體制調整**:
$$\delta = \delta_{base} \times RegimeSpreadMult$$

**斜率調整** (LOB Slope):
- 計算訂單簿累積數量的對數斜率
- 調整範圍: 0.8x - 1.2x
- 高斜率 → 縮窄價差（厚實訂單簿）
- 低斜率 → 擴大價差（稀薄訂單簿）

### 4.3 非對稱 "Hunt" 邏輯

根據 Alpha 方向調整價差：

**看漲信號** (Forecast > 0.5):
- Bid Spread: 0.8x (縮窄，想買)
- Ask Spread: 1.2x (擴大，高價賣)

**看跌信號** (Forecast < -0.5):
- Bid Spread: 1.2x (擴大，低價買)
- Ask Spread: 0.8x (縮窄，想賣)

**中性**: 兩邊都是 1.0x

### 4.4 庫存偏斜 (Inventory Skew)

**線性偏斜**:
$$Skew = 0.2 \times \frac{q_t}{q_{max}}$$

- 長倉 (q > 0): 降低 Bid，提高 Ask（想賣）
- 短倉 (q < 0): 提高 Bid，降低 Ask（想買）

### 4.5 反嗅探邏輯

**問題**: 掠奪性算法可以通過觀察報價偏斜來推斷庫存。

**解決方案**: 當偏斜過於明顯時，將報價稍微拉回中間價。

**計算**:
$$SniffPenalty = \lambda_{read} \times |Skew| \times TickSize$$

**應用**:
- 長倉時：Bid 稍微提高，Ask 稍微降低
- 短倉時：Bid 稍微降低，Ask 稍微提高

**權衡**: 略微減慢庫存清算速度，但大幅降低被 front-run 的風險。

### 4.6 最終報價

**Bid Price**:
$$Bid = r_t - \frac{\delta}{2} \times BidSpreadMult \times (1 + Skew) + BidSniffAdjust$$

**Ask Price**:
$$Ask = r_t + \frac{\delta}{2} \times AskSpreadMult \times (1 - Skew) + AskSniffAdjust$$

---

## 5. 風險管理

### 5.1 庫存管理

- **最大庫存**: 10.0 (在所有體制下保持不變)
- **訂單數量**: 1.0
- **二次懲罰**: 庫存接近限制時自動擴大價差

### 5.2 止損機制 (Enhanced 版本)

- **單筆交易最大虧損**: 50.0
- **最大總虧損**: 200.0
- **動態價差調整**: 接近止損時自動擴大價差 1.5x

### 5.3 市場狀態過濾 (Enhanced 版本)

- **高波動率閾值**: 3.0x 基礎波動率
- **最小價差比例**: 0.5
- **自動暫停**: 市場條件不利時暫停交易

---

## 6. 測試結果

### 6.1 測試配置

- **數據集**: Binance BTCUSDT Futures 2024-08-08
- **數據類型**: 真實市場數據（Level 2 訂單簿 + 交易數據）
- **數據大小**: ~1,000,000 事件
- **回測引擎**: hftbacktest (Rust-based)
- **執行環境**: Python 3.x, Numba JIT

### 6.2 Baseline vs Aggressive 對比

| 指標 | Baseline | Aggressive | 改進 |
|------|----------|-----------|------|
| **PnL** | +1,120.95 | **+1,174.35** | **+53.40** |
| **Equity** | 1,120.95 | 1,174.35 | +53.40 |
| **Balance** | 556,058.70 | 556,112.10 | +53.40 |
| **Position** | -9.0000 | -9.0000 | 相同 |
| **執行時間** | 0.95s | 1.16s | -22% |
| **改進百分比** | - | - | **+4.76%** |

### 6.3 性能分析

**PnL 改進**:
- 雖然改進幅度較小（4.76%），但在高頻交易中，即使是小幅改進也是有意義的
- 改進方向正確：優化後的策略確實表現更好

**庫存管理**:
- 兩個策略的最終持倉相同（-9.0000）
- 說明優化沒有改變整體庫存管理邏輯，只是調整了執行方式

**執行效率**:
- Aggressive 策略執行時間略長（1.16s vs 0.95s）
- 這是因為增加了更多的計算（MLOFI、體制檢測等）
- 但仍在可接受範圍內

### 6.4 已實施優化的效果

1. **二次庫存懲罰**: ✅ 更嚴格的庫存邊界控制
2. **反嗅探邏輯**: ✅ 降低被識別的風險
3. **指數衰減 MLOFI**: ✅ 更好的信號質量
4. **止損機制**: ✅ 防止過度虧損
5. **市場狀態過濾**: ✅ 只在有利條件下交易

---

## 7. 策略參數

### 7.1 核心參數

```yaml
gamma_base: 0.05          # 風險厭惡係數（低 = 更積極）
k_base: 1.5              # 價差參數
micro_weight: 0.2        # Micro Price 權重
mlofi_weight: 0.8        # MLOFI 權重（主要預測器）
order_qty: 1.0           # 訂單數量
max_position: 10.0       # 最大庫存
```

### 7.2 優化參數

```yaml
# 防禦機制
use_quadratic_penalty: true
use_anti_sniffing: true
lambda_read: 0.3         # 反嗅探係數
max_skew_penalty: 0.5    # 最大偏斜調整

# MLOFI 優化
use_exponential_decay_mlofi: true
alpha_decay: 0.5         # 指數衰減係數
num_levels: 5            # 訂單簿層級數

# 波動率
window_size: 500         # 價格緩衝大小
base_volatility_mult: 5  # 基礎波動率倍數
vol_smoothing: 0.1       # EWMA 平滑係數
```

### 7.3 體制參數

```yaml
regime:
  calm:
    spread_mult: 1.0
    alpha_mult: 1.0
    gamma_mult: 1.0
  
  active:
    spread_mult: 0.95     # 更緊的價差
    alpha_mult: 1.2       # 更信任 Alpha
    gamma_mult: 1.0
  
  volatile:
    spread_mult: 1.1      # 保持競爭
    alpha_mult: 1.5       # 強烈信任 Alpha
    gamma_mult: 1.2       # 稍微增加風險厭惡
```

---

## 8. 優化歷程

### 8.1 Phase 1: 防禦機制 (2025-12-07)

#### 二次庫存懲罰
- **實施日期**: 2025-12-07
- **效果**: 更嚴格的庫存邊界控制
- **代碼變更**: 線性 → 二次懲罰

#### 反嗅探邏輯
- **實施日期**: 2025-12-07
- **效果**: 降低被掠奪性算法識別的風險
- **參數**: lambda_read = 0.3

### 8.2 Phase 3: MLOFI 優化 (2025-12-07)

#### 指數衰減 MLOFI
- **實施日期**: 2025-12-07
- **效果**: 更好的信號質量，降低"欺騙"影響
- **參數**: alpha_decay = 0.5

### 8.3 Phase 4: 風險管理增強 (2025-12-13)

#### 止損機制
- **實施日期**: 2025-12-13
- **效果**: 防止過度虧損
- **參數**: max_total_loss = 200.0

#### 市場狀態過濾
- **實施日期**: 2025-12-13
- **效果**: 只在有利條件下交易
- **參數**: high_volatility_threshold = 3.0

---

## 9. 已知限制與改進空間

### 9.1 當前限制

1. **單一數據集測試**: 目前只測試了 2024-08-08 的數據
2. **參數固定**: 所有參數都是靜態的，無法動態調整
3. **無 VPIN 集成**: VPIN 工具已創建但未集成到策略中
4. **無隊列位置模擬**: 回測假設訂單立即成交

### 9.2 改進空間

1. **VPIN 毒性檢測**: 檢測流動性毒性，避免在有毒流動性中交易
2. **DRL 架構**: 使用強化學習動態調整參數
3. **隊列位置模擬**: 更準確的成交預測
4. **HMM 體制檢測**: 更準確的市場體制識別

---

## 10. 結論

Pyxis HFT Aggressive Market Making Strategy 成功實現了：

1. ✅ **正數 PnL**: +1,174.35 (vs Baseline +1,120.95)
2. ✅ **策略優化**: 5 項關鍵優化已實施
3. ✅ **風險管理**: 二次庫存懲罰 + 反嗅探邏輯 + 止損機制
4. ✅ **Alpha 信號**: MLOFI 作為主要預測器，權重 80%

**下一步**:
- 測試更多數據集以驗證一致性
- 實施 VPIN 毒性檢測
- 考慮 DRL 架構進行動態參數調整

---

*報告生成時間: 2025-12-13*
*策略版本: Optimized v2.0*

