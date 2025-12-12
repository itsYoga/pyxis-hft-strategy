# 目錄重組說明 (Directory Refactoring)

## 重組日期
2025-12-07

## 重組目標
將 `src/` 目錄從扁平結構重組為模組化結構，提升代碼可維護性和清晰度。

## 新的目錄結構

```
src/
├── __init__.py              # 主模組初始化
├── strategies/              # 策略實現
│   ├── __init__.py
│   ├── aggressive.py        # 積極做市策略 (原 strategy.py)
│   └── baseline.py          # 基準策略 (原 strategy_baseline.py)
│
├── core/                    # 核心功能
│   ├── __init__.py
│   ├── backtest.py          # 回測執行器
│   ├── data_loader.py       # 數據載入器
│   └── config_loader.py     # 配置載入器
│
├── utils/                    # 工具類
│   ├── __init__.py
│   ├── logger.py            # 日誌系統
│   ├── visualization.py     # 視覺化工具
│   ├── result_viewer.py     # 結果展示器
│   └── reconciliation.py    # 對賬工具
│
├── scripts/                 # 可執行腳本
│   ├── __init__.py
│   ├── recorder.py         # 數據錄製器
│   ├── normalize.py        # 數據正規化
│   ├── generate_dummy.py   # 生成測試數據
│   └── live_trading.py     # 即時交易
│
├── learning/                # 線上學習
│   ├── __init__.py
│   ├── online_learning.py  # River 線上學習
│   └── ab_testing.py       # A/B 測試框架
│
└── tests/                   # 測試文件
    ├── __init__.py
    ├── compare_strategies.py # 策略對比測試
    ├── run_tests.py         # 測試運行器
    ├── test_manager.py      # 測試管理器
    ├── test_pnl_fix.py      # PnL 測試
    └── test_result_viewer.py # 結果展示器測試
```

## 文件移動對照表

| 原路徑 | 新路徑 |
|--------|--------|
| `src/strategy.py` | `src/strategies/aggressive.py` |
| `src/strategy_baseline.py` | `src/strategies/baseline.py` |
| `src/backtest.py` | `src/core/backtest.py` |
| `src/data_loader.py` | `src/core/data_loader.py` |
| `src/config_loader.py` | `src/core/config_loader.py` |
| `src/logger.py` | `src/utils/logger.py` |
| `src/visualization.py` | `src/utils/visualization.py` |
| `src/result_viewer.py` | `src/utils/result_viewer.py` |
| `src/reconciliation.py` | `src/utils/reconciliation.py` |
| `src/recorder.py` | `src/scripts/recorder.py` |
| `src/normalize.py` | `src/scripts/normalize.py` |
| `src/generate_dummy.py` | `src/scripts/generate_dummy.py` |
| `src/live_trading.py` | `src/scripts/live_trading.py` |
| `src/online_learning.py` | `src/learning/online_learning.py` |
| `src/ab_testing.py` | `src/learning/ab_testing.py` |
| `src/compare_strategies.py` | `src/tests/compare_strategies.py` |
| `src/run_tests.py` | `src/tests/run_tests.py` |
| `src/test_manager.py` | `src/tests/test_manager.py` |
| `src/test_pnl_fix.py` | `src/tests/test_pnl_fix.py` |
| `src/test_result_viewer.py` | `src/tests/test_result_viewer.py` |
| `src/dummy_data.npy` | `data/dummy_data.npy` |
| `src/dummy_snapshot.npz` | `data/dummy_snapshot.npz` |

## 導入路徑更新

### 策略導入
```python
# 舊方式
from strategy import market_making_algo
from strategy_baseline import market_making_algo

# 新方式
from strategies.aggressive import market_making_algo
from strategies.baseline import market_making_algo

# 或使用包導入
from strategies import aggressive_mm, baseline_mm
```

### 核心模組導入
```python
# 舊方式
from backtest import run_backtest
from data_loader import create_asset
from config_loader import load_config

# 新方式
from core.backtest import run_backtest
from core.data_loader import create_asset
from core.config_loader import load_config

# 或使用包導入
from core import run_backtest, create_asset, load_config
```

### 工具類導入
```python
# 舊方式
from logger import setup_logger
from result_viewer import ResultViewer

# 新方式
from utils.logger import setup_logger
from utils.result_viewer import ResultViewer

# 或使用包導入
from utils import setup_logger, ResultViewer
```

### 測試文件導入
測試文件中的導入已更新為相對路徑或絕對路徑：
```python
# 在 tests/ 目錄中的文件
from ..core.backtest import run_backtest
from ..utils.logger import get_logger
from ..strategies.aggressive import market_making_algo
```

## 執行腳本更新

### 回測執行
```bash
# 舊方式
python src/backtest.py data/binance_usdm/btcusdt_20240808.npz

# 新方式（路徑不變，但內部導入已更新）
python src/core/backtest.py data/binance_usdm/btcusdt_20240808.npz

# 或使用模組方式
python -m src.core.backtest data/binance_usdm/btcusdt_20240808.npz
```

### 策略對比
```bash
# 舊方式
python src/compare_strategies.py

# 新方式
python src/tests/compare_strategies.py
```

### 數據生成
```bash
# 舊方式
python src/generate_dummy.py

# 新方式
python src/scripts/generate_dummy.py
```

## 數據文件位置

測試數據文件已移動到項目根目錄的 `data/` 目錄：
- `src/dummy_data.npy` → `data/dummy_data.npy`
- `src/dummy_snapshot.npz` → `data/dummy_snapshot.npz`

所有引用這些文件的路徑已更新。

## 向後兼容性

為了保持向後兼容，所有模組都支持兩種導入方式：
1. **相對導入**：當作為包使用時
2. **絕對導入**：當直接執行腳本時

這確保了現有的執行方式仍然可以工作。

## 注意事項

1. **虛擬環境**：確保在虛擬環境中運行，所有依賴已安裝
2. **路徑更新**：如果直接執行腳本，可能需要更新工作目錄
3. **文檔更新**：部分文檔中的路徑引用可能需要手動更新

## 測試驗證

重組後已驗證以下導入：
- ✅ `from strategies.aggressive import market_making_algo`
- ✅ `from core.data_loader import create_asset`
- ✅ `from core.backtest import run_backtest`
- ✅ `from utils.logger import setup_logger`

## 未來改進

1. 考慮將 `scripts/` 目錄中的腳本改為可執行的 CLI 工具
2. 添加更多單元測試
3. 考慮將配置相關功能進一步模組化

