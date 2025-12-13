# 實際下單和策略記錄指南

## 概述

本指南說明如何啟用實際下單功能和策略表現記錄。

---

## 啟用實際下單

### 步驟 1: 設置環境變數

在 `.env` 文件中添加：

```env
ENABLE_TRADING=true  # 啟用實際下單（默認為 false，只顯示報價）
```

### 步驟 2: 運行策略

```bash
python src/scripts/live_trading_optimized.py
```

**注意：**
- 默認情況下，策略只會顯示報價，不會實際下單
- 設置 `ENABLE_TRADING=true` 後才會實際下單
- 確保在 Demo Trading 模式下測試

---

## 策略表現記錄

### 自動記錄

策略運行時會自動記錄以下數據到 `logs/trading/` 目錄：

1. **CSV 文件** (`performance_YYYYMMDD_HHMMSS.csv`)
   - 時間戳
   - 中間價、買入價、賣出價
   - 持倉、MLOFI、波動率
   - 庫存價格、價差、偏斜
   - 餘額、權益、PnL

2. **JSON 文件** (`performance_YYYYMMDD_HHMMSS.json`)
   - 詳細的策略數據
   - 用於後續分析

### 記錄的數據

| 欄位 | 說明 |
|------|------|
| timestamp | 時間戳 |
| mid_price | 市場中間價 |
| bid_price | 策略買入報價 |
| ask_price | 策略賣出報價 |
| position | 當前持倉 |
| mlofi | 多層級訂單流不平衡 |
| volatility | 波動率 |
| reservation_price | 庫存價格 |
| spread | 價差 |
| skew | 偏斜 |
| balance | 餘額 |
| equity | 權益 |
| pnl | 損益 |

---

## 分析記錄數據

### 使用 Python 分析

```python
import pandas as pd
import matplotlib.pyplot as plt

# 讀取 CSV 數據
df = pd.read_csv('logs/trading/performance_20241213_054600.csv')

# 繪製 PnL 曲線
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['pnl'])
plt.title('PnL Over Time')
plt.xlabel('Time')
plt.ylabel('PnL')
plt.show()

# 分析 MLOFI 信號
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['mlofi'])
plt.title('MLOFI Signal Over Time')
plt.xlabel('Time')
plt.ylabel('MLOFI')
plt.show()

# 分析價差
spread = df['ask_price'] - df['bid_price']
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], spread)
plt.title('Spread Over Time')
plt.xlabel('Time')
plt.ylabel('Spread')
plt.show()
```

### 統計分析

```python
# 基本統計
print(df.describe())

# PnL 統計
print(f"Total PnL: {df['pnl'].iloc[-1]:.2f}")
print(f"Max PnL: {df['pnl'].max():.2f}")
print(f"Min PnL: {df['pnl'].min():.2f}")

# 價差統計
spread = df['ask_price'] - df['bid_price']
print(f"Average Spread: {spread.mean():.2f}")
print(f"Min Spread: {spread.min():.2f}")
print(f"Max Spread: {spread.max():.2f}")

# MLOFI 統計
print(f"Average MLOFI: {df['mlofi'].mean():.3f}")
print(f"MLOFI Std: {df['mlofi'].std():.3f}")
```

---

## 下單功能說明

### 下單邏輯

策略會：
1. 計算最優買入價和賣出價
2. 取消舊訂單（如果價格變化超過閾值）
3. 下新訂單（如果價格合理）

### 訂單管理

- **自動撤單**：當報價變化時，自動取消舊訂單
- **訂單追蹤**：追蹤所有活躍訂單
- **錯誤處理**：處理下單失敗的情況

---

## 安全提示

### ⚠️ 重要警告

1. **Demo Trading 模式**
   - 默認使用 `SANDBOX=true`（模擬交易）
   - 不會使用真實資金

2. **實盤交易風險**
   - 如果設置 `SANDBOX=false`，將使用真實資金
   - **強烈不建議**在實盤上直接使用未經充分測試的策略
   - 請先在 Demo Trading 中充分測試

3. **下單控制**
   - 使用 `ENABLE_TRADING=false` 可以只觀察報價，不下單
   - 建議先觀察一段時間再啟用實際下單

---

## 故障排除

### 問題 1: 下單失敗

**錯誤：** `Order placement failed`

**解決方案：**
1. 檢查 API credentials 是否正確
2. 確認 API 是否啟用了 Trade 權限
3. 檢查訂單參數是否正確（價格、數量）
4. 確認賬戶餘額是否充足

### 問題 2: 記錄文件未創建

**解決方案：**
1. 檢查 `logs/trading/` 目錄是否存在
2. 確認寫入權限
3. 檢查磁盤空間

---

## 下一步

1. ✅ 啟用記錄功能（自動）
2. ⏳ 運行策略並收集數據
3. ⏳ 分析記錄的數據
4. ⏳ 調整參數優化策略
5. ⏳ 啟用實際下單（可選）

---

*最後更新: 2025-12-13*

