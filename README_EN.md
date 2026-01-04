# HFT Strategy Backtest

**English** | **[中文](README.md)**

A High-Frequency Trading (HFT) Market Making backtesting framework.

---

## Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd hft-strategy

# 2. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Test with sample data
python src/scripts/generate_dummy.py
python src/core/backtest.py data/dummy_data.npy

# 4. Test with real Binance data
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz
```

---

## Project Structure

```
hft-strategy/
├── src/                       # Core code
│   ├── core/                  # Core functionality
│   │   ├── backtest.py        # Backtest runner
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
│
├── data/                      # Market data
│   ├── binance_usdm/          # Binance Futures (BTC, ETH)
│   ├── binance_spot/          # Binance Spot
│   ├── bybit/                 # Bybit data
│   └── dummy_data.npy         # Test data
│
├── notebooks/                 # Tutorial notebooks
├── docs/                      # Documentation
└── config/                    # Configuration files
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

## Collect OKX Real Data

```bash
# Start recording
python src/scripts/recorder.py --symbol BTC-USDT-SWAP --output data/okx/

# Normalize data
python src/scripts/normalize.py --input data/okx/ --output data/okx_btc.npz

# Backtest with real data
python src/core/backtest.py data/okx_btc.npz
```

---

## Live Trading (OKX Demo)

```bash
# 1. Setup API
cp .env.example .env
# Edit .env with your OKX Demo Trading API Key/Secret/Passphrase

# 2. Test connection
python src/scripts/live_trading.py --test

# 3. Start trading
python src/scripts/live_trading.py
```

**Detailed Guide:** See [OKX Simulated Trading Guide](docs/guides/OKX_SIMULATED_TRADING.md)

---

## Notebooks

| Topic | Notebook |
|-------|----------|
| **Getting Started** | `Getting Started.ipynb` |
| **Grid Trading** | `High-Frequency Grid Trading.ipynb` |
| **Queue Position** | `Queue-Based Market Making in Large Tick Size Assets.ipynb` |
| **Multi-Asset** | `Making Multiple Markets.ipynb` |
| **GLFT Model** | `GLFT Market Making Model and Grid Trading.ipynb` |
| **Latency Impact** | `Impact of Order Latency.ipynb` |

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
- [River ML](https://riverml.xyz/)
- [Avellaneda-Stoikov Paper](https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf)
- [OKX API](https://www.okx.com/docs-v5/en/)

---

## License
MIT
