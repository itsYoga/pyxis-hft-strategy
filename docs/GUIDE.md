# Pyxis HFT Strategy 完整指南

## 📋 目錄

1. [快速開始](#快速開始)
2. [運行策略](#運行策略)
3. [測試與驗證](#測試與驗證)
4. [配置說明](#配置說明)
5. [策略優化](#策略優化)
6. [實時交易](#實時交易)
7. [監控與儀表板](#監控與儀表板)
8. [常見問題](#常見問題)

---

## 快速開始

### 1. 安裝依賴

```bash
cd pyxis-hft-strategy
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 運行基本回測

```bash
# 使用真實數據
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz

# 不顯示圖表（更快）
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz --no-viz
```

### 3. 策略對比

```bash
python src/tests/compare_strategies.py
```

---

## 運行策略

### 基本命令

```bash
# 基本運行
python src/core/backtest.py <data_file> [--snapshot <snapshot_file>] [--no-viz] [--config <config_file>]

# 使用自定義配置
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz \
    --snapshot data/binance_usdm/btcusdt_20240808_eod.npz \
    --config config/strategy_aggressive.yaml
```

### 命令行選項

- `data_file`: 市場數據文件（必需）
- `--snapshot, -s`: 快照文件（可選，會自動檢測）
- `--no-viz`: 禁用視覺化（更快）
- `--save`: 保存報告到文件
- `--config, -c`: 配置文件路徑

### 數據文件格式

支持的格式：
- `.npz`: NumPy 壓縮格式（推薦）
- `.npy`: NumPy 數組格式
- `.gz`: Gzip 壓縮格式

---

## 測試與驗證

### 1. 策略對比測試

```bash
# 對比 Baseline vs Aggressive
python src/tests/compare_strategies.py

# 測試保守版本
python src/tests/test_conservative_strategy.py

# 參數掃描
python src/tests/parameter_sweep.py
```

### 2. 運行所有測試

```bash
./scripts/run_all_tests.sh
```

### 3. 測試優化效果

```bash
python src/tests/test_optimizations.py
```

---

## 配置說明

### 配置文件位置

- `config/strategy_aggressive.yaml` - 激進策略配置
- `config/strategy_aggressive_conservative.yaml` - 保守策略配置

### 主要參數

```yaml
strategy:
  parameters:
    gamma_base: 0.05      # 風險厭惡係數
    k_base: 1.5           # 價差參數
    max_position: 10.0    # 最大持倉
    order_qty: 1.0        # 訂單數量

backtest:
  tick_size: 0.1          # 最小價格變動
  lot_size: 0.001         # 最小訂單大小
  initial_capital: 30000.0 # 初始資本
```

詳細配置說明請參考 `docs/guides/CONFIGURATION_GUIDE.md`

---

## 策略優化

### 1. PnL 優化

參考 `docs/guides/OPTIMIZE_PNL.md` 了解如何優化策略 PnL。

主要方法：
- 擴大價差（減少不利選擇）
- 調整風險厭惡係數
- 更嚴格的庫存管理
- 添加止損機制

### 2. 參數掃描

```bash
python src/tests/parameter_sweep.py
```

掃描不同參數組合，找出最優參數。

### 3. 策略版本

- **Baseline**: 基礎策略（Level 1 訂單簿）
- **Aggressive**: 優化策略（多層級 OFI + 狀態檢測）
- **Conservative**: 保守版本（更寬價差，更嚴格風險管理）
- **Enhanced**: 增強版本（止損 + 市場狀態過濾）

---

## 實時交易

### OKX 模擬交易

```bash
# 啟動實時交易
python src/scripts/live_trading_optimized.py

# 查看配置
cat .env.example
```

詳細說明請參考 `docs/guides/OKX_SIMULATED_TRADING.md`

### 環境變量設置

創建 `.env` 文件：

```bash
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
OKX_SANDBOX=true  # 使用模擬環境
```

---

## 監控與儀表板

### Streamlit 儀表板

```bash
# 啟動儀表板
./scripts/start_dashboard.sh

# 或手動啟動
streamlit run src/utils/streamlit_dashboard.py
```

訪問 `http://localhost:8501` 查看實時監控。

### Flask 儀表板

```bash
python src/utils/dashboard.py
```

訪問 `http://localhost:5000` 查看監控。

詳細說明請參考 `docs/guides/DASHBOARD_AND_MONITORING.md`

---

## 常見問題

### Q: PnL 為負數怎麼辦？

A: 參考 `docs/guides/OPTIMIZE_PNL.md`，主要方法：
1. 擴大價差（增加 k_base）
2. 調整風險厭惡係數（增加 gamma_base）
3. 更嚴格的庫存管理
4. 添加止損機制

### Q: 如何測試策略改進？

A: 使用 `compare_strategies.py` 對比不同策略版本。

### Q: 如何優化參數？

A: 使用 `parameter_sweep.py` 進行參數掃描。

### Q: 實時交易如何設置？

A: 參考 `docs/guides/OKX_SIMULATED_TRADING.md` 和 `docs/guides/QUICK_START_OKX.md`

### Q: 如何查看策略性能？

A: 使用 Streamlit 或 Flask 儀表板，或查看 `logs/trading/` 目錄下的日誌文件。

---

## 相關文檔

- **策略優化路線圖**: `docs/reports/STRATEGY_OPTIMIZATION_ROADMAP.md`
- **實施計劃**: `docs/reports/IMPLEMENTATION_PLAN.md`
- **測試結果**: `docs/results/`
- **配置指南**: `docs/guides/CONFIGURATION_GUIDE.md`

---

*最後更新: 2025-12-13*

