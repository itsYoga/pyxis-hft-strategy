from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT, BUY, SELL

"""
Aggressive Market Making Strategy
==================================

Key features:
1. Lower risk aversion (gamma 0.05)
2. Higher alpha trust in volatile regimes (1.5x)
3. Tighter spreads in volatile regimes (1.1x)
4. No position limit reduction in volatile regimes
5. Asymmetric "Hunt" logic - tighten side aligned with alpha
6. Non-linear alpha boost for extreme imbalances
7. Capped slope adjustment (max 1.2x)
8. Quadratic inventory penalty - stricter boundaries on inventory
9. Anti-sniffing logic - mask inventory intent from predatory algorithms

Philosophy: "You must be in the market to make money"
- Prioritize fill rate over per-trade margin
- Trust alpha signals, especially during volatility
- Maximize inventory turnover, not minimize risk
- Defend against predatory algorithms and flow toxicity
"""


@njit
def market_making_algo(hbt, stat, recorder=None):
    """
    Aggressive Market Making Strategy
    
    Optimization targets:
    - Higher trade frequency (fill rate)
    - Larger inventory tolerance
    - Alpha-driven asymmetric quotes
    
    Args:
        hbt: Backtest engine
        stat: State array for tracking orders
        recorder: Optional recorder for data collection (recorder.recorder from Recorder class)
    """
    asset_no = 0
    tick_size = hbt.depth(asset_no).tick_size
    
    # Record initial state if recorder is provided
    if recorder is not None:
        try:
            recorder.record(hbt)
        except:
            pass  # Ignore recording errors
    
    # ========================================
    # Aggressive Parameters
    # ========================================
    
    # Lower risk aversion - allow inventory swings
    gamma_base = 0.05
    k_base = 1.5
    
    # Higher alpha weights - trust the signals
    micro_weight = 0.2          # Reduced (OFI is more important)
    mlofi_weight = 0.8          # Was 0.5 - OFI is primary predictor
    slope_weight = 0.0          # Disable EPI (causes double penalty)
    
    # ========================================
    # Phase 1: Defensive Mechanisms
    # ========================================
    # Quadratic inventory penalty (instead of linear)
    use_quadratic_penalty = True
    
    # Anti-sniffing parameters
    lambda_read = 0.3           # Anti-sniffing penalty coefficient
    max_skew_penalty = 0.5      # Maximum skew adjustment (in ticks)
    use_anti_sniffing = True
    
    # Multi-level depth
    num_levels = 5
    ofi_decay = 0.7
    
    # Phase 3: Optimized MLOFI with exponential decay
    use_exponential_decay_mlofi = True
    alpha_decay = 0.5  # Exponential decay factor for MLOFI
    
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
    max_steps = 1_000_000  # Safety limit: prevent infinite loops
    consecutive_empty_depth = 0
    max_empty_depth = 100  # If depth is empty for 100 consecutive steps, exit
    
    while step_count < max_steps:
        ret = hbt.elapse(100_000_000)  # 100ms
        if ret != 0:
            # Data ended (ret == 1) or error occurred
            break
        
        step_count += 1
        hbt.clear_inactive_orders(asset_no)
        
        # Record data periodically if recorder is provided (every 100 steps)
        if recorder is not None and step_count % 100 == 0:
            try:
                recorder.record(hbt)
            except:
                pass  # Ignore recording errors
        
        # Get Market Data
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
                # Phase 3: Use exponential decay instead of power decay
                if use_exponential_decay_mlofi:
                    weight = np.exp(-alpha_decay * i)  # Exponential decay: e^(-0.5*i)
                else:
                    weight = ofi_decay ** i  # Original power decay
                
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
        
        # NO CLIPPING - allow extreme signals
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
        # Regime Detection (Aggressive)
        # ========================================
        vol_ratio = volatility / base_volatility
        
        # TRUST ALPHA MORE in volatility, NOT LESS
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
            # Volatile - AGGRESSIVE: tight spread, high alpha trust
            regime_spread_mult = 1.1       # Stay competitive
            regime_alpha_mult = 1.5        # TRUST THE SIGNAL
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
        
        # Phase 1.1: Quadratic Inventory Penalty
        # Linear: position * gamma * volatility^2
        # Quadratic: position * gamma * volatility^2 * |position| / max_position
        if use_quadratic_penalty:
            # Quadratic penalty: more aggressive as inventory approaches limits
            position_factor = abs(position) / max_position if max_position > 0 else 0.0
            inventory_adjustment = position * regime_gamma * (volatility ** 2) * (1.0 + position_factor)
        else:
            # Original linear penalty
            inventory_adjustment = position * regime_gamma * (volatility ** 2)
        
        reservation_price = (
            mid_price 
            + forecast * tick_size
            - inventory_adjustment
        )
        
        # ========================================
        # Asymmetric "Hunt" Logic
        # ========================================
        # If alpha is bullish, tighten bid (to buy), widen ask (to sell higher)
        # If alpha is bearish, tighten ask (to sell), widen bid (to buy lower)
        
        half_spread_base = (2.0 / regime_gamma) * np.log(1.0 + regime_gamma / k_base) / 2.0
        half_spread = half_spread_base * regime_spread_mult
        
        # Capped slope adjustment (max 1.2x)
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
        
        # Phase 1.2: Anti-Sniffing Logic
        # Mask inventory intent by pulling quotes back toward mid if skew is too obvious
        if use_anti_sniffing:
            normalized_position = position / max_position if max_position > 0 else 0.0
            # Calculate how obvious the skew is
            obvious_skew = abs(skew)
            # Penalty pulls quotes back toward mid to mask intent
            sniff_penalty = lambda_read * obvious_skew * tick_size
            # Cap the penalty
            sniff_penalty = max(-max_skew_penalty * tick_size, min(max_skew_penalty * tick_size, sniff_penalty))
            
            # Apply penalty: if long (positive position), reduce bid/ask spread to hide intent
            # If short (negative position), reduce ask/bid spread
            if position > 0:  # Long position - want to sell but hide it
                bid_sniff_adjust = -sniff_penalty  # Pull bid up slightly
                ask_sniff_adjust = sniff_penalty   # Pull ask down slightly
            elif position < 0:  # Short position - want to buy but hide it
                bid_sniff_adjust = sniff_penalty   # Pull bid down slightly
                ask_sniff_adjust = -sniff_penalty  # Pull ask up slightly
            else:
                bid_sniff_adjust = 0.0
                ask_sniff_adjust = 0.0
        else:
            bid_sniff_adjust = 0.0
            ask_sniff_adjust = 0.0
        
        bid_price = reservation_price - half_spread * bid_spread_mult * (1 + skew) + bid_sniff_adjust
        ask_price = reservation_price + half_spread * ask_spread_mult * (1 - skew) + ask_sniff_adjust
        
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
        
        # NO position reduction in volatile regime
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
