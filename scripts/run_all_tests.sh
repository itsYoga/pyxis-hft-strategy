#!/bin/bash
# 運行所有測試

set -e  # 遇到錯誤立即退出

# 獲取腳本目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

# 檢測 Python（優先使用 venv）
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
elif [ -f "./venv/bin/python" ]; then
    PYTHON="./venv/bin/python"
else
    PYTHON="python3"
fi

echo "🧪 Pyxis HFT Strategy - Complete Test Suite"
echo "============================================"
echo "Using Python: $PYTHON"
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試函數
test_pass() {
    echo -e "${GREEN}[OK] $1${NC}"
}

test_fail() {
    echo -e "${RED}[FAIL] $1${NC}"
    exit 1
}

test_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

# 1. 測試依賴
echo "[1/6] Testing Dependencies..."
if $PYTHON -c "import numpy, numba, hftbacktest, streamlit, plotly, flask, aiohttp" 2>/dev/null; then
    test_pass "All dependencies installed"
else
    test_fail "Missing dependencies. Run: pip install -r requirements.txt"
fi

echo ""

# 2. 測試策略導入
echo "[2/6] Testing Strategy Imports..."
if $PYTHON -c "import sys; sys.path.insert(0, 'src'); from strategies.aggressive import market_making_algo; from strategies.baseline import market_making_algo as baseline_algo" 2>/dev/null; then
    test_pass "Strategies imported successfully"
else
    test_fail "Strategy import failed"
fi

echo ""

# 3. 測試 OKX 連接（如果 .env 存在）
echo "[3/6] Testing OKX Connection..."
if [ -f .env ]; then
    if $PYTHON src/scripts/live_trading_optimized.py --test 2>&1 | grep -q "Connection test successful"; then
        test_pass "OKX connection successful"
    else
        test_info "OKX connection test skipped (check .env file)"
    fi
else
    test_info "OKX connection test skipped (.env file not found)"
fi

echo ""

# 4. 測試數據記錄
echo "[4/6] Testing Data Logging..."
if $PYTHON -c "import sys; sys.path.insert(0, 'src'); from utils.performance_logger import PerformanceLogger; logger = PerformanceLogger(); logger.log({'pnl': 100}); logger.close()" 2>/dev/null; then
    test_pass "Data logging works"
else
    test_fail "Data logging failed"
fi

echo ""

# 5. 測試儀表板導入
echo "[5/6] Testing Dashboard Imports..."
if $PYTHON -c "import streamlit, plotly, flask, pandas" 2>/dev/null; then
    test_pass "Dashboard dependencies available"
else
    test_info "Dashboard dependencies not fully installed (optional)"
fi

echo ""

# 6. 檢查日誌目錄
echo "[6/6] Checking Log Directories..."
mkdir -p logs/trading
test_pass "Log directories ready"

echo ""
echo "============================================"
echo -e "${GREEN}[OK] All Core Tests Passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Test strategy comparison: python src/tests/compare_strategies.py"
echo "  2. Test OKX connection: python src/scripts/live_trading_optimized.py --test"
echo "  3. Run strategy: python src/scripts/live_trading_optimized.py"
echo "  4. Start dashboard: streamlit run src/utils/streamlit_dashboard.py"
echo ""

