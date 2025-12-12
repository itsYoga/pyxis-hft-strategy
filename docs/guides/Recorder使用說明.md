# Recorder 數據收集使用說明

## 概述

hftbacktest 的 `Recorder` 類別可以在回測過程中收集真實的歷史數據，用於準確的結果分析和波動率計算。

## 實現方式

### 1. Recorder 初始化

```python
from hftbacktest import Recorder

# 創建 Recorder（估計記錄大小）
record_size = 1_000_000  # 足夠大多數回測使用
recorder = Recorder(num_assets=1, record_size=record_size)
```

### 2. 修改策略函數

策略函數需要接受 `recorder` 參數（`recorder.recorder`，這是 `@jitclass` 實例）：

```python
from numba import njit

@njit
def market_making_algo(hbt, stat, recorder=None):
    """
    Args:
        hbt: Backtest engine
        stat: State array
        recorder: recorder.recorder from Recorder class (optional)
    """
    # 記錄初始狀態
    if recorder is not None:
        try:
            recorder.record(hbt)
        except:
            pass
    
    while True:
        ret = hbt.elapse(100_000_000)
        if ret != 0:
            break
        
        # 定期記錄（例如每 100 步）
        if recorder is not None and step_count % 100 == 0:
            try:
                recorder.record(hbt)
            except:
                pass
        
        # ... 策略邏輯 ...
```

### 3. 在回測中使用

```python
# 創建 Recorder
recorder = Recorder(num_assets=1, record_size=1_000_000)

# 運行策略，傳入 recorder.recorder
market_making_algo(hbt, stat, recorder.recorder)

# 獲取記錄的數據
records = recorder.get(asset_no=0)

# 使用數據
for record in records:
    price = record['price']
    position = record['position']
    balance = record['balance']
    fee = record['fee']
    # ... 處理數據 ...
```

## 記錄的數據字段

每個記錄包含以下字段：

- `timestamp`: 時間戳
- `price`: 中間價
- `position`: 持倉
- `balance`: 餘額
- `fee`: 累積費用
- `num_trades`: 交易次數
- `trading_volume`: 交易量
- `trading_value`: 交易價值

## 注意事項

1. **記錄頻率**: 建議每 100 步記錄一次，避免記錄過多數據
2. **記錄大小**: 預先估計需要的記錄數量，避免溢出
3. **錯誤處理**: 使用 try-except 包裹記錄調用，避免影響策略執行
4. **性能影響**: 記錄會略微影響性能，但通常可以忽略

## 當前實現狀態

✅ **已完成**:
- Recorder 初始化
- 策略函數支持 recorder 參數
- 定期記錄（每 100 步）
- 數據收集和填充 result_viewer

⚠️ **注意**:
- 記錄頻率可以調整（當前每 100 步）
- 如果記錄溢出，會回退到最終狀態

## 使用範例

```python
from hftbacktest import Recorder, HashMapMarketDepthBacktest
from strategy import market_making_algo

# 創建回測引擎
hbt = HashMapMarketDepthBacktest([asset])
stat = np.zeros(20, dtype=np.float64)

# 創建 Recorder
recorder = Recorder(num_assets=1, record_size=1_000_000)

# 運行策略
market_making_algo(hbt, stat, recorder.recorder)

# 獲取數據
records = recorder.get(asset_no=0)
print(f"收集了 {len(records)} 個數據點")
```

## 保存記錄

可以將記錄保存到文件：

```python
recorder.to_npz('backtest_records.npz')
```

## 相關文檔

- [hftbacktest Recorder 文檔](https://hftbacktest.readthedocs.io/)
- [結果展示使用指南](./結果展示使用指南.md)

