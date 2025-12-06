# HFT 高頻交易回測系統 - 完整策略筆記

###### tags: `HFT` `量化交易` `Alpha模型` `hftbacktest` `OKX`

> **專案目標**：建立高頻做市策略，使用 OKX 真實資料回測，透過 Alpha 信號優化策略表現

---

## 目錄

[TOC]

---

## 一、專案架構總覽

### 1.1 專案結構

```
hftbacktest/
├── okx_hft/                    # 我們的策略目錄
│   ├── recorder.py             # OKX 資料收集器
│   ├── normalize.py            # 資料正規化
│   ├── generate_dummy.py       # 假資料生成(測試用)
│   ├── backtest.py             # 回測主程式
│   └── strategy.py             # 策略核心 (Alpha 在這裡!)
├── examples/                   # 官方教程 (重要參考!)
│   ├── Market Making with Alpha - Order Book Imbalance.ipynb
│   ├── High-Frequency Grid Trading.ipynb
│   └── ...
└── py-hftbacktest/             # Python 函式庫
```

### 1.2 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      資料流程                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │   OKX    │───>│ recorder │───>│ .npz 檔  │              │
│  │WebSocket │    │   .py    │    │  (chunks)│              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                       │                     │
│                                       v                     │
│                              ┌──────────────┐               │
│                              │ normalize.py │               │
│                              └──────────────┘               │
│                                       │                     │
│                                       v                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  結果    │<───│ backtest │<───│ 合併後   │              │
│  │  分析    │    │   .py    │    │  .npz    │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                       ^                                     │
│                       │                                     │
│                  ┌──────────┐                               │
│                  │ strategy │                               │
│                  │   .py    │                               │
│                  └──────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、回測引擎原理

### 2.1 什麼是回測？

回測 = **用歷史資料模擬交易**，驗證策略是否賺錢

```
歷史資料 ────> 回測引擎 ────> 模擬成交 ────> 計算盈虧
   │              │              │
   │              v              │
   │     ┌────────────────┐      │
   └────>│  你的策略邏輯  │<─────┘
         └────────────────┘
```

### 2.2 hftbacktest 特色

| 特點 | 說明 |
|------|------|
| **Tick-by-Tick** | 逐筆模擬，不漏掉任何市場變化 |
| **延遲模擬** | 考慮訂單送達交易所的時間延遲 |
| **隊列位置** | 模擬掛單在訂單簿中的排隊位置 |
| **Numba JIT** | 用 `@njit` 加速 Python 程式碼 |

### 2.3 核心 API

```python
from hftbacktest import (
    BacktestAsset,           # 資產配置
    HashMapMarketDepthBacktest,  # 回測引擎
    BUY, SELL, GTX, LIMIT    # 訂單常數
)

# 回測主迴圈
@njit
def my_strategy(hbt):
    while hbt.elapse(100_000_000) == 0:  # 每 100ms
        # 清理已成交/取消的訂單
        hbt.clear_inactive_orders(0)
        
        # 取得市場資料
        depth = hbt.depth(0)
        mid_price = (depth.best_bid + depth.best_ask) / 2.0
        position = hbt.position(0)
        
        # 你的策略邏輯...
        # 下單
        hbt.submit_buy_order(0, order_id, price, qty, GTX, LIMIT, False)
```

---

## 三、取得 OKX 真實資料

### 3.1 為什麼需要真實資料？

> [!WARNING]
> **用假資料回測 = 自我欺騙**
>
> - 假資料無法反映真實市場波動
> - 無法驗證策略在極端行情的表現
> - **比賽一定要用真實資料！**

### 3.2 OKX WebSocket 資料來源

| Channel | 說明 | 更新頻率 | 深度 |
|---------|------|---------|------|
| `books-l2-tbt` | 訂單簿 (推薦) | 10ms | 400檔 |
| `books50-l2-tbt` | 訂單簿 | 10ms | 50檔 |
| `trades` | 成交紀錄 | 即時 | - |

### 3.3 資料收集步驟

#### Step 1: 開始錄製

```bash
cd /path/to/hftbacktest/okx_hft

# 開始錄製 BTC-USDT-SWAP (建議至少錄製 1-2 小時)
python recorder.py --symbol BTC-USDT-SWAP --output data/

# 程式會持續運行，按 Ctrl+C 停止
```

#### Step 2: 檢查錄製狀態

```bash
# 方法 1: 檢查 process 是否執行中
ps aux | grep recorder.py | grep -v grep

# 方法 2: 查看 data/ 資料夾大小
ls -la data/
du -sh data/

# 方法 3: 計算已收集事件數
python -c "import numpy as np; import glob; files=glob.glob('data/*.npz'); total=sum(len(np.load(f)['data']) for f in files); print(f'Total events: {total}')"
```

> [!TIP]
> **建議錄製時間**
> - 測試用：30 分鐘
> - 正式回測：2-4 小時
> - 完整驗證：24 小時以上
> - 生產環境：2 週 (需雲端伺服器)

#### Step 3: 資料正規化

```bash
# 合併所有 chunk 檔案
python normalize.py --input data/ --output okx_btc_data.npz
```

#### Step 4: 執行回測

```bash
python backtest.py okx_btc_data.npz
```

### 3.4 資料格式說明

```python
# hftbacktest 資料結構 (每個 event)
dtype = [
    ('ev', 'u8'),        # 事件類型 (DEPTH/TRADE/BUY/SELL)
    ('exch_ts', 'i8'),   # 交易所時間戳 (ns)
    ('local_ts', 'i8'),  # 本地時間戳 (ns)
    ('px', 'f8'),        # 價格
    ('qty', 'f8'),       # 數量
    ('order_id', 'u8'),  # 訂單 ID (L3 用)
    ('ival', 'i8'),      # 保留
    ('fval', 'f8'),      # 保留
]
```

---

## 四、Alpha 模型詳解 (策略核心)

### 4.1 什麼是 Alpha？

> [!NOTE]
> **Alpha = 預測價格方向的能力 = 超額收益的來源**
>
> - Alpha > 0 : 預測價格會漲
> - Alpha < 0 : 預測價格會跌
> - Alpha = 0 : 沒有預測能力

### 4.2 Order Book Imbalance (OBI) - 訂單簿失衡

最常用的 Alpha 信號之一！

#### 公式

$$
\text{Imbalance} = \frac{\text{Bid Volume} - \text{Ask Volume}}{\text{Bid Volume} + \text{Ask Volume}}
$$

#### 直覺解釋

```
買單多於賣單 -> Imbalance > 0 -> 買壓大 -> 價格可能上漲
賣單多於買單 -> Imbalance < 0 -> 賣壓大 -> 價格可能下跌
```

### 4.3 Micro Price - 微觀價格

考慮 BBO (Best Bid/Offer) 數量的加權中間價

#### 公式

$$
\text{Micro Price} = \frac{P_{bid} \times Q_{ask} + P_{ask} \times Q_{bid}}{Q_{bid} + Q_{ask}}
$$

### 4.4 Trade Flow Imbalance - 成交流失衡

追蹤最近成交的方向

```python
@njit
def calculate_trade_flow(last_trades, window=100):
    buy_volume = 0.0
    sell_volume = 0.0
    for trade in last_trades[-window:]:
        if trade.ev & BUY_EVENT == BUY_EVENT:
            buy_volume += trade.qty
        else:
            sell_volume += trade.qty
    return (buy_volume - sell_volume) / (buy_volume + sell_volume)
```

---

## 五、策略優化指南

### 5.1 當前策略 (AS Model + Alpha)

```python
# 保留價格 = 中間價 + Alpha預測 - 庫存調整
reservation_price = (
    mid_price 
    + forecast * tick_size      # Alpha 預測
    - position * gamma * volatility^2  # 庫存風險
)
```

### 5.2 參數優化表

| 參數 | 作用 | 建議範圍 | 調整方向 |
|------|------|---------|---------|
| `gamma` | 風險厭惡 | 0.01 - 1.0 | 越大則越快平倉 |
| `k` | Spread 彈性 | 0.5 - 3.0 | 越大則 Spread 越窄 |
| `alpha_weight` | Alpha 權重 | 0.1 - 1.0 | 看回測結果調整 |
| `imbalance_weight` | Imbalance 權重 | 0.1 - 1.0 | 看回測結果調整 |

---

## 六、GitHub Repo 建立指南

### 6.1 建議的 Repo 結構

```
okx-hft-strategy/
├── README.md               # 專案說明
├── requirements.txt        # Python 依賴
├── .gitignore             # 忽略檔案
├── config/
│   └── settings.py        # 配置參數
├── src/
│   ├── recorder.py        # 資料收集
│   ├── normalize.py       # 資料處理
│   ├── backtest.py        # 回測主程式
│   └── strategy.py        # 策略邏輯
├── data/                  # 資料目錄 (gitignore)
│   └── .gitkeep
├── notebooks/             # 分析 Notebooks
│   └── analysis.ipynb
├── scripts/
│   ├── run_recorder.sh    # 錄製腳本
│   └── run_backtest.sh    # 回測腳本
└── docs/
    └── strategy_notes.md  # 策略文檔
```

### 6.2 .gitignore 設定

```
# Data files (太大不適合放 Git)
data/*.npz
data/*.npy
*.npz
*.npy

# Python
__pycache__/
*.pyc
.venv/
venv/

# IDE
.vscode/
.idea/

# Logs
*.log

# OS
.DS_Store
```

### 6.3 requirements.txt

```
numpy>=1.24.0
numba>=0.57.0
hftbacktest>=2.0.0
websockets>=12.0
pandas>=2.0.0
matplotlib>=3.7.0
```

### 6.4 建立 Repo 步驟

```bash
# 1. 建立新目錄
mkdir okx-hft-strategy
cd okx-hft-strategy

# 2. 初始化 Git
git init

# 3. 複製必要檔案
cp /path/to/original/okx_hft/*.py src/

# 4. 建立 .gitignore 和 requirements.txt
# (內容如上)

# 5. 初次提交
git add .
git commit -m "Initial commit: HFT strategy framework"

# 6. 連結 GitHub
git remote add origin https://github.com/YOUR_USERNAME/okx-hft-strategy.git
git push -u origin main
```

---

## 七、雲端部署指南 (長期錄製)

### 7.1 為什麼需要雲端？

| 問題 | 本地電腦 | 雲端伺服器 |
|------|---------|-----------|
| **24/7 運行** | 電腦會當機/休眠 | 持續運行 |
| **網路延遲** | 家用網路不穩定 | 專線低延遲 |
| **運算資源** | 可能不夠 | 可彈性擴展 |
| **2 週錄製** | 不切實際 | 輕鬆達成 |

### 7.2 OKX 伺服器位置

OKX 使用 **阿里雲香港** 作為主要伺服器，也有 AWS 部署。

| 雲端區域 | 到 OKX 延遲 | 建議用途 |
|---------|------------|---------|
| **香港 (HK)** | 1-3ms | 最佳! 正式上線必選 |
| **東京 (Tokyo)** | 30-50ms | 次佳選擇 |
| **新加坡 (SG)** | 20-40ms | 可接受 |
| **台灣本地** | 50-100ms | 僅用於開發測試 |

### 7.3 雲端選擇比較

| 服務 | 香港機房 | 月費 (最低規格) | 推薦度 |
|------|---------|----------------|--------|
| **阿里雲** | 有 (cn-hongkong) | ~$25 USD | 最推薦 (與 OKX 同機房) |
| **AWS** | 有 (ap-east-1) | ~$20 USD | 推薦 |
| **GCP** | 有 (asia-east2) | ~$25 USD | 推薦 |
| **Vultr** | 有 | ~$6 USD | 便宜選擇 |
| **DigitalOcean** | 有 (Singapore) | ~$6 USD | 便宜選擇 |

### 7.4 建議規格

**資料收集 (2 週)**
- vCPU: 1-2 核
- RAM: 2-4 GB
- Storage: 50-100 GB SSD
- 月費: $10-30 USD

**回測運算**
- vCPU: 4-8 核
- RAM: 8-16 GB
- Storage: 100 GB SSD
- 月費: $50-100 USD

### 7.5 部署步驟

```bash
# 1. SSH 連線到雲端伺服器
ssh root@YOUR_SERVER_IP

# 2. 安裝 Python 環境
apt update && apt install -y python3 python3-pip python3-venv

# 3. Clone 你的 repo
git clone https://github.com/YOUR_USERNAME/okx-hft-strategy.git
cd okx-hft-strategy

# 4. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 使用 tmux/screen 背景執行 (防斷線)
tmux new -s recorder

# 6. 開始錄製
python src/recorder.py --symbol BTC-USDT-SWAP --output data/

# 按 Ctrl+B 然後 D 離開 tmux (程式繼續運行)
# 重新連接: tmux attach -t recorder
```

### 7.6 長期錄製腳本

```bash
#!/bin/bash
# run_recorder.sh - 自動重啟錄製

while true; do
    echo "[$(date)] Starting recorder..."
    python src/recorder.py --symbol BTC-USDT-SWAP --output data/
    echo "[$(date)] Recorder stopped. Restarting in 10 seconds..."
    sleep 10
done
```

### 7.7 資料備份策略

```bash
# 每天自動備份到本地
# 加入 crontab: crontab -e

# 每天凌晨 3 點備份
0 3 * * * rsync -avz root@YOUR_SERVER:/path/to/data/ /local/backup/
```

---

## 八、降低延遲的方法

### 8.1 延遲來源分析

```
總延遲 = 網路延遲 + 處理延遲 + 交易所延遲

網路延遲: 你的伺服器到 OKX 的時間
處理延遲: 你的程式執行時間
交易所延遲: OKX 處理訂單的時間 (~3ms)
```

### 8.2 優化方法

| 優化項目 | 方法 | 預期效果 |
|---------|------|---------|
| **網路延遲** | 使用香港機房 | 降低 50-100ms |
| **程式效能** | 使用 Numba @njit | 提升 10-100 倍 |
| **資料結構** | 預分配 numpy array | 減少 GC 暫停 |
| **WebSocket** | 使用 async | 非阻塞處理 |

### 8.3 延遲測試

```python
import time
import asyncio
import websockets

async def measure_latency():
    url = "wss://ws.okx.com:8443/ws/v5/public"
    async with websockets.connect(url) as ws:
        start = time.time_ns()
        await ws.send('{"op": "ping"}')
        response = await ws.recv()
        end = time.time_ns()
        print(f"RTT: {(end - start) / 1e6:.2f} ms")

asyncio.run(measure_latency())
```

---

## 九、評估指標

| 指標 | 說明 | 目標 |
|------|------|------|
| **PnL** | 總盈虧 | > 0 |
| **Sharpe Ratio** | 風險調整收益 | > 1.5 |
| **Max Drawdown** | 最大回撤 | < 10% |
| **Win Rate** | 勝率 | > 50% |
| **Turnover** | 換手率 | 合理範圍 |

---

## 十、時程規劃

### 短期 (1-2 週)
- [ ] 完成本地測試
- [ ] 收集 24 小時真實資料
- [ ] 優化策略參數

### 中期 (2-4 週)
- [ ] 部署雲端伺服器
- [ ] 收集 2 週資料
- [ ] 完整回測驗證
- [ ] 撰寫報告

### 長期 (比賽後)
- [ ] 嘗試更多 Alpha 信號
- [ ] 實盤小額測試
- [ ] 持續優化

---

## 十一、常見問題

### Q1: 為什麼回測結果是 0？
**A:** 檢查資料是否正確載入，確保有 depth update 事件

### Q2: 如何知道策略是否過度擬合？
**A:** 用不同時間段的資料做 out-of-sample 測試

### Q3: recorder.py 連不上 OKX？
**A:** 確認網路連線，可能需要 VPN

### Q4: 雲端伺服器選擇？
**A:** 優先選阿里雲香港，與 OKX 同機房延遲最低

### Q5: 2 週資料大約多大？
**A:** BTC-USDT-SWAP 約 10-50 GB (視市場活躍度)

---

## 十二、參考資源

### 必讀教程
- [Market Making with Alpha - Order Book Imbalance](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)
- [High-Frequency Grid Trading](https://hftbacktest.readthedocs.io/en/latest/tutorials/High-Frequency%20Grid%20Trading.html)

### 學術論文
- [Avellaneda-Stoikov (2008)](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf) - 做市策略經典
- [GLFT Model](https://arxiv.org/abs/1105.3115) - Grid Trading 理論
- [101 Formulaic Alphas (2016)](https://arxiv.org/abs/1601.00991) - 101 個 Alpha 公式 (強烈推薦!)

### API 文檔
- [OKX WebSocket API](https://www.okx.com/docs-v5/en/#overview-websocket)

---

> **最後更新**: 2025-12-06
> **作者**: Jesse
