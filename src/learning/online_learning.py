"""
River Online Learning Module for HFT Strategy
==============================================

Uses River (https://riverml.xyz) for online/incremental learning.
Dynamically adjusts alpha weights based on realized performance.

Features:
- Online linear regression for alpha weight learning
- Streaming feature normalization
- Real-time performance tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np

# River imports (will be installed separately)
try:
    from river import linear_model, preprocessing, optim, metrics
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False
    print("Warning: River not installed. Run: pip install river")


@dataclass
class AlphaSignals:
    """Container for alpha signals at a given timestamp"""
    timestamp: int
    micro_price_alpha: float
    mlofi_alpha: float
    slope_alpha: float  # EPI
    mid_price: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'micro': self.micro_price_alpha,
            'mlofi': self.mlofi_alpha,
            'slope': self.slope_alpha,
        }


class OnlineAlphaLearner:
    """
    Online learner for alpha signal weights.
    
    Uses linear regression to learn optimal weights for combining alpha signals.
    Target: realized price change (return)
    
    Usage:
        learner = OnlineAlphaLearner()
        
        # Each timestep:
        signals = AlphaSignals(...)
        learner.observe(signals)
        
        # When price moves:
        learner.update(realized_return)
        
        # Get current weights:
        weights = learner.get_weights()
    """
    
    def __init__(
        self,
        learning_rate: float = 0.01,
        l2_reg: float = 0.001,
        warmup_steps: int = 100
    ):
        self.learning_rate = learning_rate
        self.l2_reg = l2_reg
        self.warmup_steps = warmup_steps
        self.step_count = 0
        
        # Pending signal (waiting for realized return)
        self.pending_signal: Optional[AlphaSignals] = None
        self.pending_mid_price: float = 0.0
        
        # Performance tracking
        self.cumulative_pnl = 0.0
        self.prediction_errors: List[float] = []
        
        if RIVER_AVAILABLE:
            # Online linear model with L2 regularization
            self.model = linear_model.LinearRegression(
                optimizer=optim.SGD(self.learning_rate),
                l2=self.l2_reg,
                intercept_lr=0.0  # No intercept
            )
            
            # Feature scaler (online standardization)
            self.scaler = preprocessing.StandardScaler()
            
            # Metrics
            self.mae_metric = metrics.MAE()
            self.r2_metric = metrics.R2()
        else:
            # Fallback: simple EWMA weights
            self.model = None
            self.weights = {'micro': 0.3, 'mlofi': 0.5, 'slope': 0.2}
            self.ewma_alpha = 0.1
    
    def observe(self, signals: AlphaSignals):
        """
        Observe new alpha signals.
        Call this at each timestep before making trading decisions.
        """
        # If we have a pending signal, first update the model
        if self.pending_signal is not None and signals.mid_price != self.pending_mid_price:
            # Calculate realized return (in ticks for normalization)
            realized_return = (signals.mid_price - self.pending_mid_price)
            self.update(realized_return)
        
        # Store current signals for next update
        self.pending_signal = signals
        self.pending_mid_price = signals.mid_price
        self.step_count += 1
    
    def update(self, realized_return: float):
        """
        Update model with realized return.
        Called internally when price changes are observed.
        """
        if self.pending_signal is None:
            return
        
        x = self.pending_signal.to_dict()
        y = realized_return
        
        if RIVER_AVAILABLE and self.model is not None:
            # Scale features (learn and transform)
            self.scaler.learn_one(x)
            x_scaled = self.scaler.transform_one(x)
            
            # Predict (for metrics)
            y_pred = self.model.predict_one(x_scaled)
            
            # Update metrics
            self.mae_metric.update(y, y_pred)
            self.r2_metric.update(y, y_pred)
            
            # Learn from example
            self.model.learn_one(x_scaled, y)
            
            # Track error
            self.prediction_errors.append(abs(y - y_pred))
        else:
            # Fallback: adjust weights based on signal-return correlation
            for key in x:
                if x[key] * y > 0:  # Same sign = good prediction
                    self.weights[key] = min(1.0, self.weights[key] * 1.01)
                else:
                    self.weights[key] = max(0.1, self.weights[key] * 0.99)
        
        # Track PnL
        self.cumulative_pnl += realized_return
        self.pending_signal = None
    
    def get_weights(self) -> Dict[str, float]:
        """
        Get current alpha weights.
        Returns normalized weights that sum to 1.
        """
        if self.step_count < self.warmup_steps:
            # Return default weights during warmup
            return {'micro': 0.3, 'mlofi': 0.5, 'slope': 0.2}
        
        if RIVER_AVAILABLE and self.model is not None:
            # Extract weights from linear model
            weights = dict(self.model.weights)
            
            if not weights:
                return {'micro': 0.3, 'mlofi': 0.5, 'slope': 0.2}
            
            # Normalize to sum to 1 (take absolute values for importance)
            total = sum(abs(w) for w in weights.values())
            if total > 0:
                return {k: abs(v) / total for k, v in weights.items()}
            else:
                return {'micro': 0.3, 'mlofi': 0.5, 'slope': 0.2}
        else:
            # Normalize fallback weights
            total = sum(self.weights.values())
            return {k: v / total for k, v in self.weights.items()}
    
    def get_forecast(self, signals: AlphaSignals) -> float:
        """
        Get combined alpha forecast using learned weights.
        """
        x = signals.to_dict()
        
        if RIVER_AVAILABLE and self.model is not None and self.step_count >= self.warmup_steps:
            x_scaled = self.scaler.transform_one(x)
            return self.model.predict_one(x_scaled)
        else:
            weights = self.get_weights()
            return sum(weights.get(k, 0) * v for k, v in x.items())
    
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        stats = {
            'step_count': self.step_count,
            'cumulative_pnl': self.cumulative_pnl,
            'is_warmed_up': self.step_count >= self.warmup_steps,
        }
        
        if RIVER_AVAILABLE:
            stats['mae'] = float(self.mae_metric.get()) if self.step_count > 0 else 0.0
            stats['r2'] = float(self.r2_metric.get()) if self.step_count > 0 else 0.0
        
        if self.prediction_errors:
            stats['avg_error'] = np.mean(self.prediction_errors[-100:])
        
        return stats
    
    def __str__(self) -> str:
        weights = self.get_weights()
        stats = self.get_stats()
        return (
            f"OnlineAlphaLearner:\n"
            f"  Steps: {stats['step_count']}\n"
            f"  Weights: micro={weights.get('micro', 0):.3f}, "
            f"mlofi={weights.get('mlofi', 0):.3f}, "
            f"slope={weights.get('slope', 0):.3f}\n"
            f"  Cumulative PnL: {stats['cumulative_pnl']:.4f}"
        )


class RegimeLearner:
    """
    Online learner for regime-specific parameters.
    
    Learns optimal gamma (risk aversion) and spread multiplier
    for each volatility regime.
    """
    
    def __init__(self):
        self.regime_stats: Dict[str, Dict] = {
            'calm': {'gamma': 0.08, 'spread_mult': 0.8, 'pnl': 0.0, 'count': 0},
            'active': {'gamma': 0.10, 'spread_mult': 1.0, 'pnl': 0.0, 'count': 0},
            'volatile': {'gamma': 0.15, 'spread_mult': 1.5, 'pnl': 0.0, 'count': 0},
        }
        self.learning_rate = 0.01
        self.current_regime = 'active'
    
    def classify_regime(self, vol_ratio: float) -> str:
        """Classify current regime based on volatility ratio"""
        if vol_ratio < 1.0:
            return 'calm'
        elif vol_ratio < 2.0:
            return 'active'
        else:
            return 'volatile'
    
    def update(self, regime: str, pnl: float):
        """Update regime statistics with realized PnL"""
        self.current_regime = regime
        stats = self.regime_stats[regime]
        stats['count'] += 1
        stats['pnl'] += pnl
        
        # Adjust parameters based on PnL
        if stats['count'] > 100:  # After warmup
            avg_pnl = stats['pnl'] / stats['count']
            
            if avg_pnl < 0:
                # Losing money - widen spread, increase risk aversion
                stats['gamma'] = min(0.3, stats['gamma'] * (1 + self.learning_rate))
                stats['spread_mult'] = min(2.0, stats['spread_mult'] * (1 + self.learning_rate))
            else:
                # Making money - can be more aggressive
                stats['gamma'] = max(0.05, stats['gamma'] * (1 - self.learning_rate * 0.5))
                stats['spread_mult'] = max(0.5, stats['spread_mult'] * (1 - self.learning_rate * 0.5))
    
    def get_params(self, regime: str) -> Tuple[float, float]:
        """Get learned parameters for a regime"""
        stats = self.regime_stats[regime]
        return stats['gamma'], stats['spread_mult']
    
    def get_summary(self) -> Dict:
        """Get summary of all regime stats"""
        return {
            regime: {
                'gamma': stats['gamma'],
                'spread_mult': stats['spread_mult'],
                'avg_pnl': stats['pnl'] / max(1, stats['count']),
                'count': stats['count']
            }
            for regime, stats in self.regime_stats.items()
        }


# ========================================
# Integration Example
# ========================================

if __name__ == '__main__':
    print("Testing Online Learning Module...")
    print("-" * 50)
    
    # Test AlphaLearner
    learner = OnlineAlphaLearner(warmup_steps=10)
    
    # Simulate some data
    np.random.seed(42)
    for i in range(100):
        # Generate fake signals
        signals = AlphaSignals(
            timestamp=i * 100_000_000,
            micro_price_alpha=np.random.randn() * 0.5,
            mlofi_alpha=np.random.randn() * 0.8,
            slope_alpha=np.random.randn() * 0.3,
            mid_price=10000 + np.random.randn() * 10
        )
        
        learner.observe(signals)
    
    print(learner)
    print("\nLearned Weights:", learner.get_weights())
    print("Stats:", learner.get_stats())
    
    # Test RegimeLearner
    print("\n" + "-" * 50)
    print("Testing Regime Learner...")
    
    regime_learner = RegimeLearner()
    
    # Simulate regime changes
    for i in range(500):
        vol_ratio = 0.5 + np.random.rand() * 2.5
        regime = regime_learner.classify_regime(vol_ratio)
        pnl = np.random.randn() * 0.1
        if regime == 'volatile':
            pnl -= 0.05  # Volatile regime tends to lose
        regime_learner.update(regime, pnl)
    
    print("\nRegime Summary:")
    for regime, stats in regime_learner.get_summary().items():
        print(f"  {regime}: gamma={stats['gamma']:.3f}, "
              f"spread={stats['spread_mult']:.2f}, "
              f"avg_pnl={stats['avg_pnl']:.4f}")
    
    print("\n✓ Online learning module ready!")
    if not RIVER_AVAILABLE:
        print("⚠ Install River for full functionality: pip install river")
