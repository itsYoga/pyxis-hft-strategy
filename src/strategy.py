from numba import njit
import numpy as np
from hftbacktest import GTX, LIMIT, BUY, SELL

"""
HA3 (Hierarchical Adaptive Alpha Architecture) Market Making Strategy
=====================================================================

Enhanced Alpha Signals based on 2024-2025 HFT research:
1. Multi-Level Order Flow Imbalance (MLOFI) - captures hidden liquidity
2. LOB Slope - measures market elasticity/resilience
3. Volatility-Adaptive Spread - protects against adverse selection
4. Regime Detection - adjusts strategy based on market conditions
"""


@njit
def market_making_algo(hbt, stat):
    """
    HA3 Market Making Strategy
    
    Alpha Signals:
    1. Micro Price - BBO quantity-weighted price
    2. Multi-Level OFI - aggregated across 5 levels
    3. LOB Slope - order book elasticity
    
    Regime Detection:
    - Uses volatility ratio to detect calm/active/volatile regimes
    - Adjusts spread and alpha weights dynamically
    
    stat array layout:
    [0] = current bid order id
    [1] = current bid price
    [2] = current ask order id
    [3] = current ask price
    [4] = step counter
    [5] = prev_best_bid
    [6] = prev_best_ask
    [7] = prev_bid_qty
    [8] = prev_ask_qty
    [9] = cumulative_ofi
    """
    asset_no = 0
    tick_size = hbt.depth(asset_no).tick_size
    
    # ========================================
    # Strategy Parameters (HA3 Optimized)
    # ========================================
    
    # Avellaneda-Stoikov Base Parameters
    gamma_base = 0.1          # Base risk aversion
    k_base = 1.5              # Base spread elasticity
    
    # Alpha Weights
    micro_weight = 0.3        # Micro price alpha weight
    mlofi_weight = 0.5        # Multi-level OFI weight
    slope_weight = 0.2        # LOB Slope weight (EPI component)
    
    # Multi-level depth parameters
    num_levels = 5            # Analyze top 5 price levels
    ofi_decay = 0.7           # Exponential decay for deeper levels
    
    # Volatility & Regime
    window_size = 500         # Volatility window (faster adaptation)
    base_volatility = tick_size * 5  # Reference volatility for regime
    vol_smoothing = 0.1       # EWMA smoothing factor
    
    # Order management
    order_qty = 1.0
    max_position = 10.0
    
    # ========================================
    # State Variables
    # ========================================
    mid_price_buffer = np.zeros(window_size, dtype=np.float64)
    buffer_idx = 0
    is_buffer_full = False
    step_count = 0
    
    # EWMA volatility (more responsive)
    ewma_volatility = tick_size * 10
    ewma_slope = 1.0
    
    # Previous state for OFI delta calculation
    prev_bid_prices = np.zeros(num_levels, dtype=np.float64)
    prev_ask_prices = np.zeros(num_levels, dtype=np.float64)
    prev_bid_qtys = np.zeros(num_levels, dtype=np.float64)
    prev_ask_qtys = np.zeros(num_levels, dtype=np.float64)
    prev_initialized = False
    
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
        best_bid_tick = int(best_bid / tick_size)
        best_ask_tick = int(best_ask / tick_size)
        best_bid_qty = depth.best_bid_qty
        best_ask_qty = depth.best_ask_qty
        
        mid_price = (best_bid + best_ask) / 2.0
        spread = best_ask - best_bid
        
        # ========================================
        # 3. Alpha 1: Micro Price (Level 1)
        # ========================================
        if best_bid_qty + best_ask_qty > 0:
            micro_price = (
                best_bid * best_ask_qty + best_ask * best_bid_qty
            ) / (best_bid_qty + best_ask_qty)
        else:
            micro_price = mid_price
        
        alpha_micro = (micro_price - mid_price) / tick_size
        
        # ========================================
        # 4. Alpha 2: Multi-Level OFI (MLOFI)
        # ========================================
        # Collect multi-level depth data
        bid_qtys = np.zeros(num_levels, dtype=np.float64)
        ask_qtys = np.zeros(num_levels, dtype=np.float64)
        bid_prices = np.zeros(num_levels, dtype=np.float64)
        ask_prices = np.zeros(num_levels, dtype=np.float64)
        
        # Get quantities at each level (using tick-based access)
        for i in range(num_levels):
            bid_tick = best_bid_tick - i
            ask_tick = best_ask_tick + i
            
            bid_prices[i] = bid_tick * tick_size
            ask_prices[i] = ask_tick * tick_size
            bid_qtys[i] = depth.bid_qty_at_tick(bid_tick)
            ask_qtys[i] = depth.ask_qty_at_tick(ask_tick)
        
        # Calculate MLOFI with exponential decay weights
        mlofi = 0.0
        total_weight = 0.0
        
        if prev_initialized:
            for i in range(num_levels):
                weight = ofi_decay ** i  # Level 1 has weight 1.0, Level 5 has weight ~0.24
                
                # Delta calculation for this level
                delta_bid = 0.0
                delta_ask = 0.0
                
                # Price improvement/decay logic (simplified for numba)
                if bid_prices[i] > prev_bid_prices[i]:
                    # Price improved - full qty contribution
                    delta_bid = bid_qtys[i]
                elif bid_prices[i] < prev_bid_prices[i]:
                    # Price decayed - negative contribution
                    delta_bid = -prev_bid_qtys[i]
                else:
                    # Same price - quantity change
                    delta_bid = bid_qtys[i] - prev_bid_qtys[i]
                
                if ask_prices[i] < prev_ask_prices[i]:
                    # Ask improved - full qty contribution (negative for asks)
                    delta_ask = ask_qtys[i]
                elif ask_prices[i] > prev_ask_prices[i]:
                    # Ask decayed
                    delta_ask = -prev_ask_qtys[i]
                else:
                    delta_ask = ask_qtys[i] - prev_ask_qtys[i]
                
                # Net imbalance: positive = buy pressure
                mlofi += weight * (delta_bid - delta_ask)
                total_weight += weight
        
        # Normalize MLOFI
        if total_weight > 0:
            mlofi = mlofi / total_weight
        
        # Normalize by average level 1 quantity for comparability
        avg_l1_qty = (best_bid_qty + best_ask_qty) / 2.0
        if avg_l1_qty > 0:
            mlofi_normalized = mlofi / avg_l1_qty
        else:
            mlofi_normalized = 0.0
        
        # Clip extreme values
        mlofi_normalized = max(-2.0, min(2.0, mlofi_normalized))
        
        # Update previous state
        for i in range(num_levels):
            prev_bid_prices[i] = bid_prices[i]
            prev_ask_prices[i] = ask_prices[i]
            prev_bid_qtys[i] = bid_qtys[i]
            prev_ask_qtys[i] = ask_qtys[i]
        prev_initialized = True
        
        # ========================================
        # 5. Alpha 3: LOB Slope (Market Elasticity)
        # ========================================
        # Slope = how quickly depth accumulates away from mid
        # High slope = thick book = mean reversion
        # Low slope = thin book = momentum
        
        cumulative_bid = 0.0
        cumulative_ask = 0.0
        slope_bid_sum = 0.0
        slope_ask_sum = 0.0
        valid_levels = 0
        
        for i in range(num_levels):
            cumulative_bid += bid_qtys[i]
            cumulative_ask += ask_qtys[i]
            
            # Price distance from mid (in ticks)
            dist_bid = (i + 1)  # Level 1 = 1 tick, etc.
            dist_ask = (i + 1)
            
            if cumulative_bid > 0 and dist_bid > 0:
                slope_bid_sum += np.log(cumulative_bid + 1) / dist_bid
                valid_levels += 1
            if cumulative_ask > 0 and dist_ask > 0:
                slope_ask_sum += np.log(cumulative_ask + 1) / dist_ask
                valid_levels += 1
        
        if valid_levels > 0:
            current_slope = (slope_bid_sum + slope_ask_sum) / valid_levels
        else:
            current_slope = 1.0
        
        # EWMA smoothing for slope
        ewma_slope = vol_smoothing * current_slope + (1 - vol_smoothing) * ewma_slope
        
        # ========================================
        # 6. Update Volatility (EWMA)
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
        # 7. Regime Detection (Volatility-Based)
        # ========================================
        vol_ratio = volatility / base_volatility
        
        # Regime adjustments
        if vol_ratio < 1.0:
            # Calm regime - tighter spread, trust alpha signals
            regime_spread_mult = 0.8
            regime_alpha_mult = 1.2
            regime_gamma = gamma_base * 0.8
        elif vol_ratio < 2.0:
            # Active regime - normal parameters
            regime_spread_mult = 1.0
            regime_alpha_mult = 1.0
            regime_gamma = gamma_base
        else:
            # Volatile regime - wider spread, reduce alpha reliance
            regime_spread_mult = 1.5
            regime_alpha_mult = 0.5
            regime_gamma = gamma_base * 1.5
        
        # ========================================
        # 8. Expected Price Impact (EPI)
        # ========================================
        # EPI = Force / Mass = OFI / Slope
        if ewma_slope > 0.001:
            epi = mlofi_normalized / ewma_slope
        else:
            epi = mlofi_normalized
        
        epi = max(-3.0, min(3.0, epi))  # Clip
        
        # ========================================
        # 9. Combined Alpha Signal
        # ========================================
        forecast = regime_alpha_mult * (
            micro_weight * alpha_micro +
            mlofi_weight * mlofi_normalized +
            slope_weight * epi
        )
        
        # ========================================
        # 10. Reservation Price (AS + Alpha)
        # ========================================
        position = hbt.position(asset_no)
        
        reservation_price = (
            mid_price 
            + forecast * tick_size              # Alpha adjustment
            - position * regime_gamma * (volatility ** 2)  # Inventory risk
        )
        
        # ========================================
        # 11. Dynamic Spread Calculation
        # ========================================
        half_spread_base = (2.0 / regime_gamma) * np.log(1.0 + regime_gamma / k_base) / 2.0
        half_spread = half_spread_base * regime_spread_mult
        
        # Additional spread adjustment based on slope
        # Thin book -> wider spread for protection
        slope_adjustment = 1.0 / max(0.5, ewma_slope)
        half_spread *= min(1.5, max(0.8, slope_adjustment))
        
        # Inventory skew
        skew = 0.2 * position / max_position if max_position > 0 else 0.0
        
        bid_price = reservation_price - half_spread * (1 + skew)
        ask_price = reservation_price + half_spread * (1 - skew)
        
        # Quantize to tick size
        bid_price_tick = round(bid_price / tick_size) * tick_size
        ask_price_tick = round(ask_price / tick_size) * tick_size
        
        # Don't cross the spread
        if bid_price_tick >= ask_price_tick:
            bid_price_tick = mid_price - tick_size
            ask_price_tick = mid_price + tick_size
        
        # Stay within market
        bid_price_tick = min(bid_price_tick, best_bid)
        ask_price_tick = max(ask_price_tick, best_ask)
        
        # ========================================
        # 12. Order Management
        # ========================================
        if stat[0] > 0:
            hbt.cancel(asset_no, int(stat[0]), False)
        if stat[2] > 0:
            hbt.cancel(asset_no, int(stat[2]), False)
        
        new_bid_id = int(stat[0]) + 1 if stat[0] > 0 else 1
        new_ask_id = int(stat[2]) + 1 if stat[2] > 0 else 2
        
        if new_bid_id == new_ask_id:
            new_ask_id += 1
        
        # ========================================
        # 13. Position Limits with Regime Adjustment
        # ========================================
        # In volatile regime, reduce max position
        effective_max_pos = max_position
        if vol_ratio >= 2.0:
            effective_max_pos = max_position * 0.5
        
        can_buy = position < effective_max_pos
        can_sell = position > -effective_max_pos
        
        if can_buy:
            hbt.submit_buy_order(asset_no, new_bid_id, bid_price_tick, order_qty, GTX, LIMIT, False)
        if can_sell:
            hbt.submit_sell_order(asset_no, new_ask_id, ask_price_tick, order_qty, GTX, LIMIT, False)
        
        # Update state
        stat[0] = new_bid_id
        stat[1] = bid_price_tick
        stat[2] = new_ask_id
        stat[3] = ask_price_tick
        stat[4] = step_count

