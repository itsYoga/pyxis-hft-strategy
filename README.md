# Pyxis HFT Strategy Framework

**[中文版](README_ZH.md)** | **English**

A High-Frequency Trading (HFT) Market Making backtesting framework for team Pyxis.

## Team Pyxis - NTUFC 2025

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/itsYoga/pyxis-hft-strategy.git
cd pyxis-hft-strategy

# 2. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Test with sample data
cd src
python generate_dummy.py
python backtest.py dummy_data.npy

# 4. Test with real Binance data (included!)
python backtest.py ../data/binance_usdm/btcusdt_20240808.gz
```

---

## Project Structure

```
pyxis-hft-strategy/
├── src/                  # Core code
│   ├── strategy.py       # YOUR STRATEGY HERE - Modify this!
│   ├── backtest.py       # Backtest runner (with visualization)
│   ├── visualization.py  # Charts & metrics (NEW!)
│   ├── recorder.py       # OKX data collector
│   ├── normalize.py      # Data processing
│   └── generate_dummy.py # Test data generator
│
├── data/                 # Market data
│   ├── binance_usdm/     # Binance Futures (BTC, ETH)
│   ├── binance_spot/     # Binance Spot
│   └── bybit/            # Bybit data
│
├── notebooks/            # 21 tutorial notebooks!
└── docs/                 # Documentation
```

---

## How to Test Your Own Strategy

### Step 1: Create your strategy file

```python
# src/my_strategy.py
from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT

@njit
def my_strategy(hbt, stat):
    """
    Your custom strategy here!
    
    hbt: Backtest engine object
    stat: State array for tracking orders
    """
    asset_no = 0
    
    while True:
        ret = hbt.elapse(100_000_000)  # 100ms steps
        if ret != 0:
            break
        
        hbt.clear_inactive_orders(asset_no)
        
        depth = hbt.depth(asset_no)
        if depth.best_bid == 0 or depth.best_ask == 0:
            continue
        
        mid_price = (depth.best_bid + depth.best_ask) / 2.0
        position = hbt.position(asset_no)
        
        # ========================================
        # YOUR TRADING LOGIC HERE
        # ========================================
        
        # Example: Simple market making
        bid_price = mid_price - 1.0
        ask_price = mid_price + 1.0
        
        # Submit orders
        hbt.submit_buy_order(asset_no, 1, bid_price, 1.0, GTX, LIMIT, False)
        hbt.submit_sell_order(asset_no, 2, ask_price, 1.0, GTX, LIMIT, False)
```

### Step 2: Run backtest

```bash
cd src

# Edit backtest.py to import your strategy:
# from my_strategy import my_strategy

python backtest.py ../data/binance_usdm/btcusdt_20240808.gz
```

### Step 3: View results with visualization

```bash
# Results will show:
# - PnL curve
# - Drawdown chart
# - Position over time
# - Sharpe ratio, Max DD, Win rate
```

---

## Available Alpha Signals

### 1. Order Book Imbalance (OBI)
```python
imbalance = (bid_qty - ask_qty) / (bid_qty + ask_qty)
# > 0: Buy pressure, price may go up
# < 0: Sell pressure, price may go down
```

### 2. Micro Price
```python
micro_price = (bid * ask_qty + ask * bid_qty) / (bid_qty + ask_qty)
# More accurate fair price than simple mid
```

### 3. Trade Flow
```python
flow = (buy_volume - sell_volume) / (buy_volume + sell_volume)
# Recent trade direction
```

---

## Collect OKX Real Data

```bash
cd src

# Start recording (Ctrl+C to stop after 1-2 hours)
python recorder.py --symbol BTC-USDT-SWAP --output ../data/okx/

# Normalize data
python normalize.py --input ../data/okx/ --output ../data/okx_btc.npz

# Backtest with real data
python backtest.py ../data/okx_btc.npz
```

---

## Backtest Commands

```bash
# Basic run
python backtest.py <data_file>

# With options
python backtest.py data.npz --no-viz        # No visualization
python backtest.py data.npz --save          # Save report to file
python backtest.py data.npz -s snapshot.npz # Custom snapshot
```

---

## Notebooks (21 Tutorials!)

| Topic | Notebook |
|-------|----------|
| **Getting Started** | `Getting Started.ipynb` |
| **Alpha - OBI** | `Market Making with Alpha - Order Book Imbalance.ipynb` |
| **Grid Trading** | `High-Frequency Grid Trading.ipynb` |
| **Queue Position** | `Queue-Based Market Making in Large Tick Size Assets.ipynb` |
| **Multi-Asset** | `Making Multiple Markets.ipynb` |

---

## Cloud Deployment (2-week data)

**Recommended: Alibaba Cloud Hong Kong**
- Same datacenter as OKX = 1-3ms latency
- ~$25 USD/month

```bash
# On cloud server
tmux new -s recorder
python recorder.py --symbol BTC-USDT-SWAP --output data/
# Ctrl+B then D to detach
```

---

## Performance Metrics

| Metric | Target |
|--------|--------|
| PnL | > 0 |
| Sharpe Ratio | > 1.5 |
| Max Drawdown | < 10% |
| Win Rate | > 50% |

---

## References

- [hftbacktest Documentation](https://hftbacktest.readthedocs.io/)
- [Avellaneda-Stoikov Paper](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf)
- [101 Formulaic Alphas](https://arxiv.org/abs/1601.00991)
- [OKX API](https://www.okx.com/docs-v5/en/)

---

## License
MIT

---

> **Team Pyxis** - NTUFC Competition 2025
