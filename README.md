# HFT Strategy Backtest

**[English](README_EN.md)** | **中文**

高頻交易做市回測框架。

---

## 快速開始

```bash
# 1. Clone 專案
git clone <repository-url>
cd hft-strategy

# 2. 建立環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 用測試資料執行
python src/scripts/generate_dummy.py
python src/core/backtest.py data/dummy_data.npy

# 4. 用真實 Binance 資料測試
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz
```

---

## 專案結構

```
hft-strategy/
├── src/                       # 核心程式碼
│   ├── core/                  # 核心功能
│   │   ├── backtest.py        # 回測執行器
│   │   ├── data_loader.py     # 資料載入器
│   │   └── config_loader.py   # 配置載入器
│   │
│   ├── utils/                 # 工具類
│   │   ├── logger.py          # 日誌系統
│   │   ├── visualization.py   # 圖表與指標
│   │   ├── result_viewer.py   # 結果展示器
│   │   └── reconciliation.py  # 對賬機制
│   │
│   ├── scripts/               # 可執行腳本
│   │   ├── recorder.py        # OKX 資料收集
│   │   ├── normalize.py       # 資料處理
│   │   ├── generate_dummy.py  # 測試資料生成
│   │   └── live_trading.py    # 即時交易
│   │
│   ├── learning/              # 線上學習
│   │   ├── online_learning.py # River 線上學習
│   │   └── ab_testing.py      # A/B 測試框架
│   │
│   └── tests/                 # 測試文件
│
├── data/                      # 市場資料
│   ├── binance_usdm/          # Binance 合約 (BTC, ETH)
│   ├── binance_spot/          # Binance 現貨
│   ├── bybit/                 # Bybit 資料
│   └── dummy_data.npy         # 測試資料
│
├── notebooks/                 # 教程 notebooks
├── docs/                      # 文檔
└── config/                    # 配置文件
```

---

## 回測指令

```bash
# 基本執行
python src/core/backtest.py <data_file>

# 進階選項
python src/core/backtest.py data.npz --no-viz        # 不顯示視覺化
python src/core/backtest.py data.npz --save          # 儲存報告
python src/core/backtest.py data.npz -s snapshot.npz # 自訂快照
```

---

## 收集 OKX 真實資料

```bash
# 開始錄製
python src/scripts/recorder.py --symbol BTC-USDT-SWAP --output data/okx/

# 正規化資料
python src/scripts/normalize.py --input data/okx/ --output data/okx_btc.npz

# 用真實資料回測
python src/core/backtest.py data/okx_btc.npz
```

---

## Live Trading (OKX Demo)

```bash
# 1. 設定 API
cp .env.example .env
# 編輯 .env 填入 OKX Demo Trading API Key/Secret/Passphrase

# 2. 測試連線
python src/scripts/live_trading.py --test

# 3. 啟動交易
python src/scripts/live_trading.py
```

**詳細指南：** 查看 [OKX 模擬交易指南](docs/guides/OKX_SIMULATED_TRADING.md)

---

## Notebooks

| 主題 | Notebook |
|------|----------|
| **入門** | `Getting Started.ipynb` |
| **網格交易** | `High-Frequency Grid Trading.ipynb` |
| **隊列位置** | `Queue-Based Market Making in Large Tick Size Assets.ipynb` |
| **多資產** | `Making Multiple Markets.ipynb` |
| **GLFT 模型** | `GLFT Market Making Model and Grid Trading.ipynb` |
| **延遲影響** | `Impact of Order Latency.ipynb` |

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
- [River ML](https://riverml.xyz/)
- [Avellaneda-Stoikov 論文](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf)
- [OKX API](https://www.okx.com/docs-v5/en/)

---

## 授權
MIT
