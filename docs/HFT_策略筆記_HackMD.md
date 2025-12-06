# HFT 高頻交易回測系統 - 完整策略筆記

###### tags: `HFT` `量化交易` `Alpha模型` `hftbacktest` `MLOFI` `River`

> **專案目標**：建立高頻做市策略，使用 Binance/OKX 真實資料回測，透過 Alpha 信號優化策略表現
> **最後更新**: 2025-12-07

---

## 快速開始

```bash
# 1. 安裝依賴
cd /Users/jesse/Documents/NTUFC/pyxis-hft-strategy
pip install -r requirements.txt
pip install river  # 線上學習 (可選)

# 2. 用真實資料回測
./venv/bin/python src/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz --no-viz

# 3. 評估 River 線上學習
./venv/bin/python src/ab_testing.py
```

---

## 目錄

[TOC]

---

## 一、專案架構

### 1.1 專案結構 (最新)

```
pyxis-hft-strategy/
├── src/                        # 核心程式碼
│   ├── strategy.py             # ⭐ MLOFI + AS 策略 (主要)
│   ├── backtest.py             # 回測主程式
│   ├── online_learning.py      # River 線上學習
│   ├── ab_testing.py           # A/B 測試框架
│   ├── reconciliation.py       # 對賬機制
│   ├── recorder.py             # 資料收集器
│   ├── live_trading.py         # 即時交易
│   └── visualization.py        # 視覺化
├── data/                       # 市場資料
│   ├── binance_usdm/           # ✓ Binance 永續合約
│   │   ├── btcusdt_20240808.npz
│   │   └── btcusdt_20240808_eod.npz
│   ├── binance_spot/           # Binance 現貨
│   └── bybit/                  # Bybit
├── docs/                       # 文檔
├── notebooks/                  # Jupyter 分析
└── scripts/                    # 腳本
```

### 1.2 模組功能表

| 模組 | 功能 | 使用方式 |
|------|------|---------|
| **strategy.py** | MLOFI + LOB Slope + 體制識別 | 被 backtest.py 調用 |
| **backtest.py** | 執行回測 | `python src/backtest.py <data.npz>` |
| **online_learning.py** | River 線上學習 | `from online_learning import OnlineAlphaLearner` |
| **ab_testing.py** | A/B 測試 | `python src/ab_testing.py` |
| **reconciliation.py** | 對賬/PnL 驗證 | `from reconciliation import Reconciler` |
| **recorder.py** | 收集 OKX 資料 | `python src/recorder.py --symbol BTC-USDT-SWAP` |

---

## 二、使用資料

### 2.1 現有資料

你已經有真實 Binance 數據！

```bash
# 查看可用資料
ls -la data/binance_usdm/

# 輸出:
# btcusdt_20240808.npz      (3.6 MB, ~100萬事件)
# btcusdt_20240808_eod.npz  (快照)
# btcusdt_20240809.npz      (4.8 MB)
```

### 2.2 運行回測

```bash
# 使用真實 Binance 資料
./venv/bin/python src/backtest.py \
    data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz \
    --no-viz

# 結果範例:
# PnL: +427.00
```

### 2.3 用 Dummy Data 測試

如果沒有真實資料：

```bash
# 生成假資料
./venv/bin/python src/generate_dummy.py

# 用假資料回測
./venv/bin/python src/backtest.py src/dummy_data.npy --no-viz
```

### 2.4 收集新資料 (OKX)

```bash
# 開始錄製 (會持續運行)
./venv/bin/python src/recorder.py --symbol BTC-USDT-SWAP --output data/okx/

# 建議錄製時間:
# - 測試: 30 分鐘
# - 正式: 2-4 小時
# - 完整: 24 小時+
```

---

## 三、策略詳解 (HA3 架構)

### 3.1 策略公式

```
保留價格 = 中間價 + Alpha預測 - 庫存調整
報價 = 保留價格 ± 動態價差
```

### 3.2 Alpha 訊號組成

| Alpha | 權重 | 說明 |
|-------|------|------|
| **Micro Price** | 30% | BBO 數量加權價格 |
| **MLOFI** | 50% | 5層訂單流不平衡 |
| **EPI (OFI/Slope)** | 20% | 預期價格衝擊 |

### 3.3 MLOFI (Multi-Level Order Flow Imbalance)

傳統 OFI 只看 Level 1，MLOFI 分析 5 層深度：

```python
# strategy.py 核心邏輯
for i in range(5):  # 5 層
    weight = 0.7 ** i  # 指數衰減 (Level 1 權重最高)
    delta_bid = bid_qtys[i] - prev_bid_qtys[i]
    delta_ask = ask_qtys[i] - prev_ask_qtys[i]
    mlofi += weight * (delta_bid - delta_ask)
```

**研究顯示**：MLOFI 比 Level 1 OFI 預測準確度提升 15-74%

### 3.4 LOB Slope (訂單簿斜率)

衡量市場「厚度」= 對價格衝擊的阻力

```
高斜率 → 厚實訂單簿 → 均值回歸環境
低斜率 → 稀薄訂單簿 → 動能突破環境
```

### 3.5 體制識別 (Regime Detection)

根據波動率自動調整策略：

| 體制 | 條件 | 策略調整 |
|------|------|---------|
| Calm | vol_ratio < 1.0 | 縮窄價差 |
| Active | 1.0-2.0 | 正常 |
| Volatile | > 2.0 | 擴大價差，減少持倉 |

---

## 四、River 線上學習

### 4.1 什麼是 River？

River 是 Python 線上學習庫，可以**即時**調整 Alpha 權重，適應市場變化。

```python
# 使用方式
from online_learning import OnlineAlphaLearner, AlphaSignals

learner = OnlineAlphaLearner(
    learning_rate=0.01,
    warmup_steps=100
)

# 每個 timestep
signals = AlphaSignals(
    micro_price_alpha=0.5,
    mlofi_alpha=0.8,
    slope_alpha=0.3,
    mid_price=50000.0
)
learner.observe(signals)
weights = learner.get_weights()  # {'micro': 0.3, 'mlofi': 0.5, 'slope': 0.2}
```

### 4.2 如何評估 River 是否有效？

**關鍵問題：Mock Data 無法評估 River 效果！**

原因：
- Mock data 的 Alpha 與價格關係是固定的
- 靜態權重如果剛好正確，River 無法超越
- **River 的價值在於適應市場變化**

**正確評估方法：**

```bash
# 1. 用真實資料運行 A/B 測試
./venv/bin/python src/ab_testing.py

# 2. 查看統計顯著性
# p < 0.05 且 River > Baseline → 使用 River
# 否則 → 使用靜態權重或調參
```

### 4.3 A/B 測試解讀

| 結果 | 行動 |
|------|------|
| River 顯著優於 Baseline (p < 0.05) | ✅ 使用 River |
| River 較好但不顯著 | 收集更多資料 |
| Baseline 較好 | 調參或用靜態權重 |

### 4.4 調參建議

```python
# 如果 River 表現不好，嘗試：
learner = OnlineAlphaLearner(
    learning_rate=0.005,   # 降低學習率 (更穩定)
    warmup_steps=200,      # 增加 warmup (避免早期波動)
    l2_reg=0.01            # 增加正則化 (防止過擬合)
)
```

---

## 五、PnL 計算 (Kronos 方法)

### 5.1 正確公式

```python
# backtest.py 中的計算
equity_wo_fee = balance + position * mid_price * contract_size
equity = equity_wo_fee - fee  # 扣除手續費
pnl = equity
```

### 5.2 對賬機制

```python
from reconciliation import Reconciler

reconciler = Reconciler()
reconciler.record_trade(timestamp, order_id, 'BUY', price, qty, fee, balance, position)
result = reconciler.reconcile(final_balance, final_position, final_fee)
print(result)  # PASS / FAIL
```

---

## 六、完整運行流程

### 6.1 回測流程

```bash
# Step 1: 確認環境
cd /Users/jesse/Documents/NTUFC/pyxis-hft-strategy
source venv/bin/activate

# Step 2: 選擇資料
DATA=data/binance_usdm/btcusdt_20240808.npz
SNAPSHOT=data/binance_usdm/btcusdt_20240808_eod.npz

# Step 3: 運行回測
./venv/bin/python src/backtest.py $DATA --snapshot $SNAPSHOT --no-viz

# Step 4: 查看結果
# Balance, Position, PnL 會顯示在終端
```

### 6.2 A/B 測試流程

```bash
# 評估 River vs 靜態權重
./venv/bin/python src/ab_testing.py
```

### 6.3 即時交易 (未來)

```bash
# 需要設定 .env 中的 API 金鑰
./venv/bin/python src/live_trading.py
```

---

## 七、參數優化

### 7.1 策略參數 (strategy.py)

| 參數 | 預設值 | 作用 | 調整方向 |
|------|--------|------|---------|
| `gamma_base` | 0.1 | 風險厭惡 | ↑ 更快平倉 |
| `k_base` | 1.5 | 價差彈性 | ↑ 更窄價差 |
| `num_levels` | 5 | MLOFI 層數 | 5-10 層 |
| `ofi_decay` | 0.7 | 深層權重衰減 | 0.5-0.9 |
| `max_position` | 10 | 最大持倉 | 視風險調整 |

### 7.2 River 參數 (online_learning.py)

| 參數 | 預設值 | 作用 |
|------|--------|------|
| `learning_rate` | 0.01 | 學習速度 |
| `warmup_steps` | 100 | 預熱期 |
| `l2_reg` | 0.001 | 正則化強度 |

---

## 八、雲端部署 (VPS)

### 8.1 推薦配置

| 用途 | CPU | RAM | 存儲 | 月費 |
|------|-----|-----|------|------|
| 資料收集 | 1-2 核 | 2 GB | 50 GB | $10-20 |
| 即時交易 | 2-4 核 | 4 GB | 50 GB | $20-40 |

### 8.2 推薦區域

| 交易所 | 推薦區域 | 延遲 |
|--------|---------|------|
| OKX | 香港 | 1-3ms |
| Binance | 東京/新加坡 | 10-30ms |

### 8.3 部署步驟

```bash
# 1. SSH 連線
ssh root@YOUR_VPS_IP

# 2. Clone repo
git clone https://github.com/YOUR_USERNAME/pyxis-hft-strategy.git
cd pyxis-hft-strategy

# 3. 安裝環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 使用 tmux 背景執行
tmux new -s trading
./venv/bin/python src/live_trading.py
# Ctrl+B, D 離開 (程式繼續運行)
```

---

## 九、常見問題

### Q1: Mock data 和真實資料結果差很多？
**A:** 正常！Mock data 沒有真實市場的複雜性。一定要用真實資料驗證。

### Q2: River 表現比 Baseline 差？
**A:** 可能原因：
- 學習率太高 → 降低到 0.005
- Warmup 太短 → 增加到 200
- 資料太少 → 收集更多資料

### Q3: PnL 為什麼是 0？
**A:** 檢查：
- 資料是否正確載入
- Snapshot 檔案是否存在
- 策略是否有下單

### Q4: 如何知道策略是否過擬合？
**A:** 用不同日期的資料做 out-of-sample 測試。

---

## 十、下一步

### 立即可做
- [x] MLOFI 策略實作
- [x] River 線上學習
- [x] A/B 測試框架
- [ ] 用多天資料驗證
- [ ] VPS 部署

### 未來研究
- [ ] Lead-Lag 跨資產套利
- [ ] VPIN 毒性偵測
- [ ] RL 執行優化

---

## 參考資源

- [hftbacktest 文檔](https://hftbacktest.readthedocs.io/)
- [River ML](https://riverml.xyz/)
- [Avellaneda-Stoikov 論文](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf)
- [MLOFI 研究 (2024)](https://arxiv.org/abs/2401.06485)
