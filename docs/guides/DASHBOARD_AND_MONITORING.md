# 策略監控儀表板指南

## 概述

本指南說明如何使用 Web 儀表板監控策略表現，以及如何在雲端部署和監控。

---

## 本地 Web 儀表板

### 快速開始

```bash
# 安裝依賴
pip install flask pandas

# 啟動儀表板
python src/utils/dashboard.py
```

### 訪問儀表板

打開瀏覽器訪問：`http://localhost:5000`

### 功能特點

- ✅ 實時更新（每2秒）
- ✅ PnL 曲線圖
- ✅ 持倉變化圖
- ✅ MLOFI 信號圖
- ✅ 價差變化圖
- ✅ 當前狀態顯示

---

## 雲端部署和監控

### 選項 1: 使用 Flask + 雲端服務

#### 部署到 Heroku

```bash
# 1. 安裝 Heroku CLI
# 2. 創建 Procfile
echo "web: python src/utils/dashboard.py" > Procfile

# 3. 創建 requirements.txt
pip freeze > requirements.txt

# 4. 部署
heroku create hft-dashboard
git push heroku main
```

#### 部署到 Railway

```bash
# 1. 安裝 Railway CLI
npm i -g @railway/cli

# 2. 登錄
railway login

# 3. 初始化項目
railway init

# 4. 部署
railway up
```

### 選項 2: 使用 Grafana + Prometheus（推薦用於生產）

#### 設置 Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hft-strategy'
    static_configs:
      - targets: ['localhost:9090']
```

#### 設置 Grafana

1. 安裝 Grafana
2. 配置 Prometheus 數據源
3. 導入預設儀表板

### 選項 3: 使用 Streamlit（簡單易用）

```python
# src/utils/streamlit_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("HFT Strategy Dashboard")

# 讀取數據
log_file = "logs/trading/performance_latest.csv"
df = pd.read_csv(log_file)

# 顯示圖表
st.plotly_chart(px.line(df, x='timestamp', y='pnl', title='PnL Over Time'))
st.plotly_chart(px.line(df, x='timestamp', y='position', title='Position Over Time'))
```

運行：
```bash
pip install streamlit plotly
streamlit run src/utils/streamlit_dashboard.py
```

---

## 監控工具推薦

### 1. Grafana（推薦）

**優點：**
- 專業的監控和可視化工具
- 豐富的圖表類型
- 支持告警
- 可以連接多種數據源

**設置：**
```bash
# Docker 部署
docker run -d -p 3000:3000 grafana/grafana

# 訪問 http://localhost:3000
# 默認用戶名/密碼: admin/admin
```

### 2. Prometheus + Grafana

**優點：**
- 時間序列數據庫
- 強大的查詢語言
- 與 Grafana 完美集成

### 3. Datadog

**優點：**
- 雲端監控服務
- 自動發現和監控
- 豐富的集成

**缺點：**
- 付費服務（有免費層）

### 4. CloudWatch (AWS)

**適用於：**
- AWS 部署的策略
- 與其他 AWS 服務集成

---

## 告警設置

### 使用 Python 發送告警

```python
# src/utils/alert.py
import smtplib
from email.mime.text import MIMEText

def send_alert(message):
    # 發送郵件告警
    msg = MIMEText(message)
    msg['Subject'] = 'Strategy Alert'
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = 'recipient@gmail.com'
    
    # 使用 SMTP 發送
    # ...

# 或使用 Slack
import requests

def send_slack_alert(message):
    webhook_url = "YOUR_SLACK_WEBHOOK_URL"
    requests.post(webhook_url, json={"text": message})
```

### 使用 Grafana 告警

1. 在 Grafana 中設置告警規則
2. 配置通知渠道（郵件、Slack、PagerDuty等）
3. 設置閾值（如 PnL < -1000）

---

## 移動端監控

### 使用 Grafana Mobile App

1. 安裝 Grafana Mobile App
2. 連接到 Grafana 服務器
3. 查看儀表板

### 使用 Telegram Bot

```python
# src/utils/telegram_monitor.py
import telegram
from telegram.ext import Updater

bot = telegram.Bot(token='YOUR_BOT_TOKEN')

def send_update(message):
    bot.send_message(chat_id='YOUR_CHAT_ID', text=message)
```

---

## 部署建議

### 雲端服務器選擇

1. **AWS EC2**
   - 穩定可靠
   - 豐富的服務集成

2. **Google Cloud Platform**
   - 強大的機器學習工具
   - 良好的文檔

3. **DigitalOcean**
   - 簡單易用
   - 價格合理

4. **Vultr / Linode**
   - 高性能
   - 全球節點

### 部署步驟

1. **設置服務器**
   ```bash
   # 安裝 Python、Git 等
   sudo apt update
   sudo apt install python3 python3-pip git
   ```

2. **克隆項目**
   ```bash
   git clone <your-repo>
   cd hft-strategy
   ```

3. **設置環境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **使用 systemd 運行**
   ```ini
   # /etc/systemd/system/hft-strategy.service
   [Unit]
   Description=HFT Strategy
   After=network.target

   [Service]
   Type=simple
   User=your_user
   WorkingDirectory=/path/to/hft-strategy
   ExecStart=/path/to/venv/bin/python src/scripts/live_trading_optimized.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **啟動服務**
   ```bash
   sudo systemctl enable hft-strategy
   sudo systemctl start hft-strategy
   sudo systemctl status hft-strategy
   ```

---

## 監控指標

### 關鍵指標

1. **PnL（損益）**
   - 當前 PnL
   - 最大回撤
   - 累計收益

2. **持倉**
   - 當前持倉
   - 最大持倉
   - 持倉變化率

3. **交易活動**
   - 訂單數量
   - 成交率
   - 平均價差

4. **信號質量**
   - MLOFI 信號強度
   - 波動率
   - Alpha 信號

5. **系統健康**
   - 連接狀態
   - 延遲
   - 錯誤率

---

## 故障排除

### 問題 1: 儀表板無法訪問

**解決方案：**
- 檢查防火牆設置
- 確認端口是否開放
- 檢查服務是否運行

### 問題 2: 數據不更新

**解決方案：**
- 檢查日誌文件是否存在
- 確認策略是否在運行
- 檢查文件權限

---

## 相關文檔

- [下單和記錄指南](TRADING_AND_LOGGING.md)
- [OKX 模擬交易指南](OKX_SIMULATED_TRADING.md)

---

*最後更新: 2025-12-13*

