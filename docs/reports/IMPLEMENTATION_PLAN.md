# Strategy Optimization Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for the optimizations described in `STRATEGY_OPTIMIZATION_ROADMAP.md`.

---

## Phase 1: Defensive Mechanisms (Week 1-2)

### 1.1 Quadratic Inventory Penalty

**File:** `src/strategies/aggressive.py`

**Changes:**
- Replace linear inventory skew with quadratic penalty
- Update reservation price calculation:
  ```python
  # Old: linear
  inventory_adjustment = position * regime_gamma * (volatility ** 2)
  
  # New: quadratic
  inventory_adjustment = position * regime_gamma * (volatility ** 2) * abs(position) / max_position
  ```

**Testing:**
- Compare inventory distribution before/after
- Measure impact on max inventory reached
- Verify spread widening behavior

### 1.2 Anti-Sniffing Logic

**File:** `src/strategies/aggressive.py`

**New Parameters:**
```python
lambda_read = 0.3  # Anti-sniffing penalty coefficient
max_skew_penalty = 0.5  # Maximum skew adjustment (in ticks)
```

**Implementation:**
```python
def calculate_anti_sniffing_adjustment(position, max_position, lambda_read):
    """Calculate adjustment to mask inventory intent"""
    normalized_position = position / max_position
    skew = normalized_position * 0.2  # Current skew
    
    # Penalty pulls quotes back toward mid if skew is too obvious
    sniff_penalty = lambda_read * skew
    sniff_penalty = max(-max_skew_penalty, min(max_skew_penalty, sniff_penalty))
    
    return sniff_penalty
```

**Integration:**
```python
sniff_adjustment = calculate_anti_sniffing_adjustment(position, max_position, lambda_read)

bid_price = reservation_price - half_spread * bid_spread_mult * (1 + skew) - sniff_adjustment
ask_price = reservation_price + half_spread * ask_spread_mult * (1 - skew) + sniff_adjustment
```

---

## Phase 2: Flow Toxicity Detection (Week 2-3)

### 2.1 VPIN Calculator

**New File:** `src/utils/vpin.py`

**Implementation:**
```python
class VPINCalculator:
    def __init__(self, volume_bucket_size=10000, window_size=50):
        self.volume_bucket_size = volume_bucket_size
        self.window_size = window_size
        self.buckets = []
        self.vpin_history = []
    
    def add_trade(self, volume, side):
        """Add trade to current bucket"""
        # Implementation here
    
    def calculate_vpin(self):
        """Calculate current VPIN value"""
        # Implementation here
    
    def get_toxicity_percentile(self):
        """Get CDF percentile of current VPIN"""
        # Implementation here
```

### 2.2 Toxicity Response

**File:** `src/strategies/aggressive.py`

**Integration:**
```python
from utils.vpin import VPINCalculator

vpin_calc = VPINCalculator(volume_bucket_size=10000)

# In main loop
vpin = vpin_calc.calculate_vpin()
toxicity_percentile = vpin_calc.get_toxicity_percentile()

if toxicity_percentile > 0.9:
    # High toxicity: widen spreads or cancel orders
    regime_spread_mult *= 3.0  # Triple spreads
    # Or: cancel_all_orders()
```

---

## Phase 3: Enhanced MLOFI (Week 3)

### 3.1 Exponential Decay MLOFI

**File:** `src/strategies/aggressive.py`

**Current Implementation:**
```python
# Line 171: Current decay
weight = ofi_decay ** i  # ofi_decay = 0.7
```

**Optimized Implementation:**
```python
# Use exponential decay with alpha = 0.5
alpha_decay = 0.5
for i in range(num_levels):
    weight = np.exp(-alpha_decay * i)  # More aggressive decay
    # ... rest of MLOFI calculation
```

**Testing:**
- Compare prediction accuracy vs current implementation
- Measure impact on signal-to-noise ratio

---

## Phase 4: Queue Position Simulation (Week 4)

### 4.1 Queue Position Tracker

**New File:** `src/core/queue_position.py`

**Implementation:**
```python
class QueuePositionTracker:
    def __init__(self, reduce_ratio_base=0.1):
        self.reduce_ratio_base = reduce_ratio_base
        self.queue_positions = {}  # order_id -> position
    
    def place_order(self, order_id, level_total_volume):
        """Initialize queue position when order is placed"""
        self.queue_positions[order_id] = level_total_volume
    
    def process_trade(self, order_id, trade_volume):
        """Update position after trade"""
        if order_id in self.queue_positions:
            self.queue_positions[order_id] -= trade_volume
    
    def process_cancel(self, order_id, cancel_volume, level_total_volume):
        """Update position after cancellation"""
        if order_id in self.queue_positions:
            current_pos = self.queue_positions[order_id]
            # Calculate reduce ratio
            r = max(self.reduce_ratio_base, current_pos / level_total_volume)
            self.queue_positions[order_id] -= r * cancel_volume
    
    def get_fill_probability(self, order_id):
        """Estimate fill probability based on queue position"""
        # Implementation
```

### 4.2 Integration with Backtest

**File:** `src/core/backtest.py`

**Note:** This requires modifications to the hftbacktest engine or custom order fill logic.

---

## Phase 5: DRL Architecture (Week 5-8)

### 5.1 State Space Definition

**New File:** `src/learning/drl_state.py`

```python
class StateSpace:
    def __init__(self):
        self.features = [
            'normalized_inventory',
            'spread',
            'volatility',
            'rsi',
            'macd',
            'vpin',
            'mlofi',
            'lob_imbalance'
        ]
    
    def extract_state(self, market_data, position, max_position):
        """Extract state vector"""
        # Implementation
```

### 5.2 Action Space Definition

**New File:** `src/learning/drl_action.py`

```python
class ActionSpace:
    def __init__(self):
        self.gamma_range = (0.5, 5.0)  # Risk aversion multiplier
        self.xi_range = (-0.5, 0.5)    # Skew offset
    
    def decode_action(self, action_vector):
        """Decode action from neural network output"""
        # Implementation
```

### 5.3 Reward Function

**New File:** `src/learning/drl_reward.py`

```python
def calculate_reward(delta_pnl, position, beta=1.0, lambda_inv=0.1):
    """Asymmetric Dampened PnL reward"""
    reward = delta_pnl
    reward -= beta * max(0, -delta_pnl) ** 2  # Quadratic penalty for losses
    reward -= lambda_inv * abs(position)  # Inventory penalty
    return reward
```

### 5.4 RL Agent

**New File:** `src/learning/drl_agent.py`

**Framework:** Use Stable-Baselines3 or Ray RLlib

```python
from stable_baselines3 import PPO

class AlphaASAgent:
    def __init__(self):
        self.model = PPO("MlpPolicy", env, verbose=1)
    
    def train(self, timesteps=100000):
        self.model.learn(total_timesteps=timesteps)
    
    def predict(self, state):
        action, _ = self.model.predict(state)
        return action
```

---

## Phase 6: HMM Regime Detection (Week 9)

### 6.1 HMM Implementation

**New File:** `src/learning/regime_hmm.py`

```python
from hmmlearn import hmm

class RegimeHMM:
    def __init__(self, n_states=4):
        self.model = hmm.GaussianHMM(n_components=n_states)
        self.states = ['Calm', 'Trending', 'Mean-Reverting', 'Crisis']
    
    def train(self, returns, volatility):
        """Train HMM on historical data"""
        features = np.column_stack([returns, volatility])
        self.model.fit(features)
    
    def predict_regime(self, returns, volatility):
        """Predict current regime"""
        features = np.array([[returns, volatility]])
        state = self.model.predict(features)[0]
        return self.states[state]
```

### 6.2 Regime-Based Parameters

**File:** `src/strategies/aggressive.py`

```python
regime = hmm_model.predict_regime(returns, volatility)

regime_params = {
    'Calm': {'gamma_mult': 1.0, 'spread_mult': 1.0},
    'Trending': {'gamma_mult': 0.8, 'spread_mult': 0.9, 'disable_fade': True},
    'Mean-Reverting': {'gamma_mult': 1.2, 'spread_mult': 1.1},
    'Crisis': {'gamma_mult': 2.0, 'spread_mult': 3.0}
}
```

---

## Testing Strategy

### Unit Tests
- Each component should have unit tests
- Test edge cases (zero volume, extreme positions, etc.)

### Integration Tests
- Test full strategy with all optimizations enabled
- Compare against baseline strategy

### Backtest Validation
- Run on multiple datasets (different dates, exchanges)
- Measure key metrics:
  - Sharpe Ratio
  - Max Drawdown
  - Win Rate
  - Fill Rate
  - Inventory Distribution

### A/B Testing
- Compare optimized vs baseline on same data
- Statistical significance testing

---

## Performance Metrics

Track the following metrics for each optimization:

1. **PnL Improvement**: % change in total PnL
2. **Risk Reduction**: Change in max drawdown, volatility
3. **Fill Rate Impact**: Change in order fill rate
4. **Inventory Management**: Distribution of inventory levels
5. **Toxicity Avoidance**: Number of toxic fills avoided

---

## Rollout Plan

1. **Development**: Implement in feature branches
2. **Testing**: Comprehensive backtesting
3. **Staging**: Paper trading / demo account
4. **Production**: Gradual rollout with monitoring

---

*Last Updated: 2025-12-07*

