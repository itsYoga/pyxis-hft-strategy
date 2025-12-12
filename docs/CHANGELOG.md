# 更新日誌

## 2025-12 - 優化與清理

### 已完成的改進

1. **移除策略暱稱**
   - 刪除所有 HA4/HA3 引用
   - 重命名配置檔案為 `strategy_aggressive.yaml`
   - 更新所有文檔和代碼註釋

2. **配置檔案系統**
   - 新增 YAML 配置檔案支援
   - 統一的配置載入模組 (`config_loader.py`)
   - 結構化的配置類別

3. **統一的資料載入**
   - 新增 `data_loader.py` 模組
   - 自動偵測資料格式
   - 統一的載入介面

4. **日誌系統**
   - 新增 `logger.py` 模組
   - 支援檔案和控制台輸出
   - 可配置的日誌級別

5. **結果展示工具**
   - 新增 `result_viewer.py` 模組
   - 按 tick 顯示波動率
   - 完整的結果摘要和圖表
   - 簡單易用的 API

6. **改進的回測執行器**
   - 整合新的模組
   - 更好的錯誤處理
   - 支援配置檔案

### 新增檔案

- `config/strategy_aggressive.yaml` - 策略配置檔案
- `src/config_loader.py` - 配置載入模組
- `src/data_loader.py` - 統一資料載入模組
- `src/logger.py` - 日誌系統
- `src/result_viewer.py` - 結果展示工具
- `src/test_result_viewer.py` - 測試腳本
- `README_OPTIMIZATION.md` - 優化說明文檔

### 更新的檔案

- `src/strategy.py` - 移除 HA4 引用
- `src/backtest.py` - 整合新模組和結果展示
- `src/compare_strategies.py` - 使用新模組
- `README.md` / `README_EN.md` - 更新文檔
- `requirements.txt` - 新增 pyyaml

### 使用方式

```bash
# 基本回測
cd src
python backtest.py ../data/binance_usdm/btcusdt_20240808.npz

# 測試結果展示工具
python test_result_viewer.py
```

