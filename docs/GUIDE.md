# HFT Strategy Backtest Guide

## Contents

1. [Quick Start](#quick-start)
2. [Running Backtest](#running-backtest)
3. [Configuration](#configuration)
4. [Live Trading](#live-trading)
5. [Monitoring & Dashboard](#monitoring--dashboard)
6. [FAQ](#faq)

---

## Quick Start

### 1. Install Dependencies

```bash
cd hft-strategy
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Basic Backtest

```bash
# With real data
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz

# Without visualization (faster)
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz --no-viz
```

---

## Running Backtest

### Basic Commands

```bash
# Basic run
python src/core/backtest.py <data_file> [--snapshot <snapshot_file>] [--no-viz] [--config <config_file>]

# With custom config
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz \
    --config config/backtest.yaml
```

### Command Line Options

- `data_file`: Market data file (required)
- `--snapshot, -s`: Snapshot file (optional, auto-detected)
- `--no-viz`: Disable visualization (faster)
- `--save`: Save report to file
- `--config, -c`: Config file path

### Supported Data Formats

- `.npz`: NumPy compressed format (recommended)
- `.npy`: NumPy array format
- `.gz`: Gzip compressed format

---

## Configuration

### Configuration Files

Located in `config/` directory.

### Main Parameters

```yaml
backtest:
  tick_size: 0.1          # Minimum price movement
  lot_size: 0.001         # Minimum order size
  initial_capital: 30000.0 # Initial capital
```

Detailed configuration: `docs/guides/CONFIGURATION_GUIDE.md`

---

## Live Trading

### OKX Simulated Trading

```bash
# Start live trading
python src/scripts/live_trading.py

# View configuration
cat .env.example
```

Detailed guide: `docs/guides/OKX_SIMULATED_TRADING.md`

### Environment Variables

Create `.env` file:

```bash
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
OKX_SANDBOX=true  # Use simulated environment
```

---

## Monitoring & Dashboard

### Streamlit Dashboard

```bash
# Start dashboard
./scripts/start_dashboard.sh

# Or manually
streamlit run src/utils/streamlit_dashboard.py
```

Visit `http://localhost:8501` for real-time monitoring.

### Flask Dashboard

```bash
python src/utils/dashboard.py
```

Visit `http://localhost:5000` for monitoring.

Detailed guide: `docs/guides/DASHBOARD_AND_MONITORING.md`

---

## FAQ

### Q: How to setup live trading?

A: Reference `docs/guides/OKX_SIMULATED_TRADING.md` and `docs/guides/QUICK_START_OKX.md`

### Q: How to view performance?

A: Use Streamlit or Flask dashboard, or check log files in `logs/trading/` directory.

---

## Related Documentation

- **Test Results**: `docs/results/`
- **Configuration Guide**: `docs/guides/CONFIGURATION_GUIDE.md`

---

*Last updated: 2025-01*
