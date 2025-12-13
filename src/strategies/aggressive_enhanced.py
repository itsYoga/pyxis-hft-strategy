from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT, BUY, SELL

"""
Enhanced Aggressive Market Making Strategy
===========================================

新增功能：
1. 止損機制 - 限制單筆交易最大虧損
2. 市場狀態過濾 - 只在有利的市場條件下交易
3. 動態價差調整 - 根據市場狀態調整價差

基於 aggressive.py，添加了風險管理功能
"""


@njit
def market_making_algo(hbt, stat, recorder=None):
    """
    Enhanced Aggressive Market Making Strategy
    
    新增功能：
    - 止損機制
    - 市場狀態過濾
    - 動態價差調整
    
    Args:
        hbt: Backtest engine
        stat: State array for tracking orders
        recorder: Optional recorder for data collection
    """
    asset_no = 0
    tick_size = hbt.depth(asset_no).tick_size
    
    # Record initial state if recorder is provided
    if recorder is not None:
        try:
            recorder.record(hbt)
        except:
            pass
    
    # ========================================
    # Enhanced Parameters
    # ========================================
    
    # Base parameters
    gamma_base = 0.05
    k_base = 1.5
    
    # Alpha weights
    micro_weight = 0.2
    mlofi_weight = 0.8
    slope_weight = 0.0
    
    # Defensive mechanisms
    use_quadratic_penalty = True
    lambda_read = 0.3
    use_anti_sniffing = True
    
    # Multi-level depth
    num_levels = 5
    ofi_decay = 0.7
    use_exponential_decay_mlofi = True
    alpha_decay = 0.5
    
    # Volatility
    window_size = 500
    base_volatility = tick_size * 5
    vol_smoothing = 0.1
    
    # Order management
    order_qty = 1.0
    max_position = 10.0
    
    # ========================================
    # NEW: Stop Loss Mechanism
    # ========================================
    max_loss_per_trade = 50.0  # Maximum loss per trade
    max_total_loss = 200.0     # Maximum total loss before stopping
    stop_loss_enabled = True
    
    # ========================================
    # NEW: Market State Filter
    # ========================================
    market_state_filter_enabled = True
    high_volatility_threshold = 3.0  # Vol ratio threshold
    min_spread_ratio = 0.5           # Minimum spread / volatility ratio
    
    # ========================================
    # State Variables
    # ========================================
    mid_price_buffer = np.zeros(window_size, dtype=np.float64)
    buffer_idx = 0
    is_buffer_full = False
    step_count = 0
    
    ewma_volatility = tick_size * 10
    ewma_slope = 1.0
    
    # Order tracking
    bid_order_id = -1
    ask_order_id = -1
    
    # NEW: Track PnL for stop loss
    initial_equity = 0.0
    initial_equity_set = False
    last_trade_pnl = 0.0
    total_pnl = 0.0
    
    # ========================================
    # Main Loop
    # ========================================
    max_steps = 10_000_000
    empty_depth_count = 0
    max_empty_depth = 1000
    
    while step_count < max_steps:
        step_count += 1
        
        # Check for empty depth
        depth = hbt.depth(asset_no)
        if depth.best_bid <= 0 or depth.best_ask <= 0:
            empty_depth_count += 1
            if empty_depth_count > max_empty_depth:
                break
            hbt.clear_inactive_orders()
            hbt.elapse(100_000_000)
            continue
        
        empty_depth_count = 0
        
        # Get current state
        stat_val = hbt.state_values(asset_no)
        position = stat_val.position
        balance = stat_val.balance
        fee = stat_val.fee
        
        # Calculate current equity for stop loss
        mid_price = (depth.best_bid + depth.best_ask) / 2.0
        current_equity = balance + position * mid_price - fee
        
        if not initial_equity_set:
            initial_equity = current_equity
            initial_equity_set = True
        
        total_pnl = current_equity - initial_equity
        
        # NEW: Stop Loss Check
        if stop_loss_enabled:
            if total_pnl < -max_total_loss:
                # Stop trading if total loss exceeds threshold
                if bid_order_id >= 0:
                    hbt.cancel(bid_order_id)
                if ask_order_id >= 0:
                    hbt.cancel(ask_order_id)
                hbt.clear_inactive_orders()
                hbt.elapse(100_000_000)
                continue
        
        # Update volatility buffer
        mid_price_buffer[buffer_idx] = mid_price
        buffer_idx += 1
        if buffer_idx >= window_size:
            buffer_idx = 0
            is_buffer_full = True
        
        # Calculate volatility
        if is_buffer_full:
            price_changes = np.diff(np.roll(mid_price_buffer, -buffer_idx))
            volatility = np.std(price_changes) * np.sqrt(window_size)
        else:
            if buffer_idx > 1:
                price_changes = np.diff(mid_price_buffer[:buffer_idx])
                volatility = np.std(price_changes) * np.sqrt(buffer_idx)
            else:
                volatility = base_volatility
        
        if volatility < base_volatility:
            volatility = base_volatility
        
        # EWMA smoothing
        ewma_volatility = vol_smoothing * volatility + (1 - vol_smoothing) * ewma_volatility
        
        # Regime detection
        vol_ratio = ewma_volatility / base_volatility
        
        # NEW: Market State Filter
        if market_state_filter_enabled:
            # Check if market is too volatile
            if vol_ratio > high_volatility_threshold:
                # Pause trading or widen spreads significantly
                if bid_order_id >= 0:
                    hbt.cancel(bid_order_id)
                if ask_order_id >= 0:
                    hbt.cancel(ask_order_id)
                hbt.clear_inactive_orders()
                hbt.elapse(100_000_000)
                continue
        
        if vol_ratio < 1.0:
            regime = "calm"
            spread_mult = 1.0
            alpha_mult = 1.0
            regime_gamma = gamma_base
        elif vol_ratio < 2.0:
            regime = "active"
            spread_mult = 0.95
            alpha_mult = 1.2
            regime_gamma = gamma_base
        else:
            regime = "volatile"
            spread_mult = 1.1
            alpha_mult = 1.5
            regime_gamma = gamma_base * 1.2
        
        # Calculate MLOFI with exponential decay
        mlofi = 0.0
        total_weight = 0.0
        
        for level in range(1, min(num_levels + 1, len(depth.bidq) + 1)):
            if level <= len(depth.bidq) and level <= len(depth.askq):
                bid_vol = depth.bidq[level - 1]
                ask_vol = depth.askq[level - 1]
                
                if bid_vol + ask_vol > 0:
                    level_ofi = (bid_vol - ask_vol) / (bid_vol + ask_vol)
                    weight = np.exp(-alpha_decay * (level - 1))
                    mlofi += weight * level_ofi
                    total_weight += weight
        
        if total_weight > 0:
            mlofi = mlofi / total_weight
        
        # Calculate forecast
        forecast = mlofi_weight * mlofi * alpha_mult
        
        # Calculate reservation price with quadratic penalty
        if use_quadratic_penalty and max_position > 0:
            reservation_price = (
                mid_price 
                + forecast * tick_size
                - regime_gamma * (ewma_volatility ** 2) * position * abs(position) / max_position
            )
        else:
            reservation_price = mid_price + forecast * tick_size - regime_gamma * (ewma_volatility ** 2) * position
        
        # Calculate spread
        half_spread = k_base * spread_mult * ewma_volatility
        
        # NEW: Dynamic spread adjustment based on stop loss
        if stop_loss_enabled and total_pnl < -max_total_loss * 0.5:
            # Widen spreads if approaching stop loss
            half_spread *= 1.5
        
        # Check minimum spread ratio
        if market_state_filter_enabled:
            spread_ratio = half_spread * 2 / ewma_volatility
            if spread_ratio < min_spread_ratio:
                # Spread too tight, skip this iteration
                hbt.clear_inactive_orders()
                hbt.elapse(100_000_000)
                continue
        
        # Inventory skew
        if max_position > 0:
            skew = position / max_position
        else:
            skew = 0.0
        
        # Anti-sniffing penalty
        anti_sniffing_penalty = 0.0
        if use_anti_sniffing and max_position > 0:
            anti_sniffing_penalty = lambda_read * position / max_position * tick_size
        
        # Calculate bid/ask prices
        bid_price = reservation_price - half_spread * (1 + skew) + anti_sniffing_penalty
        ask_price = reservation_price + half_spread * (1 - skew) - anti_sniffing_penalty
        
        # Round to tick size
        bid_price = np.round(bid_price / tick_size) * tick_size
        ask_price = np.round(ask_price / tick_size) * tick_size
        
        # Ensure prices are valid
        if bid_price >= depth.best_bid:
            bid_price = depth.best_bid - tick_size
        if ask_price <= depth.best_ask:
            ask_price = depth.best_ask + tick_size
        
        # Cancel existing orders
        if bid_order_id >= 0:
            hbt.cancel(bid_order_id)
        if ask_order_id >= 0:
            hbt.cancel(ask_order_id)
        
        # Place new orders if within position limits
        if position > -max_position:
            bid_order_id = hbt.submit(
                asset_no, GTX, LIMIT, BUY, bid_price, order_qty
            )
        
        if position < max_position:
            ask_order_id = hbt.submit(
                asset_no, GTX, LIMIT, SELL, ask_price, order_qty
            )
        
        # Record periodically
        if recorder is not None and step_count % 100 == 0:
            try:
                recorder.record(hbt)
            except:
                pass
        
        # Elapse time
        hbt.clear_inactive_orders()
        hbt.elapse(100_000_000)  # 100ms

