#!/bin/bash
# 測試策略優化效果
# 比較 Baseline 和優化後的 Aggressive 策略

echo "=========================================="
echo "策略優化效果測試"
echo "=========================================="
echo ""

# 檢查數據文件
DATA_FILE="data/binance_usdm/btcusdt_20240808.npz"
SNAPSHOT_FILE="data/binance_usdm/btcusdt_20240808_eod.npz"

if [ ! -f "$DATA_FILE" ]; then
    echo "錯誤: 找不到數據文件 $DATA_FILE"
    exit 1
fi

if [ ! -f "$SNAPSHOT_FILE" ]; then
    echo "錯誤: 找不到快照文件 $SNAPSHOT_FILE"
    exit 1
fi

echo "使用數據: $DATA_FILE"
echo "快照文件: $SNAPSHOT_FILE"
echo ""

# 運行對比測試
echo "運行策略對比測試..."
echo ""

python src/tests/compare_strategies.py

echo ""
echo "=========================================="
echo "測試完成！"
echo "=========================================="
echo ""
echo "提示："
echo "- 如果 Aggressive PnL > Baseline PnL，優化有效"
echo "- 建議在多個數據集上測試以驗證一致性"
echo "- 查看 docs/guides/TESTING_OPTIMIZATIONS.md 獲取詳細分析指南"

