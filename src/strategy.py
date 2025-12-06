from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT, BUY, SELL

@njit
def market_making_algo(hbt, stat):
    """
    Market Making Strategy with Alpha Signals
    
    Alpha 信號:
    1. Micro Price - 考慮 BBO 數量的加權中間價
    2. BBO Imbalance - 最佳買賣價位的數量失衡
    
    stat array 用途:
    [0] = current bid order id
    [1] = current bid price
    [2] = current ask order id
    [3] = current ask price
    [4] = step counter
    """
    asset_no = 0
    tick_size = hbt.depth(asset_no).tick_size
    
    # ========================================
    # Strategy Parameters (可調整優化)
    # ========================================
    gamma = 0.1           # 風險厭惡係數 (越大 -> 越快平倉)
    k = 1.5               # Spread 彈性 (越大 -> Spread 越窄)
    alpha_weight = 0.3    # Alpha 信號權重
    imbalance_weight = 0.5  # Imbalance 信號權重
    window_size = 1000    # 波動率計算窗口
    
    # Order management
    order_qty = 1.0       # 每單數量
    max_position = 10.0   # 最大持倉限制
    
    # ========================================
    # State Variables
    # ========================================
    mid_price_buffer = np.zeros(window_size, dtype=np.float64)
    buffer_idx = 0
    is_buffer_full = False
    step_count = 0
    
    # ========================================
    # Main Event Loop (100ms per step)
    # ========================================
    while True:
        ret = hbt.elapse(100_000_000)  # 100ms
        if ret != 0:
            print("Elapse returned:", ret)
            break
        
        step_count += 1
        
        # 1. Clear inactive orders
        hbt.clear_inactive_orders(asset_no)
        
        # 2. Get Market Data
        depth = hbt.depth(asset_no)
        if depth.best_bid == 0 or depth.best_ask == 0:
            continue
        if np.isnan(depth.best_bid) or np.isnan(depth.best_ask):
            continue
        
        best_bid = depth.best_bid
        best_ask = depth.best_ask
        best_bid_qty = depth.best_bid_qty
        best_ask_qty = depth.best_ask_qty
        
        mid_price = (best_bid + best_ask) / 2.0
        
        # ========================================
        # 3. Calculate Alpha Signals (核心!)
        # ========================================
        
        # Alpha 1: Micro Price
        # 考慮 BBO 數量的加權價格，預測短期價格方向
        if best_bid_qty + best_ask_qty > 0:
            micro_price = (
                best_bid * best_ask_qty + best_ask * best_bid_qty
            ) / (best_bid_qty + best_ask_qty)
        else:
            micro_price = mid_price
        
        # Micro Price Alpha (以 tick 為單位)
        alpha_micro = (micro_price - mid_price) / tick_size
        
        # Alpha 2: BBO Imbalance
        # 買單量 > 賣單量 -> 正值 -> 預測上漲
        if best_bid_qty + best_ask_qty > 0:
            bbo_imbalance = (
                best_bid_qty - best_ask_qty
            ) / (best_bid_qty + best_ask_qty)
        else:
            bbo_imbalance = 0.0
        
        # 綜合 Alpha 信號
        forecast = (
            alpha_weight * alpha_micro + 
            imbalance_weight * bbo_imbalance
        )
        
        # ========================================
        # 4. Update Volatility Buffer
        # ========================================
        mid_price_buffer[buffer_idx] = mid_price
        buffer_idx += 1
        if buffer_idx >= window_size:
            buffer_idx = 0
            is_buffer_full = True
        
        # Calculate Volatility
        volatility = 0.0
        if is_buffer_full:
            mean_price = np.sum(mid_price_buffer) / window_size
            variance = np.sum((mid_price_buffer - mean_price) ** 2) / window_size
            volatility = np.sqrt(variance)
            if volatility == 0:
                volatility = tick_size
        else:
            volatility = tick_size * 10
        
        # ========================================
        # 5. Calculate Reservation Price (AS Model + Alpha)
        # ========================================
        position = hbt.position(asset_no)
        
        # 原始 AS 模型: r = s - q * gamma * sigma^2
        # 加入 Alpha:   r = s + forecast - q * gamma * sigma^2
        reservation_price = (
            mid_price 
            + forecast * tick_size              # Alpha 預測調整
            - position * gamma * (volatility ** 2)  # 庫存風險調整
        )
        
        # ========================================
        # 6. Calculate Bid/Ask Spread
        # ========================================
        # delta = (2/gamma) * ln(1 + gamma/k) / 2
        half_spread = (2.0 / gamma) * np.log(1.0 + gamma / k) / 2.0
        
        # 根據持倉調整 spread (skewing)
        # 持多倉 -> 降低 bid, 提高 ask (鼓勵賣出)
        skew = 0.2 * position / max_position if max_position > 0 else 0.0
        
        bid_price = reservation_price - half_spread * (1 + skew)
        ask_price = reservation_price + half_spread * (1 - skew)
        
        # Quantize to tick size
        bid_price_tick = round(bid_price / tick_size) * tick_size
        ask_price_tick = round(ask_price / tick_size) * tick_size
        
        # Ensure we don't cross the spread
        if bid_price_tick >= ask_price_tick:
            bid_price_tick = mid_price - tick_size
            ask_price_tick = mid_price + tick_size
        
        # Ensure prices stay within market
        bid_price_tick = min(bid_price_tick, best_bid)
        ask_price_tick = max(ask_price_tick, best_ask)
            
        # ========================================
        # 7. Order Management
        # ========================================
        
        # 取消舊訂單（如果存在）
        if stat[0] > 0:
            hbt.cancel(asset_no, int(stat[0]), False)
        if stat[2] > 0:
            hbt.cancel(asset_no, int(stat[2]), False)
        
        # 產生新訂單 ID
        new_bid_id = int(stat[0]) + 1 if stat[0] > 0 else 1
        new_ask_id = int(stat[2]) + 1 if stat[2] > 0 else 2
        
        # 確保 ID 不重複
        if new_bid_id == new_ask_id:
            new_ask_id += 1
        
        # ========================================
        # 8. 持倉限制檢查
        # ========================================
        can_buy = position < max_position
        can_sell = position > -max_position
        
        # 提交訂單
        if can_buy:
            hbt.submit_buy_order(asset_no, new_bid_id, bid_price_tick, order_qty, GTX, LIMIT, False)
        if can_sell:
            hbt.submit_sell_order(asset_no, new_ask_id, ask_price_tick, order_qty, GTX, LIMIT, False)
        
        # 更新狀態
        stat[0] = new_bid_id
        stat[1] = bid_price_tick
        stat[2] = new_ask_id
        stat[3] = ask_price_tick
        stat[4] = step_count

