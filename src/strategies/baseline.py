from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT, BUY, SELL

@njit
def market_making_algo(hbt, stat):
    """
    BASELINE Market Making Strategy (Original)
    Only uses Level 1 data: Micro Price + BBO Imbalance
    
    For comparison with aggressive strategy.
    """
    asset_no = 0
    tick_size = hbt.depth(asset_no).tick_size
    
    # Original Parameters
    gamma = 0.1
    k = 1.5
    alpha_weight = 0.3
    imbalance_weight = 0.5
    window_size = 1000
    
    order_qty = 1.0
    max_position = 10.0
    
    # State Variables
    mid_price_buffer = np.zeros(window_size, dtype=np.float64)
    buffer_idx = 0
    is_buffer_full = False
    step_count = 0
    
    # Safety limit: prevent infinite loops
    max_steps = 1_000_000
    consecutive_empty_depth = 0
    max_empty_depth = 100  # If depth is empty for 100 consecutive steps, exit
    
    while step_count < max_steps:
        ret = hbt.elapse(100_000_000)
        if ret != 0:
            # Data ended (ret == 1) or error occurred
            break
        
        step_count += 1
        hbt.clear_inactive_orders(asset_no)
        
        depth = hbt.depth(asset_no)
        if depth.best_bid == 0 or depth.best_ask == 0:
            consecutive_empty_depth += 1
            if consecutive_empty_depth >= max_empty_depth:
                # Data likely ended, exit loop
                break
            continue
        else:
            consecutive_empty_depth = 0  # Reset counter when depth is valid
        if np.isnan(depth.best_bid) or np.isnan(depth.best_ask):
            continue
        
        best_bid = depth.best_bid
        best_ask = depth.best_ask
        best_bid_qty = depth.best_bid_qty
        best_ask_qty = depth.best_ask_qty
        
        mid_price = (best_bid + best_ask) / 2.0
        
        # Alpha 1: Micro Price (Level 1 only)
        if best_bid_qty + best_ask_qty > 0:
            micro_price = (
                best_bid * best_ask_qty + best_ask * best_bid_qty
            ) / (best_bid_qty + best_ask_qty)
        else:
            micro_price = mid_price
        
        alpha_micro = (micro_price - mid_price) / tick_size
        
        # Alpha 2: BBO Imbalance (Level 1 only)
        if best_bid_qty + best_ask_qty > 0:
            bbo_imbalance = (
                best_bid_qty - best_ask_qty
            ) / (best_bid_qty + best_ask_qty)
        else:
            bbo_imbalance = 0.0
        
        # Combined forecast (simple)
        forecast = alpha_weight * alpha_micro + imbalance_weight * bbo_imbalance
        
        # Volatility
        mid_price_buffer[buffer_idx] = mid_price
        buffer_idx += 1
        if buffer_idx >= window_size:
            buffer_idx = 0
            is_buffer_full = True
        
        if is_buffer_full:
            mean_price = np.sum(mid_price_buffer) / window_size
            variance = np.sum((mid_price_buffer - mean_price) ** 2) / window_size
            volatility = np.sqrt(variance)
            if volatility == 0:
                volatility = tick_size
        else:
            volatility = tick_size * 10
        
        # Reservation Price (standard AS)
        position = hbt.position(asset_no)
        reservation_price = mid_price + forecast * tick_size - position * gamma * (volatility ** 2)
        
        # Fixed Spread
        half_spread = (2.0 / gamma) * np.log(1.0 + gamma / k) / 2.0
        skew = 0.2 * position / max_position if max_position > 0 else 0.0
        
        bid_price = reservation_price - half_spread * (1 + skew)
        ask_price = reservation_price + half_spread * (1 - skew)
        
        bid_price_tick = round(bid_price / tick_size) * tick_size
        ask_price_tick = round(ask_price / tick_size) * tick_size
        
        if bid_price_tick >= ask_price_tick:
            bid_price_tick = mid_price - tick_size
            ask_price_tick = mid_price + tick_size
        
        bid_price_tick = min(bid_price_tick, best_bid)
        ask_price_tick = max(ask_price_tick, best_ask)
        
        # Order Management
        if stat[0] > 0:
            hbt.cancel(asset_no, int(stat[0]), False)
        if stat[2] > 0:
            hbt.cancel(asset_no, int(stat[2]), False)
        
        new_bid_id = int(stat[0]) + 1 if stat[0] > 0 else 1
        new_ask_id = int(stat[2]) + 1 if stat[2] > 0 else 2
        
        if new_bid_id == new_ask_id:
            new_ask_id += 1
        
        can_buy = position < max_position
        can_sell = position > -max_position
        
        if can_buy:
            hbt.submit_buy_order(asset_no, new_bid_id, bid_price_tick, order_qty, GTX, LIMIT, False)
        if can_sell:
            hbt.submit_sell_order(asset_no, new_ask_id, ask_price_tick, order_qty, GTX, LIMIT, False)
        
        stat[0] = new_bid_id
        stat[1] = bid_price_tick
        stat[2] = new_ask_id
        stat[3] = ask_price_tick
        stat[4] = step_count
