# Pyxis HFT 策略框架

**中文** | **[English](README_ZH.md)**

Pyxis 團隊的高頻交易做市回測框架。

## Team Pyxis - NTUFC 2025

---

## 快速開始

```bash
# 1. Clone 專案
git clone https://github.com/itsYoga/pyxis-hft-strategy.git
cd pyxis-hft-strategy

# 2. 建立環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 用測試資料執行
cd src
python generate_dummy.py
python backtest.py dummy_data.npy

# 4. 用真實 Binance 資料測試 (已內建!)
python backtest.py ../data/binance_usdm/btcusdt_20240808.gz
```

---

## 專案結構

```
pyxis-hft-strategy/
├── src/                  # 核心程式碼
│   ├── strategy.py       # 你的策略在這裡 - 改這個!
│   ├── backtest.py       # 回測執行器 (含視覺化)
│   ├── visualization.py  # 圖表與指標 (新增!)
│   ├── recorder.py       # OKX 資料收集
│   ├── normalize.py      # 資料處理
│   └── generate_dummy.py # 測試資料生成
│
├── data/                 # 市場資料
│   ├── binance_usdm/     # Binance 合約 (BTC, ETH)
│   ├── binance_spot/     # Binance 現貨
│   └── bybit/            # Bybit 資料
│
├── notebooks/            # 21 個教程 notebooks!
└── docs/                 # 文檔
```

---

## 如何測試你自己的策略

### 步驟 1: 建立你的策略檔案

```python
# src/my_strategy.py
from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT

@njit
def my_strategy(hbt, stat):
    """
    你的自訂策略!
    
    hbt: 回測引擎物件
    stat: 狀態陣列
    """
    asset_no = 0
    
    while True:
        ret = hbt.elapse(100_000_000)  # 每 100ms
        if ret != 0:
            break
        
        hbt.clear_inactive_orders(asset_no)
        
        depth = hbt.depth(asset_no)
        if depth.best_bid == 0 or depth.best_ask == 0:
            continue
        
        mid_price = (depth.best_bid + depth.best_ask) / 2.0
        position = hbt.position(asset_no)
        
        # ========================================
        # 你的交易邏輯在這裡
        # ========================================
        
        # 範例: 簡單做市
        bid_price = mid_price - 1.0
        ask_price = mid_price + 1.0
        
        # 下單
        hbt.submit_buy_order(asset_no, 1, bid_price, 1.0, GTX, LIMIT, False)
        hbt.submit_sell_order(asset_no, 2, ask_price, 1.0, GTX, LIMIT, False)
```

### 步驟 2: 執行回測

```bash
cd src

# 修改 backtest.py 來 import 你的策略:
# from my_strategy import my_strategy

python backtest.py ../data/binance_usdm/btcusdt_20240808.gz
```

### 步驟 3: 查看視覺化結果

```bash
# 結果會顯示:
# - PnL 曲線
# - Drawdown 圖表
# - 持倉變化
# - Sharpe ratio, Max DD, Win rate
```

---

## 可用的 Alpha 信號

### 1. Order Book Imbalance (OBI) - 訂單簿失衡
```python
imbalance = (bid_qty - ask_qty) / (bid_qty + ask_qty)
# > 0: 買壓大，價格可能上漲
# < 0: 賣壓大，價格可能下跌
```

### 2. Micro Price - 微觀價格
```python
micro_price = (bid * ask_qty + ask * bid_qty) / (bid_qty + ask_qty)
# 比簡單中間價更準確的公平價格
```

### 3. Trade Flow - 成交流
```python
flow = (buy_volume - sell_volume) / (buy_volume + sell_volume)
# 最近交易方向
```

---

## 收集 OKX 真實資料

```bash
cd src

# 開始錄製 (1-2 小時後 Ctrl+C 停止)
python recorder.py --symbol BTC-USDT-SWAP --output ../data/okx/

# 正規化資料
python normalize.py --input ../data/okx/ --output ../data/okx_btc.npz

# 用真實資料回測
python backtest.py ../data/okx_btc.npz
```

---

## 回測指令

```bash
# 基本執行
python backtest.py <data_file>

# 進階選項
python backtest.py data.npz --no-viz        # 不顯示視覺化
python backtest.py data.npz --save          # 儲存報告
python backtest.py data.npz -s snapshot.npz # 自訂快照
```

---

## Notebooks (21 個教程!)

| 主題 | Notebook |
|------|----------|
| **入門** | `Getting Started.ipynb` |
| **Alpha - OBI** | `Market Making with Alpha - Order Book Imbalance.ipynb` |
| **網格交易** | `High-Frequency Grid Trading.ipynb` |
| **隊列位置** | `Queue-Based Market Making in Large Tick Size Assets.ipynb` |
| **多資產** | `Making Multiple Markets.ipynb` |

---

## 雲端部署 (2 週資料)

**推薦: 阿里雲香港**
- 與 OKX 同機房 = 1-3ms 延遲
- 月費約 $25 USD

```bash
# 在雲端伺服器
tmux new -s recorder
python recorder.py --symbol BTC-USDT-SWAP --output data/
# Ctrl+B 然後 D 離開
```

---

## 績效指標

| 指標 | 目標 |
|------|------|
| PnL | > 0 |
| Sharpe Ratio | > 1.5 |
| Max Drawdown | < 10% |
| Win Rate | > 50% |

---

## 參考資源

- [hftbacktest 文檔](https://hftbacktest.readthedocs.io/)
- [Avellaneda-Stoikov 論文](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf)
- [101 Formulaic Alphas](https://arxiv.org/abs/1601.00991)
- [OKX API](https://www.okx.com/docs-v5/en/)

---

## 授權
MIT

---

> **Team Pyxis** - NTUFC Competition 2025
