# 測試常見問題 FAQ

## ❓ 測試卡在 "Running Baseline strategy..." 怎麼辦？

### 這是正常的！

**原因：**
- 策略需要處理所有市場數據事件
- 每個事件處理時間約 0.1-1ms
- 對於 2,100 個事件的 dummy data，大約需要 1-3 秒
- 對於真實數據（100萬+事件），可能需要 10-60 秒

**如何確認程序正在運行：**
1. 檢查 CPU 使用率（應該 > 0%）
2. 等待幾秒鐘，策略會自動完成
3. 如果超過 5 分鐘沒有輸出，可能是真的卡住了

**加速測試：**
```bash
# 使用更小的數據集
python src/core/backtest.py data/dummy_data.npy --no-viz

# 或使用真實數據但較短的時段
```

---

## ❓ 如何知道測試是否成功？

### 成功標誌

1. **看到完整的對比報告**
   ```
   ============================================================
   STRATEGY COMPARISON REPORT
   ============================================================
   ```

2. **看到 PnL 數字**
   ```
   Baseline PnL:     +1,120.95
   Aggressive PnL:   +1,250.30
   ```

3. **看到 "Winner" 結論**
   ```
   Winner:           Aggressive
   ```

---

## ❓ 測試需要多長時間？

### 預估時間

| 數據類型 | 事件數 | 預計時間 |
|---------|--------|----------|
| Dummy Data | ~2,100 | 1-3 秒 |
| 1 小時真實數據 | ~100,000 | 10-30 秒 |
| 1 天真實數據 | ~1,000,000 | 1-3 分鐘 |

**提示：** 使用 `--no-viz` 選項可以加快速度（不顯示圖表）

---

## ❓ 如何中斷測試？

### 安全中斷

按 `Ctrl+C` 可以安全中斷測試

**注意：** 
- 中斷後不會顯示結果
- 可以重新運行測試

---

## ❓ 測試結果不一致怎麼辦？

### 可能原因

1. **使用了不同的數據集**
   - 確保兩次測試使用相同的數據文件

2. **配置不同**
   - 檢查配置文件是否一致

3. **隨機性**
   - 某些回測引擎可能有隨機性
   - 運行多次取平均值

### 解決方案

```bash
# 確保使用相同數據
python src/tests/compare_strategies.py

# 運行多次
for i in {1..5}; do
    echo "Run $i:"
    python src/tests/compare_strategies.py
done
```

---

## ❓ 如何測試個別優化？

### 步驟

1. **編輯策略文件** `src/strategies/aggressive.py`

2. **只啟用一個優化**：
   ```python
   use_quadratic_penalty = True   # 只啟用這個
   use_anti_sniffing = False
   use_exponential_decay_mlofi = False
   ```

3. **運行測試**

4. **記錄結果**

5. **禁用並測試下一個**

---

## ❓ 優化後 PnL 降低了怎麼辦？

### 診斷步驟

1. **測試個別優化**
   - 找出哪個優化導致問題

2. **調整參數**
   ```python
   # 降低反嗅探強度
   lambda_read = 0.2  # 從 0.3 降低
   
   # 降低二次懲罰強度
   # 修改 position_factor 計算
   ```

3. **測試不同數據集**
   - 某些優化可能在某些市場條件下不適用

4. **檢查日誌**
   ```bash
   tail -f src/logs/backtest.log
   ```

---

## ❓ 如何查看詳細的執行過程？

### 啟用詳細日誌

```bash
# 設置日誌級別為 DEBUG
export PYTHONPATH=src
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from tests.compare_strategies import main
main()
"
```

---

## ❓ 測試腳本找不到數據文件？

### 解決方案

1. **檢查數據文件是否存在**：
   ```bash
   ls data/binance_usdm/*.npz
   ls data/dummy_data.npy
   ```

2. **使用絕對路徑**：
   ```bash
   python src/tests/compare_strategies.py \
       --data /full/path/to/data.npz \
       --snapshot /full/path/to/snapshot.npz
   ```

3. **生成測試數據**：
   ```bash
   python src/scripts/generate_dummy.py
   ```

---

## ❓ 如何比較優化前後的版本？

### 方法

由於當前版本已經包含優化，要比較"優化前"版本：

1. **創建優化前的版本**：
   - 複製 `aggressive.py` 為 `aggressive_pre_opt.py`
   - 禁用所有優化：
     ```python
     use_quadratic_penalty = False
     use_anti_sniffing = False
     use_exponential_decay_mlofi = False
     ```

2. **運行對比**：
   ```python
   from strategies.aggressive_pre_opt import market_making_algo as pre_opt
   from strategies.aggressive import market_making_algo as optimized
   ```

---

## 📞 需要幫助？

如果測試遇到問題：

1. 查看日誌：`src/logs/backtest.log`
2. 檢查數據文件是否存在
3. 確認虛擬環境已激活
4. 查看 [完整測試指南](TESTING_OPTIMIZATIONS.md)

---

*最後更新: 2025-12-07*

