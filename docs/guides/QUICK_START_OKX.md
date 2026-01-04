# OKX 模擬交易快速開始

## ✅ 連接測試成功！

你的 OKX Demo Trading API 連接正常，可以開始模擬交易了。

---

## 🚀 啟動模擬交易

### 啟動優化後的策略

```bash
python src/scripts/live_trading_optimized.py
```

### 運行時會看到

```
============================================================
HFT Trading Bot (Optimized Strategy)
============================================================
Symbol: BTC-USDT-SWAP
Sandbox Mode: True
API Key: 588d1a72...
============================================================

📡 Connecting to OKX Public WebSocket...
   Symbol: BTC-USDT-SWAP
   Sandbox: True
✅ Subscribed to BTC-USDT-SWAP order book (5 levels)

🔐 Connecting to OKX Private WebSocket...
✅ Login successful!
✅ Subscribed to orders and positions

🚀 Starting Optimized Trading Strategy...
   Strategy: Aggressive Market Making (Optimized)
   Optimizations: Quadratic Penalty, Anti-Sniffing, Exponential MLOFI
   Parameters: gamma=0.05, k=1.5, max_pos=10.0

[14:30:15] Mid: 89356.2 | Bid: 89355.1 | Ask: 89357.3 | Pos: 0.0000 | MLOFI: +0.123 | Vol: 12.34
[14:30:16] Mid: 89357.1 | Bid: 89356.0 | Ask: 89358.2 | Pos: 0.0000 | MLOFI: +0.145 | Vol: 12.35
...
```

---

## 📊 實時監控指標

策略運行時會顯示：

- **Mid**: 中間價
- **Bid**: 買入價（策略報價）
- **Ask**: 賣出價（策略報價）
- **Pos**: 當前持倉
- **MLOFI**: 多層級訂單流不平衡信號
- **Vol**: 波動率

---

## ⏹️ 停止策略

按 `Ctrl+C` 安全停止策略

---

## ⚙️ 調整策略參數

如果需要調整策略參數，編輯 `src/scripts/live_trading_optimized.py`：

```python
# Strategy parameters
self.gamma_base = 0.05      # 風險厭惡係數（越低越積極）
self.k_base = 1.5           # 價差參數（越低價差越緊）
self.max_position = 10.0     # 最大持倉
self.order_qty = 0.01       # 訂單數量

# Alpha weights
self.micro_weight = 0.2     # Micro price 權重
self.mlofi_weight = 0.8     # MLOFI 權重

# Optimization flags
self.use_quadratic_penalty = True      # 二次庫存懲罰
self.use_anti_sniffing = True          # 反嗅探邏輯
self.use_exponential_decay_mlofi = True  # 指數衰減 MLOFI
```

---

## 🔍 當前狀態

- ✅ API 連接正常
- ✅ Sandbox 模式已啟用（模擬交易，不使用真實資金）
- ✅ 策略已優化（包含所有最新優化）

---

## 📝 注意事項

1. **Demo Trading**: 當前使用模擬交易模式，不會使用真實資金
2. **實盤風險**: 不要將 `SANDBOX=false` 設置為 false，除非你完全理解風險
3. **監控**: 建議先運行一段時間觀察策略表現
4. **參數調整**: 根據表現調整參數，但不要過度優化

---

## 🎯 下一步

1. ✅ 測試連接 - 完成
2. ⏳ 啟動模擬交易 - 運行 `python src/scripts/live_trading_optimized.py`
3. ⏳ 監控策略表現
4. ⏳ 分析交易結果
5. ⏳ 調整參數優化

---

*準備好了嗎？運行上面的命令開始模擬交易！*

