# 如何運行策略

本指南說明如何運行 Pyxis HFT 策略框架。

## 📋 目錄

1. [基本運行](#基本運行)
2. [使用真實數據](#使用真實數據)
3. [配置選項](#配置選項)
4. [策略對比](#策略對比)
5. [命令行選項](#命令行選項)
6. [常見問題](#常見問題)

---

## 基本運行

### 1. 準備環境

```bash
# 進入專案目錄
cd pyxis-hft-strategy

# 激活虛擬環境
source venv/bin/activate

# 確認依賴已安裝
pip install -r requirements.txt
```

### 2. 使用測試數據運行

```bash
# 生成測試數據（如果還沒有）
cd src
python3 generate_dummy.py

# 運行回測
python3 backtest.py dummy_data.npy --snapshot dummy_snapshot.npz
```

### 3. 使用真實 Binance 數據

```bash
# 從專案根目錄運行
cd src

# BTCUSDT 2024-08-08
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz

# BTCUSDT 2024-08-09
python3 backtest.py ../data/binance_usdm/btcusdt_20240809.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240809_eod.npz

# ETHUSDT（使用 .gz 格式，會自動檢測快照）
python3 backtest.py ../data/binance_usdm/ethusdt_20240808.gz
```

---

## 使用真實數據

### Binance 數據格式

專案支援多種數據格式：

1. **`.npz` 格式**（推薦）
   - 需要單獨的快照文件（`*_eod.npz`）
   - 更快的載入速度

2. **`.gz` 格式**
   - 自動檢測快照文件
   - 如果找不到，會自動生成

3. **`.npy` 格式**
   - 自定義數據格式
   - 需要手動指定快照文件

### 示例命令

```bash
# 使用 .npz 格式（需要快照）
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz

# 使用 .gz 格式（自動檢測快照）
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.gz

# 使用自定義配置
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --config ../config/strategy_aggressive.yaml
```

---

## 配置選項

### 使用自定義配置文件

```bash
python3 backtest.py <data_file> \
    --config config/strategy_aggressive.yaml
```

配置文件位置：`config/strategy_aggressive.yaml`

主要配置項：
- `strategy.parameters`: 策略參數（gamma, k, alpha weights 等）
- `strategy.regimes`: 體制特定參數
- `backtest`: 回測配置（tick_size, lot_size, latency 等）

### 修改策略參數

編輯 `config/strategy_aggressive.yaml`：

```yaml
strategy:
  parameters:
    gamma_base: 0.05          # 風險厭惡係數（越低越積極）
    k_base: 1.5               # 價差參數
    micro_weight: 0.2         # Micro price 權重
    mlofi_weight: 0.8         # MLOFI 權重
    num_levels: 5             # 訂單簿層級數
    max_position: 10.0        # 最大持倉
```

---

## 策略對比

### 運行策略對比測試

```bash
cd src
python3 compare_strategies.py
```

這會比較：
- **Baseline**：原始策略
- **Aggressive**：改進的策略（MLOFI + Regime Detection）

### 對比結果

對比報告會顯示：
- PnL 對比
- 交易次數
- 平均價差
- 最大回撤
- Sharpe Ratio

---

## 命令行選項

### 完整命令格式

```bash
python3 backtest.py <data_file> [OPTIONS]
```

### 可用選項

| 選項 | 簡寫 | 說明 |
|------|------|------|
| `--snapshot` | `-s` | 指定快照文件（.npz 格式需要） |
| `--no-viz` | - | 禁用視覺化（不顯示圖表） |
| `--save` | - | 保存報告到文件 |
| `--config` | `-c` | 指定配置文件路徑 |

### 示例

```bash
# 基本運行（顯示圖表）
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz

# 不顯示圖表（更快）
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --no-viz

# 保存報告
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --save

# 使用自定義配置
python3 backtest.py ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --config ../config/strategy_aggressive.yaml
```

---

## 輸出說明

### 控制台輸出

回測運行時會顯示：

1. **初始狀態**
   ```
   Initial State:
      Balance: 0.00
      Position: 0.0000
      Mid Price: 10,000.00
      Equity: 0.00
   ```

2. **最終狀態**
   ```
   Final State:
      Balance: 1,120.95 (change: +1,120.95)
      Position: 0.0000 (change: +0.0000)
      Fee: 15.20 (accumulated: +15.20)
      Equity: 1,105.75 (change: +1,105.75)
   ```

3. **回測結果摘要**
   ```
   BACKTEST RESULTS
   ==================================================
   Execution Time: 45.23 seconds
   Capital:
      Balance:                 1,120.95
      Position:              0.0000
      Mid Price:          10,000.00
      Equity (net):         1,105.75
      PnL:                +1,105.75 (+110.58%)
   ```

### 圖表輸出

如果啟用視覺化（默認），會顯示：

1. **權益曲線**：顯示權益隨時間變化
2. **持倉變化**：顯示持倉隨時間變化
3. **按 Tick 波動率**：顯示市場波動率

### 日誌文件

日誌保存在 `logs/backtest.log`，包含詳細的執行信息。

---

## 常見問題

### Q1: 找不到數據文件

**錯誤**：`FileNotFoundError: [Errno 2] No such file or directory`

**解決**：
- 確認數據文件路徑正確
- 使用相對路徑時，確認當前目錄正確
- 檢查數據文件是否存在

### Q2: 策略運行時間過長

**原因**：
- 數據量太大
- 策略邏輯複雜

**解決**：
- 使用 `--no-viz` 禁用視覺化
- 減少數據時間範圍
- 檢查是否有無限循環（已修復）

### Q3: 沒有交易產生

**可能原因**：
- 數據質量問題
- 策略參數設置過於保守
- 市場深度不足

**檢查**：
- 查看日誌中的市場深度信息
- 調整 `gamma_base` 參數（降低值 = 更積極）
- 檢查數據是否包含有效的訂單簿更新

### Q4: PnL 為 0

**正常情況**：
- 初始資本為 0（從零開始）
- 沒有產生交易
- 數據時間範圍太短

**檢查**：
- 查看最終狀態的 Balance 和 Position
- 檢查是否有交易記錄
- 確認數據時間範圍足夠長

### Q5: 配置未生效

**檢查**：
- 確認配置文件路徑正確
- 檢查 YAML 語法是否正確
- 查看日誌中的配置載入信息

---

## 進階用法

### 在 Python 代碼中使用

```python
from backtest import run_backtest

# 運行回測
result = run_backtest(
    data_file='../data/binance_usdm/btcusdt_20240808.npz',
    snapshot_file='../data/binance_usdm/btcusdt_20240808_eod.npz',
    visualize=True,
    save_report=False,
    config_file='../config/strategy_aggressive.yaml'
)

# 獲取結果
print(f"PnL: {result['pnl']:.2f}")
print(f"Equity: {result['equity']:.2f}")
print(f"Execution Time: {result['elapsed_time']:.2f}s")
```

### 批量運行多個數據文件

```bash
#!/bin/bash
# run_multiple.sh

for file in ../data/binance_usdm/btcusdt_*.npz; do
    echo "Running: $file"
    python3 backtest.py "$file" \
        --snapshot "${file%.npz}_eod.npz" \
        --no-viz
done
```

---

## 下一步

- 查看 [策略對比報告](./strategy_comparison_report.md)
- 閱讀 [專案分析與改進報告](./專案分析與改進報告.md)
- 了解 [結果展示使用指南](./結果展示使用指南.md)
- 學習 [Recorder 使用說明](./Recorder使用說明.md)

---

## 需要幫助？

如果遇到問題：
1. 檢查日誌文件：`logs/backtest.log`
2. 查看文檔：`docs/` 目錄
3. 檢查配置：`config/strategy_aggressive.yaml`

