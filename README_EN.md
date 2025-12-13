# Pyxis HFT Strategy Framework

**[中文版](README.md)** | **English**

A High-Frequency Trading (HFT) Market Making framework implementing multi-level order flow imbalance strategies.

## Team Pyxis - NTUFC 2025

---

## ✨ New Features (2025-12)

- **MLOFI** - Multi-Level Order Flow Imbalance (5 levels)
- **LOB Slope** - Order Book Elasticity
- **Regime Detection** - Auto-adjust strategy based on volatility
- **River Online Learning** - Dynamic alpha weight adjustment
- **A/B Testing Framework** - Evaluate strategy improvements
- **Modular Refactoring** - Clean directory structure for better maintainability
- **Quadratic Inventory Penalty** - Stricter inventory boundary control
- **Anti-Sniffing Logic** - Prevent predatory algorithms from detecting inventory intent
- **Exponential Decay MLOFI** - Optimized multi-level signal weighting

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
pip install river  # Online learning (optional)

# 3. Test with sample data
python src/scripts/generate_dummy.py
python src/core/backtest.py data/dummy_data.npy

# 4. Test with real Binance data (included!)
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz

# 5. Strategy comparison test
python src/tests/compare_strategies.py
```

---

## Project Structure

```
pyxis-hft-strategy/
├── src/                       # Core code
│   ├── strategies/            # Strategy implementations
│   │   ├── aggressive.py     # ⭐ Aggressive Strategy (MLOFI + Regime)
│   │   └── baseline.py        # Original baseline for comparison
│   │
│   ├── core/                  # Core functionality
│   │   ├── backtest.py        # Backtest runner (with visualization)
│   │   ├── data_loader.py     # Data loader
│   │   └── config_loader.py   # Configuration loader
│   │
│   ├── utils/                 # Utility modules
│   │   ├── logger.py          # Logging system
│   │   ├── visualization.py   # Charts & metrics
│   │   ├── result_viewer.py   # Result viewer
│   │   └── reconciliation.py  # Trade reconciliation
│   │
│   ├── scripts/               # Executable scripts
│   │   ├── recorder.py        # OKX data collector
│   │   ├── normalize.py       # Data processing
│   │   ├── generate_dummy.py  # Test data generator
│   │   └── live_trading.py    # Live trading
│   │
│   ├── learning/              # Online learning
│   │   ├── online_learning.py # River online learning
│   │   └── ab_testing.py      # A/B testing framework
│   │
│   └── tests/                 # Test files
│       ├── compare_strategies.py  # Strategy comparison test
│       └── ...
│
├── data/                      # Market data
│   ├── binance_usdm/          # ✓ Binance Futures (BTC, ETH)
│   ├── binance_spot/          # Binance Spot
│   ├── bybit/                 # Bybit data
│   ├── dummy_data.npy         # Test data
│   └── dummy_snapshot.npz     # Test snapshot
│
├── notebooks/                 # 21 tutorial notebooks!
└── docs/                      # Documentation
```

---

## How to Test Your Own Strategy

### Step 1: Create your strategy file

```python
# src/strategies/my_strategy.py
from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT

@njit
def market_making_algo(hbt, stat):
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
# Edit src/core/backtest.py to import your strategy:
# from strategies.my_strategy import market_making_algo

python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz
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

## Alpha Signals

### Level 1 (Basic)

#### 1. Order Book Imbalance (OBI)
```python
imbalance = (bid_qty - ask_qty) / (bid_qty + ask_qty)
# > 0: Buy pressure, price may go up
# < 0: Sell pressure, price may go down
```

#### 2. Micro Price
```python
micro_price = (bid * ask_qty + ask * bid_qty) / (bid_qty + ask_qty)
# More accurate fair price than simple mid
```

#### 3. Trade Flow
```python
flow = (buy_volume - sell_volume) / (buy_volume + sell_volume)
# Recent trade direction
```

### Level 2 (Advanced)

| Signal | Description |
|--------|-------------|
| **MLOFI** | 5-level order flow imbalance |
| **LOB Slope** | Order book elasticity |
| **EPI** | Expected Price Impact (MLOFI/Slope) |

---

## Strategy Comparison

```bash
# Run comparison test (Baseline vs Optimized)
python src/tests/compare_strategies.py

# Or use test script
./scripts/test_optimization.sh
```

**Testing Optimizations:**
- See [Testing Guide](docs/guides/HOW_TO_TEST_OPTIMIZATIONS.md) for how to verify optimization effectiveness

# Sample output:
# ============================================================
# STRATEGY COMPARISON REPORT
# ============================================================
# Baseline PnL: +1,120.95
# Aggressive PnL:  +427.00
# Improvement:    -61.91%
# Winner:         Baseline
```

---

## River Online Learning

```python
from learning.online_learning import OnlineAlphaLearner, AlphaSignals

learner = OnlineAlphaLearner(learning_rate=0.01)

# Each timestep
signals = AlphaSignals(micro_price_alpha=0.5, mlofi_alpha=0.8, ...)
learner.observe(signals)
weights = learner.get_weights()
```

**Evaluate River effectiveness:**
```bash
python src/learning/ab_testing.py
```

---

## Collect OKX Real Data

```bash
# Start recording (Ctrl+C to stop after 1-2 hours)
python src/scripts/recorder.py --symbol BTC-USDT-SWAP --output data/okx/

# Normalize data
python src/scripts/normalize.py --input data/okx/ --output data/okx_btc.npz

# Backtest with real data
python src/core/backtest.py data/okx_btc.npz
```

---

## Backtest Commands

```bash
# Basic run
python src/core/backtest.py <data_file>

# With options
python src/core/backtest.py data.npz --no-viz        # No visualization
python src/core/backtest.py data.npz --save          # Save report to file
python src/core/backtest.py data.npz -s snapshot.npz # Custom snapshot
```

---

## Live Trading (OKX Demo)

### Using Optimized Strategy (Recommended)

```bash
# 1. Setup API (copy .env.example and fill in your API)
cp .env.example .env
# Edit .env with your OKX Demo Trading API Key/Secret/Passphrase

# 2. Test connection
python src/scripts/live_trading_optimized.py --test

# 3. Start optimized strategy (includes all optimizations)
python src/scripts/live_trading_optimized.py
```

### Using Original Strategy

```bash
# Test connection
python src/scripts/live_trading.py --test

# Start trading
python src/scripts/live_trading.py
```

**Detailed Guide:** See [OKX Simulated Trading Guide](docs/guides/OKX_SIMULATED_TRADING.md)

---

## Notebooks (21 Tutorials!)

| Topic | Notebook |
|-------|----------|
| **Getting Started** | `Getting Started.ipynb` |
| **Alpha - OBI** | `Market Making with Alpha - Order Book Imbalance.ipynb` |
| **Grid Trading** | `High-Frequency Grid Trading.ipynb` |
| **Queue Position** | `Queue-Based Market Making in Large Tick Size Assets.ipynb` |
| **Multi-Asset** | `Making Multiple Markets.ipynb` |
| **APT Alpha** | `Market Making with Alpha - APT.ipynb` |
| **Basis Alpha** | `Market Making with Alpha - Basis.ipynb` |
| **GLFT Model** | `GLFT Market Making Model and Grid Trading.ipynb` |
| **Latency Impact** | `Impact of Order Latency.ipynb` |

---

## Cloud Deployment (2-week data)

**Recommended: Alibaba Cloud Hong Kong**
- Same datacenter as OKX = 1-3ms latency
- ~$25 USD/month

```bash
# On cloud server
tmux new -s recorder
python src/scripts/recorder.py --symbol BTC-USDT-SWAP --output data/
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

## Strategy Optimization Roadmap

We have developed a comprehensive optimization plan from stochastic control to deep reinforcement learning:

- **[Strategy Optimization Analysis](docs/reports/STRATEGY_OPTIMIZATION_ROADMAP.md)** - Detailed optimization theory and mathematical framework
- **[Implementation Plan](docs/reports/IMPLEMENTATION_PLAN.md)** - Phase-by-phase implementation guide

**Optimization Focus:**
- 🛡️ Defensive Mechanisms: Anti-Sniffing logic
- ⚠️ Flow Toxicity: VPIN detection
- 🤖 Dynamic Control: Alpha-AS Deep Reinforcement Learning architecture
- 📊 Execution Precision: Queue position simulation

---

## References

- [hftbacktest Documentation](https://hftbacktest.readthedocs.io/)
- [River ML](https://riverml.xyz/)
- [Avellaneda-Stoikov Paper](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf)
- [101 Formulaic Alphas](https://arxiv.org/abs/1601.00991)
- [OKX API](https://www.okx.com/docs-v5/en/)

---

## License
MIT

---

> **Team Pyxis** - NTUFC Competition 2025
