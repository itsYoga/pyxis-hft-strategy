# 快速測試指南

## 🚀 立即開始測試

### 步驟 1: 安裝依賴

```bash
pip install -r requirements.txt
```

### 步驟 2: 運行自動測試

```bash
./scripts/run_all_tests.sh
```

---

## 📋 手動測試步驟

### 1. 測試策略對比（最重要）

```bash
python src/tests/compare_strategies.py
```

**預期：** 顯示 Baseline vs Optimized 對比，Optimized 應該表現更好

---

### 2. 測試 OKX 連接

```bash
python src/scripts/live_trading_optimized.py --test
```

**預期：** ✅ Connection test successful!

---

### 3. 運行策略（觀察模式）

```bash
python src/scripts/live_trading_optimized.py
```

**運行 10-30 秒後按 Ctrl+C**

**檢查：**
- ✅ 顯示實時報價
- ✅ 創建日誌文件在 `logs/trading/`

---

### 4. 啟動儀表板

```bash
# 終端 1: 運行策略（生成數據）
python src/scripts/live_trading_optimized.py

# 終端 2: 啟動儀表板
streamlit run src/utils/streamlit_dashboard.py
```

**訪問：** http://localhost:8501

---

## ✅ 測試檢查清單

- [ ] 依賴安裝成功
- [ ] 策略對比測試通過
- [ ] OKX 連接成功
- [ ] 策略運行正常
- [ ] 數據記錄正常
- [ ] 儀表板顯示正常

---

## 🎯 推薦測試順序

1. **快速驗證（5分鐘）**
   ```bash
   ./scripts/run_all_tests.sh
   python src/tests/compare_strategies.py
   python src/scripts/live_trading_optimized.py --test
   ```

2. **完整測試（15分鐘）**
   - 運行策略 30 秒
   - 啟動儀表板
   - 檢查記錄的數據

3. **雲端部署前測試**
   - 所有上述測試
   - 測試實際下單（Demo Trading）

---

*最後更新: 2025-12-13*
