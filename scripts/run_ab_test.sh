#!/bin/bash
# run_ab_test_real_data.sh
# Run A/B test with real Binance data

echo "========================================"
echo "A/B Test: Static vs River (Real Data)"
echo "========================================"

cd "$(dirname "$0")/.."

# Check for real data
if [ -f "data/binance_usdm/btcusdt_20240808.npz" ]; then
    echo "✓ Found real Binance data"
    DATA_FILE="data/binance_usdm/btcusdt_20240808.npz"
    SNAPSHOT_FILE="data/binance_usdm/btcusdt_20240808_eod.npz"
else
    echo "✗ No real data found, using dummy data"
    DATA_FILE="src/dummy_data.npy"
    SNAPSHOT_FILE="src/dummy_snapshot.npz"
fi

echo "Data: $DATA_FILE"
echo ""

# Run backtest with baseline strategy
echo "Step 1: Running baseline backtest..."
./venv/bin/python src/backtest.py "$DATA_FILE" --snapshot "$SNAPSHOT_FILE" --no-viz 2>&1 | tee /tmp/baseline_result.txt

echo ""
echo "Step 2: A/B Test complete!"
echo ""
echo "To compare with River, integrate online_learning.py into strategy.py"
echo "and run the backtest again."
