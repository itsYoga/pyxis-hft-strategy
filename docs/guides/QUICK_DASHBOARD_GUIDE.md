# 快速儀表板指南

## 🚀 最簡單的方法：Streamlit Dashboard

### 安裝和啟動

```bash
# 安裝依賴
pip install streamlit plotly pandas

# 啟動儀表板
streamlit run src/utils/streamlit_dashboard.py
```

或使用腳本：

```bash
./scripts/start_dashboard.sh
```

### 訪問

打開瀏覽器訪問：`http://localhost:8501`

### 功能

- ✅ 實時更新（可設置自動刷新）
- ✅ PnL 曲線圖
- ✅ 持倉變化圖
- ✅ MLOFI 信號圖
- ✅ 價差變化圖
- ✅ 當前指標顯示
- ✅ 數據表格查看

---

## 🌐 雲端部署

### 選項 1: Streamlit Cloud（最簡單）

1. 推送到 GitHub
2. 訪問 [streamlit.io/cloud](https://streamlit.io/cloud)
3. 連接 GitHub 倉庫
4. 選擇 `src/utils/streamlit_dashboard.py` 作為主文件
5. 部署完成！

### 選項 2: Railway

```bash
# 1. 安裝 Railway CLI
npm i -g @railway/cli

# 2. 登錄
railway login

# 3. 初始化
railway init

# 4. 設置啟動命令
railway variables set START_COMMAND="streamlit run src/utils/streamlit_dashboard.py --server.port $PORT"

# 5. 部署
railway up
```

### 選項 3: Heroku

```bash
# 1. 創建 Procfile
echo "web: streamlit run src/utils/streamlit_dashboard.py --server.port \$PORT --server.address 0.0.0.0" > Procfile

# 2. 創建 setup.sh
echo "mkdir -p ~/.streamlit/
echo '[server]
headless = true
port = \$PORT
enableCORS = false
' > ~/.streamlit/config.toml" > setup.sh

# 3. 部署
heroku create pyxis-dashboard
git push heroku main
```

---

## 📱 移動端訪問

### 使用 ngrok（本地測試）

```bash
# 1. 安裝 ngrok
brew install ngrok  # macOS
# 或下載從 https://ngrok.com

# 2. 啟動儀表板
streamlit run src/utils/streamlit_dashboard.py

# 3. 在另一個終端
ngrok http 8501

# 4. 使用 ngrok 提供的 URL 訪問
```

### 雲端部署後

- 直接使用雲端服務提供的 URL
- 可以在手機瀏覽器中訪問
- Streamlit 自動適配移動端

---

## 🔔 告警設置

### 簡單的 Python 告警腳本

```python
# src/utils/check_and_alert.py
import pandas as pd
from pathlib import Path
import requests

def check_strategy():
    log_file = Path('logs/trading/performance_latest.csv')
    if not log_file.exists():
        return
    
    df = pd.read_csv(log_file)
    if len(df) == 0:
        return
    
    latest = df.iloc[-1]
    
    # 檢查 PnL
    if latest['pnl'] < -1000:
        send_alert(f"⚠️ PnL Alert: {latest['pnl']:.2f}")
    
    # 檢查持倉
    if abs(latest['position']) > 9:
        send_alert(f"⚠️ Position Alert: {latest['position']:.4f}")

def send_alert(message):
    # Slack webhook
    webhook_url = "YOUR_SLACK_WEBHOOK_URL"
    requests.post(webhook_url, json={"text": message})
    
    # 或發送郵件
    # ...

if __name__ == '__main__':
    check_strategy()
```

---

## 📊 推薦的監控工具

### 1. Streamlit（推薦用於快速開始）

**優點：**
- 簡單易用
- 快速部署
- 免費雲端部署（Streamlit Cloud）

**適用於：**
- 快速原型
- 個人項目
- 小團隊

### 2. Grafana（推薦用於生產）

**優點：**
- 專業監控
- 豐富的圖表
- 告警功能
- 多數據源支持

**適用於：**
- 生產環境
- 團隊協作
- 長期監控

### 3. Datadog

**優點：**
- 雲端服務
- 自動發現
- 豐富集成

**適用於：**
- 企業級應用
- 多服務監控

---

## 🎯 快速開始

1. **本地測試**
   ```bash
   pip install streamlit plotly pandas
   streamlit run src/utils/streamlit_dashboard.py
   ```

2. **雲端部署**
   - 推送到 GitHub
   - 使用 Streamlit Cloud 部署（免費）

3. **設置告警**
   - 使用 Slack/Telegram webhook
   - 或設置郵件告警

---

*最後更新: 2025-12-13*

