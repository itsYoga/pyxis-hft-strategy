#!/bin/bash
# 啟動監控儀表板

echo "[INFO] Starting Pyxis HFT Strategy Dashboard..."
echo ""

# 檢查依賴
if ! command -v streamlit &> /dev/null; then
    echo "[WARN] Streamlit not found. Installing..."
    pip install streamlit plotly pandas
fi

# 啟動 Streamlit 儀表板
echo "[INFO] Starting Streamlit dashboard..."
echo "Access at: http://localhost:8501"
echo ""

streamlit run src/utils/streamlit_dashboard.py --server.port 8501 --server.address 0.0.0.0

