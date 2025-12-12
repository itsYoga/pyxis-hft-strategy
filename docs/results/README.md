# 測試結果目錄

此目錄包含所有測試結果和報告。

## 📁 文件說明

### 自動生成的文件

- **`test_results.json`** - 測試結果數據庫（自動生成）
  - 包含所有測試記錄
  - JSON 格式，易於程序讀取
  - 每次運行 `test_manager.py` 會自動更新

- **`test_report.md`** - 測試報告（自動生成）
  - 使用 `python3 test_manager.py --report` 生成
  - 包含測試歷史和策略對比

### 手動維護的文件

- **`TEST_RESULTS.md`** - 測試結果文檔
  - 功能測試結果記錄
  - 手動更新

- **`完成總結.md`** - 完成總結
  - 項目完成情況總結
  - 已合併到專案分析報告

---

## 🚀 使用測試結果管理系統

### 記錄測試結果

```bash
cd src
python3 test_manager.py \
    --data ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --strategy aggressive_mm \
    --notes "測試說明"
```

### 查看歷史記錄

結果會自動保存到 `test_results.json`，可以使用 Python 讀取：

```python
from test_manager import TestResultManager

manager = TestResultManager()
history = manager.get_history("aggressive_mm", limit=10)
```

### 比較策略

```bash
python3 test_manager.py --compare baseline aggressive_mm
```

### 生成報告

```bash
python3 test_manager.py --report
```

詳細說明請參考 [測試結果管理系統使用指南](../guides/TEST_RESULT_MANAGEMENT.md)。

---

## 📊 結果格式

每個測試記錄包含：

```json
{
  "timestamp": "2025-12-13T04:50:45",
  "strategy_name": "aggressive_mm",
  "config_file": "../config/strategy_aggressive.yaml",
  "data_file": "../data/binance_usdm/btcusdt_20240808.npz",
  "snapshot_file": "../data/binance_usdm/btcusdt_20240808_eod.npz",
  "result": {
    "balance": 556098.90,
    "position": -9.0,
    "equity": 1161.15,
    "pnl": 1161.15,
    "pnl_pct": 0.0,
    "elapsed_time": 2.05
  },
  "notes": "測試說明"
}
```

---

## 💡 最佳實踐

1. **每次重要更新後記錄結果**
2. **使用清晰的策略名稱**
3. **在 notes 中記錄重要變更**
4. **定期生成報告進行比較**
5. **將 test_results.json 加入版本控制**

---

**最後更新**: 2025-12-13

