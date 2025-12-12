# 文檔索引

本文檔目錄包含專案的所有文檔和指南。

## 📚 文檔結構

```
docs/
├── README.md                    # 本文檔索引
├── CHANGELOG.md                 # 更新日誌
├── HFT_策略筆記_HackMD.md       # 策略開發筆記
│
├── guides/                      # 使用指南
│   ├── HOW_TO_RUN.md           # ⭐ 如何運行策略
│   ├── CONFIGURATION_GUIDE.md   # ⭐ 配置參數優化指南
│   ├── QUICK_REFERENCE.md       # ⭐ 快速參考指南
│   ├── Recorder使用說明.md      # Recorder 使用指南
│   ├── 結果展示使用指南.md      # 結果展示工具說明
│   └── TEST_RESULT_MANAGEMENT.md # ⭐ 測試結果管理系統
│
├── reports/                     # 分析報告
│   ├── 專案分析與改進報告.md    # 完整專案分析
│   └── strategy_comparison_report.md # 策略對比報告
│
├── results/                     # 測試結果
│   ├── test_results.json        # 測試結果數據（自動生成）
│   ├── test_report.md           # 測試報告（自動生成）
│   └── TEST_RESULTS.md          # 測試結果文檔
│
└── hftbacktest-docs/            # hftbacktest 官方文檔
```

---

## 🚀 快速開始

### 新用戶必讀

1. **[如何運行策略](./guides/HOW_TO_RUN.md)** - 從安裝到運行
2. **[快速參考指南](./guides/QUICK_REFERENCE.md)** - 常用命令和參數
3. **[測試結果管理系統](./guides/TEST_RESULT_MANAGEMENT.md)** - 如何記錄和比較測試結果

### 優化策略

1. **[配置參數優化指南](./guides/CONFIGURATION_GUIDE.md)** - 參數調整詳解
2. **[策略對比報告](./reports/strategy_comparison_report.md)** - 性能對比

---

## 📋 文檔列表

### ⭐ 必讀文檔

| 文檔 | 描述 | 位置 |
|------|------|------|
| [如何運行策略](./guides/HOW_TO_RUN.md) | 完整運行指南 | guides/ |
| [配置參數優化指南](./guides/CONFIGURATION_GUIDE.md) | 參數調整指南 | guides/ |
| [快速參考指南](./guides/QUICK_REFERENCE.md) | 快速命令參考 | guides/ |
| [測試結果管理系統](./guides/TEST_RESULT_MANAGEMENT.md) | 測試結果管理 | guides/ |

### 使用指南

| 文檔 | 描述 | 位置 |
|------|------|------|
| [Recorder 使用說明](./guides/Recorder使用說明.md) | Recorder 數據收集 | guides/ |
| [結果展示使用指南](./guides/結果展示使用指南.md) | 結果展示工具 | guides/ |

### 分析報告

| 文檔 | 描述 | 位置 |
|------|------|------|
| [專案分析與改進報告](./reports/專案分析與改進報告.md) | 完整專案分析 | reports/ |
| [策略對比報告](./reports/strategy_comparison_report.md) | 策略性能對比 | reports/ |

### 其他文檔

| 文檔 | 描述 | 位置 |
|------|------|------|
| [HFT 策略筆記](./HFT_策略筆記_HackMD.md) | 策略開發筆記 | docs/ |
| [測試結果](./results/TEST_RESULTS.md) | 功能測試結果 | results/ |
| [更新日誌](./CHANGELOG.md) | 專案更新記錄 | docs/ |

---

## 🔍 快速查找

### 我想了解...

- **如何開始使用** → [如何運行策略](./guides/HOW_TO_RUN.md) ⭐
- **如何調整參數** → [配置參數優化指南](./guides/CONFIGURATION_GUIDE.md) ⭐
- **快速命令參考** → [快速參考指南](./guides/QUICK_REFERENCE.md) ⭐
- **如何管理測試結果** → [測試結果管理系統](./guides/TEST_RESULT_MANAGEMENT.md) ⭐
- **如何使用結果展示工具** → [結果展示使用指南](./guides/結果展示使用指南.md)
- **策略理論和筆記** → [HFT 策略筆記](./HFT_策略筆記_HackMD.md)
- **策略性能對比** → [策略對比報告](./reports/strategy_comparison_report.md)
- **專案結構和優化建議** → [專案分析與改進報告](./reports/專案分析與改進報告.md)

---

## 📊 測試結果管理

### 記錄測試結果

```bash
cd src
python3 test_manager.py \
    --data ../data/binance_usdm/btcusdt_20240808.npz \
    --snapshot ../data/binance_usdm/btcusdt_20240808_eod.npz \
    --strategy aggressive_mm \
    --notes "測試新參數"
```

### 比較策略

```bash
python3 test_manager.py --compare baseline aggressive_mm
```

### 生成報告

```bash
python3 test_manager.py --report
```

詳細說明請參考 [測試結果管理系統](./guides/TEST_RESULT_MANAGEMENT.md)。

---

## 📝 文檔維護

### 文檔更新記錄

- 2025-12-13: 重新組織文檔結構，創建測試結果管理系統
- 2025-12-13: 創建配置參數優化指南
- 2025-12-13: 修復 PnL 計算錯誤
- 2025-12-13: 實現 Recorder 數據收集

### 文檔結構說明

- **guides/**: 使用指南和教程
- **reports/**: 分析報告和對比結果
- **results/**: 測試結果數據和報告（自動生成）

---

## 💡 使用建議

1. **新用戶**: 從 [如何運行策略](./guides/HOW_TO_RUN.md) 開始
2. **優化策略**: 參考 [配置參數優化指南](./guides/CONFIGURATION_GUIDE.md)
3. **記錄結果**: 使用 [測試結果管理系統](./guides/TEST_RESULT_MANAGEMENT.md) 追蹤改進
4. **快速查找**: 使用 [快速參考指南](./guides/QUICK_REFERENCE.md)

---

**最後更新**: 2025-12-13
