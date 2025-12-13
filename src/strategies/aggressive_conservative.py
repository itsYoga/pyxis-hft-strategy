from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT, BUY, SELL

"""
Conservative Aggressive Market Making Strategy
==============================================

Optimized for positive PnL by:
1. Wider spreads (k_base = 2.0 vs 1.5)
2. More conservative risk management (gamma_base = 0.08 vs 0.05)
3. Better inventory control (max_position = 8.0 vs 10.0)
4. Less aggressive alpha trust (mlofi_weight = 0.6 vs 0.8)
5. More conservative regime spreads

Key changes from aggressive.py:
- k_base: 1.5 → 2.0 (wider spreads)
- gamma_base: 0.05 → 0.08 (more risk averse)
- max_position: 10.0 → 8.0 (stricter inventory)
- order_qty: 1.0 → 0.8 (smaller orders)
- mlofi_weight: 0.8 → 0.6 (less trust in OFI)
- Regime spreads: wider in all regimes
"""


@njit
def market_making_algo(hbt, stat, recorder=None):
    """
    Conservative Aggressive Market Making Strategy
    
    Optimized for positive PnL with wider spreads and better risk management.
    
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
    # Conservative Parameters
    # ========================================
    
    # More conservative risk aversion
    gamma_base = 0.08  # Increased from 0.05
    k_base = 2.0       # Increased from 1.5 (wider spreads)
    
    # Less aggressive alpha weights
    micro_weight = 0.3         # Increased from 0.2
    mlofi_weight = 0.6         # Decreased from 0.8 (less trust)
    slope_weight = 0.0          # Disabled
    
    # ========================================
    # Phase 1: Defensive Mechanisms
    # ========================================
    use_quadratic_penalty = True
    
    # Anti-sniffing parameters
    lambda_read = 0.3
    max_skew_penalty = 0.5
    use_anti_sniffing = True
    
    # Multi-level depth
    num_levels = 5
    ofi_decay = 0.7
    
    # Optimized MLOFI with exponential decay
    use_exponential_decay_mlofi = True
    alpha_decay = 0.5
    
    # Volatility
    window_size = 500
    base_volatility = tick_size * 5
    vol_smoothing = 0.1
    
    # More conservative order management
    order_qty = 0.8      # Decreased from 1.0
    max_position = 8.0    # Decreased from 10.0
    
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
            hbt.elapse(100_000_000)  # 100ms
            continue
        
        empty_depth_count = 0
        
        # Get current state
        stat_val = hbt.state_values(asset_no)
        position = stat_val.position
        balance = stat_val.balance
        
        # Calculate mid price
        mid_price = (depth.best_bid + depth.best_ask) / 2.0
        
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
        
        if vol_ratio < 1.0:
            regime = "calm"
            spread_mult = 1.1      # Wider than original
            alpha_mult = 0.9        # Less trust
            regime_gamma = gamma_base * 1.0
        elif vol_ratio < 2.0:
            regime = "active"
            spread_mult = 1.2      # Wider than original
            alpha_mult = 1.1       # Less trust
            regime_gamma = gamma_base * 1.0
        else:
            regime = "volatile"
            spread_mult = 1.5      # Much wider
            alpha_mult = 1.2       # Less trust
            regime_gamma = gamma_base * 1.3  # More risk averse
        
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

