# 測試檢查清單

## 🚀 快速測試流程

按照以下順序測試所有功能：

---

## 1️⃣ 安裝依賴

```bash
# 安裝所有依賴
pip install -r requirements.txt
```

**驗證：**
```bash
python -c "import numpy, numba, hftbacktest, streamlit, plotly, flask, aiohttp; print('✅ All dependencies installed')"
```

---

## 2️⃣ 測試策略回測

### 測試 Baseline vs Optimized 策略對比

```bash
python src/tests/compare_strategies.py
```

**預期結果：**
- ✅ 兩個策略都成功運行
- ✅ 顯示對比報告
- ✅ Optimized 策略 PnL >= Baseline PnL

**檢查點：**
- [ ] Baseline 策略完成
- [ ] Aggressive 策略完成
- [ ] 顯示改進百分比
- [ ] 執行時間合理（< 5秒）

---

## 3️⃣ 測試 OKX 連接

### 測試 API 連接（不下單）

```bash
python src/scripts/live_trading_optimized.py --test
```

**預期結果：**
```
🔍 Testing OKX Connection...
   Sandbox: True
   API Key: xxxxx...
   BTC Price: xxxxx
✅ Connection test successful!
```

**檢查點：**
- [ ] 連接成功
- [ ] 顯示 BTC 價格
- [ ] 沒有錯誤

---

## 4️⃣ 測試策略運行（觀察模式）

### 運行策略但不實際下單

```bash
python src/scripts/live_trading_optimized.py
```

**預期結果：**
- ✅ 連接 OKX WebSocket
- ✅ 登錄成功
- ✅ 訂閱訂單簿
- ✅ 顯示實時報價
- ✅ 自動記錄數據到 `logs/trading/`

**運行 10-30 秒後按 Ctrl+C 停止**

**檢查點：**
- [ ] 顯示實時報價（Mid, Bid, Ask）
- [ ] 顯示持倉、MLOFI、波動率
- [ ] 創建日誌文件
- [ ] 沒有錯誤

---

## 5️⃣ 測試儀表板

### 啟動 Streamlit 儀表板

```bash
# 在一個終端運行策略（生成數據）
python src/scripts/live_trading_optimized.py

# 在另一個終端啟動儀表板
streamlit run src/utils/streamlit_dashboard.py
```

**訪問：** `http://localhost:8501`

**預期結果：**
- ✅ 顯示策略狀態
- ✅ 顯示當前指標
- ✅ 顯示圖表（PnL, Position, MLOFI, Spread）
- ✅ 自動刷新

**檢查點：**
- [ ] 儀表板加載成功
- [ ] 顯示最新數據
- [ ] 圖表正常顯示
- [ ] 自動刷新工作

---

## 6️⃣ 測試優化功能

### 驗證優化是否啟用

檢查策略文件：

```bash
python -c "
import sys
sys.path.insert(0, 'src')
from strategies.aggressive import market_making_algo
import inspect
source = inspect.getsource(market_making_algo)
print('✅ Quadratic Penalty:', 'use_quadratic_penalty' in source)
print('✅ Anti-Sniffing:', 'use_anti_sniffing' in source)
print('✅ Exponential MLOFI:', 'use_exponential_decay_mlofi' in source)
"
```

**檢查點：**
- [ ] 所有優化都在代碼中
- [ ] 策略可以正常導入

---

## 7️⃣ 測試數據記錄

### 檢查記錄的數據

```bash
# 查看最新的日誌文件
ls -lt logs/trading/*.csv | head -1

# 查看數據內容
head -5 logs/trading/performance_*.csv
```

**檢查點：**
- [ ] CSV 文件存在
- [ ] 包含所有欄位（timestamp, pnl, position, mlofi 等）
- [ ] 數據格式正確

---

## 8️⃣ 測試實際下單（可選，僅在 Demo Trading）

### ⚠️ 警告：這會實際下單（但使用模擬資金）

```bash
# 1. 在 .env 中設置
echo "ENABLE_TRADING=true" >> .env

# 2. 運行策略
python src/scripts/live_trading_optimized.py
```

**檢查點：**
- [ ] 策略顯示 🟢（表示交易啟用）
- [ ] 訂單成功下單（檢查 OKX Demo Trading 界面）
- [ ] 訂單自動更新

**注意：** 只在 Demo Trading 模式下測試！

---

## 📊 完整測試腳本

創建一個自動化測試腳本：

```bash
#!/bin/bash
# scripts/run_all_tests.sh

echo "🧪 Running All Tests..."
echo ""

echo "1️⃣ Testing dependencies..."
python -c "import numpy, numba, hftbacktest, streamlit, plotly, flask, aiohttp; print('✅ Dependencies OK')" || exit 1

echo ""
echo "2️⃣ Testing strategy comparison..."
python src/tests/compare_strategies.py || exit 1

echo ""
echo "3️⃣ Testing OKX connection..."
python src/scripts/live_trading_optimized.py --test || exit 1

echo ""
echo "✅ All tests passed!"
```

---

## 🎯 推薦的測試順序

### 第一次設置

1. ✅ 安裝依賴
2. ✅ 測試 OKX 連接
3. ✅ 運行策略觀察模式（30秒）
4. ✅ 測試儀表板
5. ✅ 檢查記錄的數據

### 日常測試

1. ✅ 測試 OKX 連接
2. ✅ 運行策略觀察模式（10秒）
3. ✅ 檢查儀表板

### 部署前測試

1. ✅ 所有依賴安裝
2. ✅ 策略對比測試
3. ✅ OKX 連接測試
4. ✅ 策略運行測試
5. ✅ 儀表板測試
6. ✅ 數據記錄測試

---

## ❌ 常見問題排查

### 問題 1: 依賴安裝失敗

```bash
# 升級 pip
pip install --upgrade pip

# 單獨安裝失敗的包
pip install <package-name>
```

### 問題 2: OKX 連接失敗

- 檢查 `.env` 文件是否存在
- 確認 API credentials 正確
- 檢查網絡連接

### 問題 3: 儀表板無法訪問

- 確認 Streamlit 已安裝
- 檢查端口是否被占用
- 確認策略正在運行（生成數據）

---

## 📝 測試結果記錄

記錄測試結果：

| 測試項目 | 狀態 | 備註 |
|---------|------|------|
| 依賴安裝 | ⬜ | |
| 策略對比 | ⬜ | |
| OKX 連接 | ⬜ | |
| 策略運行 | ⬜ | |
| 儀表板 | ⬜ | |
| 數據記錄 | ⬜ | |

---

*最後更新: 2025-12-13*

