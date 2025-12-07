from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT, BUY, SELL

"""
HA4 (Hierarchical Adaptive Alpha Architecture - Aggressive)
============================================================

Key optimizations from HA3:
1. Lower risk aversion (gamma 0.1 → 0.05)
2. Higher alpha trust in volatile regimes (0.5 → 1.5)
3. Tighter spreads in volatile regimes (1.5x → 1.1x)
4. No position limit reduction in volatile regimes
5. Asymmetric "Hunt" logic - tighten side aligned with alpha
6. Non-linear alpha boost for extreme imbalances
7. Capped slope adjustment (max 1.2x)

Philosophy: "You must be in the market to make money"
- Prioritize fill rate over per-trade margin
- Trust alpha signals, especially during volatility
- Maximize inventory turnover, not minimize risk
"""


@njit
def market_making_algo(hbt, stat):
    """
    HA4 Aggressive Market Making Strategy
    
    Optimization targets:
    - Higher trade frequency (fill rate)
    - Larger inventory tolerance
    - Alpha-driven asymmetric quotes
    """
    asset_no = 0
    tick_size = hbt.depth(asset_no).tick_size
    
    # ========================================
    # HA4 Aggressive Parameters
    # ========================================
    
    # Lower risk aversion - allow inventory swings
    gamma_base = 0.05           # Was 0.1 in HA3
    k_base = 1.5
    
    # Higher alpha weights - trust the signals
    micro_weight = 0.2          # Reduced (OFI is more important)
    mlofi_weight = 0.8          # Was 0.5 - OFI is primary predictor
    slope_weight = 0.0          # Disable EPI (causes double penalty)
    
    # Multi-level depth
    num_levels = 5
    ofi_decay = 0.7
    
    # Volatility
    window_size = 500
    base_volatility = tick_size * 5
    vol_smoothing = 0.1
    
    # Order management - NO REDUCTION in volatile regime
    order_qty = 1.0
    max_position = 10.0         # Always 10, never reduced
    
    # ========================================
    # State Variables
    # ========================================
    mid_price_buffer = np.zeros(window_size, dtype=np.float64)
    buffer_idx = 0
    is_buffer_full = False
    step_count = 0
    
    ewma_volatility = tick_size * 10
    ewma_slope = 1.0
    
    prev_bid_prices = np.zeros(num_levels, dtype=np.float64)
    prev_ask_prices = np.zeros(num_levels, dtype=np.float64)
    prev_bid_qtys = np.zeros(num_levels, dtype=np.float64)
    prev_ask_qtys = np.zeros(num_levels, dtype=np.float64)
    prev_initialized = False
    
    # ========================================
    # Main Event Loop
    # ========================================
    while True:
        ret = hbt.elapse(100_000_000)  # 100ms
        if ret != 0:
            print("Elapse returned:", ret)
            break
        
        step_count += 1
        hbt.clear_inactive_orders(asset_no)
        
        # Get Market Data
        depth = hbt.depth(asset_no)
        if depth.best_bid == 0 or depth.best_ask == 0:
            continue
        if np.isnan(depth.best_bid) or np.isnan(depth.best_ask):
            continue
        
        best_bid = depth.best_bid
        best_ask = depth.best_ask
        best_bid_tick = int(best_bid / tick_size)
        best_ask_tick = int(best_ask / tick_size)
        best_bid_qty = depth.best_bid_qty
        best_ask_qty = depth.best_ask_qty
        
        mid_price = (best_bid + best_ask) / 2.0
        
        # ========================================
        # Alpha 1: Micro Price
        # ========================================
        if best_bid_qty + best_ask_qty > 0:
            micro_price = (
                best_bid * best_ask_qty + best_ask * best_bid_qty
            ) / (best_bid_qty + best_ask_qty)
        else:
            micro_price = mid_price
        
        alpha_micro = (micro_price - mid_price) / tick_size
        
        # ========================================
        # Alpha 2: Multi-Level OFI (MLOFI)
        # ========================================
        bid_qtys = np.zeros(num_levels, dtype=np.float64)
        ask_qtys = np.zeros(num_levels, dtype=np.float64)
        bid_prices = np.zeros(num_levels, dtype=np.float64)
        ask_prices = np.zeros(num_levels, dtype=np.float64)
        
        for i in range(num_levels):
            bid_tick = best_bid_tick - i
            ask_tick = best_ask_tick + i
            bid_prices[i] = bid_tick * tick_size
            ask_prices[i] = ask_tick * tick_size
            bid_qtys[i] = depth.bid_qty_at_tick(bid_tick)
            ask_qtys[i] = depth.ask_qty_at_tick(ask_tick)
        
        mlofi = 0.0
        total_weight = 0.0
        
        if prev_initialized:
            for i in range(num_levels):
                weight = ofi_decay ** i
                
                delta_bid = 0.0
                delta_ask = 0.0
                
                if bid_prices[i] > prev_bid_prices[i]:
                    delta_bid = bid_qtys[i]
                elif bid_prices[i] < prev_bid_prices[i]:
                    delta_bid = -prev_bid_qtys[i]
                else:
                    delta_bid = bid_qtys[i] - prev_bid_qtys[i]
                
                if ask_prices[i] < prev_ask_prices[i]:
                    delta_ask = ask_qtys[i]
                elif ask_prices[i] > prev_ask_prices[i]:
                    delta_ask = -prev_ask_qtys[i]
                else:
                    delta_ask = ask_qtys[i] - prev_ask_qtys[i]
                
                mlofi += weight * (delta_bid - delta_ask)
                total_weight += weight
        
        if total_weight > 0:
            mlofi = mlofi / total_weight
        
        avg_l1_qty = (best_bid_qty + best_ask_qty) / 2.0
        if avg_l1_qty > 0:
            mlofi_normalized = mlofi / avg_l1_qty
        else:
            mlofi_normalized = 0.0
        
        # HA4: NO CLIPPING - allow extreme signals
        # Only soft clip to prevent numerical issues
        mlofi_normalized = max(-5.0, min(5.0, mlofi_normalized))
        
        # Update previous state
        for i in range(num_levels):
            prev_bid_prices[i] = bid_prices[i]
            prev_ask_prices[i] = ask_prices[i]
            prev_bid_qtys[i] = bid_qtys[i]
            prev_ask_qtys[i] = ask_qtys[i]
        prev_initialized = True
        
        # ========================================
        # LOB Slope (for regime only, not for spread)
        # ========================================
        cumulative_bid = 0.0
        cumulative_ask = 0.0
        slope_bid_sum = 0.0
        slope_ask_sum = 0.0
        valid_levels = 0
        
        for i in range(num_levels):
            cumulative_bid += bid_qtys[i]
            cumulative_ask += ask_qtys[i]
            dist = (i + 1)
            if cumulative_bid > 0 and dist > 0:
                slope_bid_sum += np.log(cumulative_bid + 1) / dist
                valid_levels += 1
            if cumulative_ask > 0 and dist > 0:
                slope_ask_sum += np.log(cumulative_ask + 1) / dist
                valid_levels += 1
        
        if valid_levels > 0:
            current_slope = (slope_bid_sum + slope_ask_sum) / valid_levels
        else:
            current_slope = 1.0
        
        ewma_slope = vol_smoothing * current_slope + (1 - vol_smoothing) * ewma_slope
        
        # ========================================
        # Volatility (EWMA)
        # ========================================
        mid_price_buffer[buffer_idx] = mid_price
        buffer_idx += 1
        if buffer_idx >= window_size:
            buffer_idx = 0
            is_buffer_full = True
        
        if is_buffer_full:
            mean_price = np.sum(mid_price_buffer) / window_size
            variance = np.sum((mid_price_buffer - mean_price) ** 2) / window_size
            current_vol = np.sqrt(variance)
            if current_vol > 0:
                ewma_volatility = vol_smoothing * current_vol + (1 - vol_smoothing) * ewma_volatility
        
        volatility = max(ewma_volatility, tick_size)
        
        # ========================================
        # HA4 Regime Detection (Aggressive)
        # ========================================
        vol_ratio = volatility / base_volatility
        
        # HA4: TRUST ALPHA MORE in volatility, NOT LESS
        if vol_ratio < 1.0:
            # Calm - normal operation
            regime_spread_mult = 1.0
            regime_alpha_mult = 1.0
            regime_gamma = gamma_base
        elif vol_ratio < 2.0:
            # Active - slightly tighter, trust alpha
            regime_spread_mult = 0.95
            regime_alpha_mult = 1.2
            regime_gamma = gamma_base
        else:
            # Volatile - HA4 AGGRESSIVE: tight spread, high alpha trust
            regime_spread_mult = 1.1       # Was 1.5 - stay competitive
            regime_alpha_mult = 1.5        # Was 0.5 - TRUST THE SIGNAL
            regime_gamma = gamma_base * 1.2  # Slightly more skew for protection
        
        # ========================================
        # Non-Linear Alpha Boost (Extreme Imbalances)
        # ========================================
        alpha_boost = 1.0
        if abs(mlofi_normalized) > 1.5:
            alpha_boost = 2.0  # Double signal for extreme OFI
        elif abs(mlofi_normalized) > 1.0:
            alpha_boost = 1.5
        
        # ========================================
        # Combined Alpha Signal
        # ========================================
        forecast = regime_alpha_mult * alpha_boost * (
            micro_weight * alpha_micro +
            mlofi_weight * mlofi_normalized
            # slope_weight removed - no EPI double penalty
        )
        
        # ========================================
        # Reservation Price
        # ========================================
        position = hbt.position(asset_no)
        
        reservation_price = (
            mid_price 
            + forecast * tick_size
            - position * regime_gamma * (volatility ** 2)
        )
        
        # ========================================
        # HA4: Asymmetric "Hunt" Logic
        # ========================================
        # If alpha is bullish, tighten bid (to buy), widen ask (to sell higher)
        # If alpha is bearish, tighten ask (to sell), widen bid (to buy lower)
        
        half_spread_base = (2.0 / regime_gamma) * np.log(1.0 + regime_gamma / k_base) / 2.0
        half_spread = half_spread_base * regime_spread_mult
        
        # HA4: Capped slope adjustment (max 1.2x)
        if ewma_slope > 0.001:
            slope_adjustment = 1.0 / ewma_slope
            slope_adjustment = min(1.2, max(0.8, slope_adjustment))
        else:
            slope_adjustment = 1.0
        
        half_spread *= slope_adjustment
        
        # Asymmetric spread based on alpha direction
        if forecast > 0.5:  # Bullish
            bid_spread_mult = 0.8   # Tighten bid to buy
            ask_spread_mult = 1.2   # Widen ask to sell higher
        elif forecast < -0.5:  # Bearish
            bid_spread_mult = 1.2   # Widen bid to buy lower
            ask_spread_mult = 0.8   # Tighten ask to sell
        else:  # Neutral
            bid_spread_mult = 1.0
            ask_spread_mult = 1.0
        
        # Inventory skew
        skew = 0.2 * position / max_position if max_position > 0 else 0.0
        
        bid_price = reservation_price - half_spread * bid_spread_mult * (1 + skew)
        ask_price = reservation_price + half_spread * ask_spread_mult * (1 - skew)
        
        # Quantize
        bid_price_tick = round(bid_price / tick_size) * tick_size
        ask_price_tick = round(ask_price / tick_size) * tick_size
        
        if bid_price_tick >= ask_price_tick:
            bid_price_tick = mid_price - tick_size
            ask_price_tick = mid_price + tick_size
        
        bid_price_tick = min(bid_price_tick, best_bid)
        ask_price_tick = max(ask_price_tick, best_ask)
        
        # ========================================
        # Order Management
        # ========================================
        if stat[0] > 0:
            hbt.cancel(asset_no, int(stat[0]), False)
        if stat[2] > 0:
            hbt.cancel(asset_no, int(stat[2]), False)
        
        new_bid_id = int(stat[0]) + 1 if stat[0] > 0 else 1
        new_ask_id = int(stat[2]) + 1 if stat[2] > 0 else 2
        
        if new_bid_id == new_ask_id:
            new_ask_id += 1
        
        # HA4: NO position reduction in volatile regime
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
