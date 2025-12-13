# OKX 模擬交易指南

## 概述

本指南說明如何使用優化後的策略在 OKX Demo Trading (Sandbox) 進行模擬交易。

---

## 前置準備

### 1. 獲取 OKX Demo Trading API

1. 訪問 [OKX 官網](https://www.okx.com)
2. 註冊/登錄帳號
3. 前往 **API 管理** → **創建 API**
4. 選擇 **Demo Trading** (模擬交易) 模式
5. 設置權限：**Trade** (交易權限)
6. 記錄以下信息：
   - API Key
   - Secret Key
   - Passphrase

### 2. 安裝依賴

```bash
# 確保已安裝所需套件
pip install websockets python-dotenv
```

---

## 設置步驟

### 步驟 1: 創建 .env 文件

```bash
# 複製範例文件
cp .env.example .env

# 編輯 .env 文件，填入你的 API 信息
```

編輯 `.env` 文件：

```env
OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_PASSPHRASE=your_passphrase_here

SYMBOL=BTC-USDT-SWAP
SANDBOX=true  # true = Demo Trading, false = Real Trading
```

### 步驟 2: 測試連接

```bash
# 測試 OKX 連接（不進行交易）
python src/scripts/live_trading_optimized.py --test
```

**預期輸出：**
```
🔍 Testing OKX Connection...
   Sandbox: True
   API Key: abc12345...
   BTC Price: 61234.5
✅ Connection test successful!
```

如果連接失敗，請檢查：
- API credentials 是否正確
- 網絡連接是否正常
- API 是否啟用了 Trade 權限

---

## 啟動模擬交易

### 使用優化後的策略

```bash
# 啟動優化後的策略（包含所有優化）
python src/scripts/live_trading_optimized.py
```

### 使用原始策略

```bash
# 啟動原始策略
python src/scripts/live_trading.py
```

---

## 運行輸出示例

```
============================================================
🤖 Pyxis HFT Trading Bot (Optimized Strategy)
============================================================
Symbol: BTC-USDT-SWAP
Sandbox Mode: True
API Key: abc12345...
============================================================

📡 Connecting to OKX Public WebSocket...
   Symbol: BTC-USDT-SWAP
   Sandbox: True
✅ Subscribed to BTC-USDT-SWAP order book (5 levels)

🔐 Connecting to OKX Private WebSocket...
✅ Login successful!
✅ Subscribed to orders and positions

🚀 Starting Optimized Trading Strategy...
   Strategy: Aggressive Market Making (Optimized)
   Optimizations: Quadratic Penalty, Anti-Sniffing, Exponential MLOFI
   Parameters: gamma=0.05, k=1.5, max_pos=10.0

[14:30:15] Mid: 61234.5 | Bid: 61233.2 | Ask: 61235.8 | Pos: 0.0000 | MLOFI: +0.123 | Vol: 12.34
[14:30:16] Mid: 61235.1 | Bid: 61233.8 | Ask: 61236.4 | Pos: 0.0000 | MLOFI: +0.145 | Vol: 12.35
...
```

---

## 策略說明

### 優化後的策略包含

1. **二次庫存懲罰** (Quadratic Inventory Penalty)
   - 庫存接近限制時更激進地擴大價差
   - 更好的庫存邊界控制

2. **反嗅探邏輯** (Anti-Sniffing Logic)
   - 掩蓋庫存意圖，防止掠奪性算法識別
   - 降低被 front-run 的風險

3. **指數衰減 MLOFI** (Exponential Decay MLOFI)
   - 使用 5 層訂單簿深度
   - 給 Level 1-2 更高權重
   - 降低深層訂單簿的"欺騙"影響

### 策略參數

可以在 `live_trading_optimized.py` 中調整：

```python
# Strategy parameters
self.gamma_base = 0.05      # 風險厭惡係數
self.k_base = 1.5           # 價差參數
self.max_position = 10.0    # 最大持倉
self.order_qty = 0.01       # 訂單數量

# Alpha weights
self.micro_weight = 0.2     # Micro price 權重
self.mlofi_weight = 0.8     # MLOFI 權重

# Optimization flags
self.use_quadratic_penalty = True
self.use_anti_sniffing = True
self.use_exponential_decay_mlofi = True
```

---

## 安全提示

### ⚠️ 重要警告

1. **Demo Trading 模式**
   - 默認使用 `SANDBOX=true`（模擬交易）
   - 不會使用真實資金
   - 適合測試和學習

2. **實盤交易風險**
   - 如果設置 `SANDBOX=false`，將使用真實資金
   - **強烈不建議**在實盤上直接使用未經充分測試的策略
   - 請先在 Demo Trading 中充分測試

3. **API 安全**
   - 不要將 `.env` 文件提交到版本控制
   - 使用強密碼保護 API
   - 定期輪換 API keys

---

## 故障排除

### 問題 1: 連接失敗

**錯誤：** `Connection test failed`

**解決方案：**
1. 檢查 `.env` 文件是否正確設置
2. 確認 API credentials 是否正確
3. 檢查網絡連接
4. 確認 API 是否啟用了 Trade 權限

### 問題 2: 登錄失敗

**錯誤：** `Login failed`

**解決方案：**
1. 檢查 API Key、Secret Key、Passphrase 是否正確
2. 確認 API 是否啟用了 Trade 權限
3. 檢查 API 是否在 Demo Trading 模式下創建

### 問題 3: 沒有市場數據

**錯誤：** 沒有收到訂單簿更新

**解決方案：**
1. 檢查 WebSocket 連接是否正常
2. 確認訂閱的 symbol 是否正確
3. 檢查網絡連接

---

## 監控和日誌

### 實時監控

策略運行時會顯示：
- 中間價 (Mid Price)
- 買入價 (Bid Price)
- 賣出價 (Ask Price)
- 當前持倉 (Position)
- MLOFI 信號
- 波動率 (Volatility)

### 停止策略

按 `Ctrl+C` 安全停止策略

---

## 下一步

1. ✅ 設置 API credentials
2. ✅ 測試連接
3. ✅ 啟動模擬交易
4. ⏳ 監控策略表現
5. ⏳ 調整參數優化表現
6. ⏳ 分析交易結果

---

## 相關文檔

- [策略優化報告](../reports/STRATEGY_OPTIMIZATION_ROADMAP.md)
- [測試優化效果](HOW_TO_TEST_OPTIMIZATIONS.md)
- [優化實施狀態](../reports/OPTIMIZATION_STATUS.md)

---

*最後更新: 2025-12-13*

