# 測試結果管理系統使用指南

## 概述

測試結果管理系統 (`test_manager.py`) 提供了一個系統化的方式來：
- 記錄每次測試的結果
- 比較不同策略版本的性能
- 生成測試報告
- 追蹤策略改進歷史

---

## 快速開始

### 1. 運行測試並自動記錄

```bash
cd src
python3 test_manager.py \
    --data ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --strategy aggressive_mm \
    --notes "測試新參數配置"
```

### 2. 比較兩個策略

```bash
python3 test_manager.py \
    --compare baseline aggressive_mm
```

### 3. 生成測試報告

```bash
python3 test_manager.py --report
```

---

## 詳細使用

### 記錄測試結果

#### 基本用法

```python
from test_manager import run_test_with_recording

# 運行測試並自動記錄
result = run_test_with_recording(
    data_file="../data/binance_usdm/btcusdt_20240808.npz",
    snapshot_file="../data/binance_usdm/btcusdt_20240808_eod.npz",
    strategy_name="aggressive_mm",
    notes="測試 gamma_base=0.03"
)
```

#### 使用自定義配置

```python
result = run_test_with_recording(
    data_file="../data/binance_usdm/btcusdt_20240808.npz",
    snapshot_file="../data/binance_usdm/btcusdt_20240808_eod.npz",
    config_file="../config/strategy_aggressive.yaml",
    strategy_name="aggressive_mm_v2",
    notes="使用新配置參數"
)
```

---

### 比較策略

#### 在 Python 中使用

```python
from test_manager import TestResultManager

manager = TestResultManager()

# 比較兩個策略
comparison = manager.compare_strategies(
    strategy1_name="baseline",
    strategy2_name="aggressive_mm"
)

print(f"Baseline PnL: {comparison['strategy1']['pnl']:.2f}")
print(f"Aggressive PnL: {comparison['strategy2']['pnl']:.2f}")
print(f"改進: {comparison['difference']['improvement_pct']:.2f}%")
print(f"勝者: {comparison['difference']['winner']}")
```

#### 命令行比較

```bash
python3 test_manager.py \
    --compare baseline aggressive_mm
```

---

### 查看歷史記錄

```python
from test_manager import TestResultManager

manager = TestResultManager()

# 獲取所有歷史記錄
all_results = manager.get_history()

# 獲取特定策略的歷史記錄
aggressive_results = manager.get_history(strategy_name="aggressive_mm", limit=10)

# 獲取最新結果
latest = manager.get_latest("aggressive_mm")
```

---

### 生成報告

#### 自動生成報告

```python
from test_manager import TestResultManager

manager = TestResultManager()

# 生成報告並保存到文件
report = manager.generate_report("../docs/results/test_report.md")

# 或只獲取報告內容
report_content = manager.generate_report()
print(report_content)
```

#### 命令行生成報告

```bash
python3 test_manager.py --report
```

報告會包含：
- 所有策略的測試歷史
- 策略對比結果
- 改進統計

---

## 結果文件結構

測試結果保存在 `docs/results/test_results.json`：

```json
[
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
    "notes": "測試新參數"
  }
]
```

---

## 工作流程示例

### 場景 1: 測試新參數配置

```bash
# 1. 修改配置文件
vim config/strategy_aggressive.yaml
# 修改 gamma_base: 0.03

# 2. 運行測試並記錄
python3 test_manager.py \
    --data ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --strategy aggressive_mm_v2 \
    --notes "gamma_base=0.03"

# 3. 比較結果
python3 test_manager.py \
    --compare aggressive_mm aggressive_mm_v2

# 4. 生成報告
python3 test_manager.py --report
```

### 場景 2: 批量測試多個數據集

```bash
#!/bin/bash
# test_multiple_datasets.sh

datasets=(
    "../data/binance_usdm/btcusdt_20240808.npz"
    "../data/binance_usdm/btcusdt_20240809.npz"
)

for data in "${datasets[@]}"; do
    snapshot="${data%.npz}_eod.npz"
    python3 test_manager.py \
        --data "$data" \
        --snapshot "$snapshot" \
        --strategy aggressive_mm \
        --notes "批量測試"
done

# 生成報告
python3 test_manager.py --report
```

### 場景 3: 策略版本追蹤

```bash
# 版本 1
python3 test_manager.py \
    --data ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --strategy aggressive_mm_v1 \
    --notes "初始版本"

# 修改策略後，版本 2
python3 test_manager.py \
    --data ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --strategy aggressive_mm_v2 \
    --notes "優化參數"

# 比較版本
python3 test_manager.py \
    --compare aggressive_mm_v1 aggressive_mm_v2
```

---

## 最佳實踐

### 1. 命名策略

使用清晰的策略名稱：
- ✅ `aggressive_mm_v1`
- ✅ `baseline_gamma_0.05`
- ✅ `mlofi_5levels`
- ❌ `test1`, `new_strategy`

### 2. 添加備註

在 `--notes` 中記錄重要信息：
- 參數變更
- 配置文件名
- 測試目的

### 3. 定期生成報告

每次重要更新後生成報告：
```bash
python3 test_manager.py --report > ../docs/results/latest_report.md
```

### 4. 版本控制

將 `docs/results/test_results.json` 加入版本控制：
```bash
git add docs/results/test_results.json
git commit -m "Add test results for aggressive_mm_v2"
```

---

## 報告格式

生成的報告包含：

### 測試歷史

| 時間 | 數據集 | PnL | PnL % | Equity | 執行時間 |
|------|--------|-----|-------|--------|----------|
| 2025-12-13 04:50:45 | btcusdt_20240808 | +1161.15 | +0.00% | 1161.15 | 2.05s |

### 策略對比

```
### aggressive_mm vs baseline
- aggressive_mm: PnL = +1161.15
- baseline: PnL = +1120.95
- 差異: +40.20
- 改進: +3.58%
- 勝者: aggressive_mm
```

---

## 故障排除

### 問題: 結果未保存

**檢查**:
1. `docs/results/` 目錄是否存在
2. 文件權限是否正確
3. 查看日誌: `logs/backtest.log`

### 問題: 比較結果為空

**原因**: 沒有找到足夠的測試結果

**解決**:
1. 確保兩個策略都有測試記錄
2. 檢查策略名稱是否正確
3. 確認數據文件路徑一致

### 問題: 報告生成失敗

**檢查**:
1. JSON 文件格式是否正確
2. 文件編碼是否為 UTF-8
3. 查看錯誤日誌

---

## 相關文檔

- [如何運行策略](./HOW_TO_RUN.md)
- [配置參數優化指南](./CONFIGURATION_GUIDE.md)
- [快速參考指南](./QUICK_REFERENCE.md)

---

**最後更新**: 2025-12-13

