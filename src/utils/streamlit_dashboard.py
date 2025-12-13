"""
Streamlit Dashboard for Pyxis HFT Strategy
==========================================
簡單易用的實時監控儀表板

使用方法:
    pip install streamlit plotly pandas
    streamlit run src/utils/streamlit_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import time

st.set_page_config(
    page_title="Pyxis HFT Strategy Dashboard",
    page_icon=None,
    layout="wide"
)

st.title("Pyxis HFT Strategy Dashboard")

# 獲取最新的日誌文件
def get_latest_log_file():
    log_dir = Path('logs/trading')
    if not log_dir.exists():
        return None
    csv_files = list(log_dir.glob('performance_*.csv'))
    if not csv_files:
        return None
    return max(csv_files, key=lambda p: p.stat().st_mtime)

# 自動刷新
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 60, 5)

log_file = get_latest_log_file()

if log_file and log_file.exists():
    try:
        df = pd.read_csv(log_file)
        
        # 檢查策略是否在運行
        file_mtime = log_file.stat().st_mtime
        time_diff = datetime.now().timestamp() - file_mtime
        is_running = time_diff < 300  # 5分鐘內更新認為在運行
        
        # 狀態顯示
        col1, col2, col3 = st.columns(3)
        with col1:
            status_text = "Running" if is_running else "Stopped"
            st.metric("Status", status_text)
        
        with col2:
            if len(df) > 0:
                latest = df.iloc[-1]
                st.metric("Current PnL", f"${latest.get('pnl', 0):.2f}")
        
        with col3:
            if len(df) > 0:
                latest = df.iloc[-1]
                st.metric("Position", f"{latest.get('position', 0):.4f}")
        
        # 最新數據
        if len(df) > 0:
            latest = df.iloc[-1]
            
            st.subheader("Current Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mid Price", f"${latest.get('mid_price', 0):.2f}")
            with col2:
                spread = latest.get('spread', 0)
                if spread == 0:
                    spread = latest.get('ask_price', 0) - latest.get('bid_price', 0)
                st.metric("Spread", f"${spread:.2f}")
            with col3:
                st.metric("MLOFI", f"{latest.get('mlofi', 0):.3f}")
            with col4:
                st.metric("Volatility", f"{latest.get('volatility', 0):.2f}")
        
        # 圖表
        st.subheader("Performance Charts")
        
        # 轉換時間戳
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # PnL 圖
        col1, col2 = st.columns(2)
        with col1:
            fig_pnl = px.line(df, x='timestamp', y='pnl', title='PnL Over Time',
                             labels={'pnl': 'PnL ($)', 'timestamp': 'Time'})
            fig_pnl.update_traces(line_color='#4CAF50')
            st.plotly_chart(fig_pnl, use_container_width=True)
        
        with col2:
            fig_position = px.line(df, x='timestamp', y='position', title='Position Over Time',
                                 labels={'position': 'Position', 'timestamp': 'Time'})
            fig_position.update_traces(line_color='#2196F3')
            st.plotly_chart(fig_position, use_container_width=True)
        
        # MLOFI 和 Spread
        col1, col2 = st.columns(2)
        with col1:
            fig_mlofi = px.line(df, x='timestamp', y='mlofi', title='MLOFI Signal',
                               labels={'mlofi': 'MLOFI', 'timestamp': 'Time'})
            fig_mlofi.update_traces(line_color='#FF9800')
            st.plotly_chart(fig_mlofi, use_container_width=True)
        
        with col2:
            if 'spread' in df.columns:
                fig_spread = px.line(df, x='timestamp', y='spread', title='Spread Over Time',
                                    labels={'spread': 'Spread ($)', 'timestamp': 'Time'})
            else:
                df['spread'] = df['ask_price'] - df['bid_price']
                fig_spread = px.line(df, x='timestamp', y='spread', title='Spread Over Time',
                                    labels={'spread': 'Spread ($)', 'timestamp': 'Time'})
            fig_spread.update_traces(line_color='#9C27B0')
            st.plotly_chart(fig_spread, use_container_width=True)
        
        # 統計摘要
        st.subheader("Statistics Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            if 'pnl' in df.columns:
                st.metric("Max PnL", f"${df['pnl'].max():.2f}")
        with col3:
            if 'pnl' in df.columns:
                st.metric("Min PnL", f"${df['pnl'].min():.2f}")
        with col4:
            if 'position' in df.columns:
                st.metric("Max Position", f"{df['position'].abs().max():.4f}")
        
        # 數據表格
        with st.expander("View Raw Data"):
            st.dataframe(df.tail(100))
        
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the strategy is running and generating log files.")
else:
    st.warning("No log file found. Please start the strategy first.")
    st.info("Run: `python src/scripts/live_trading_optimized.py`")

