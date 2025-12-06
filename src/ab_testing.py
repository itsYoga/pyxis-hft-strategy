"""
A/B Testing Framework for Online Learning Evaluation
=====================================================

Compare strategy performance WITH vs WITHOUT River online learning.
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
import time


@dataclass
class ABTestResult:
    """Results from A/B comparison"""
    baseline_pnl: float = 0.0
    river_pnl: float = 0.0
    baseline_trades: int = 0
    river_trades: int = 0
    improvement_pct: float = 0.0
    is_significant: bool = False
    t_statistic: float = 0.0
    p_value: float = 1.0
    
    def __str__(self) -> str:
        winner = "River" if self.river_pnl > self.baseline_pnl else "Baseline"
        sig = "✓ Significant" if self.is_significant else "✗ Not Significant"
        return (
            f"{'='*50}\n"
            f"A/B TEST RESULTS\n"
            f"{'='*50}\n"
            f"\n"
            f"Baseline (Static Weights):\n"
            f"   PnL:    {self.baseline_pnl:+.4f}\n"
            f"   Trades: {self.baseline_trades}\n"
            f"\n"
            f"River (Online Learning):\n"
            f"   PnL:    {self.river_pnl:+.4f}\n"
            f"   Trades: {self.river_trades}\n"
            f"\n"
            f"Improvement: {self.improvement_pct:+.2f}%\n"
            f"Winner: {winner}\n"
            f"Statistical: {sig} (p={self.p_value:.4f})\n"
            f"{'='*50}"
        )


class ABTester:
    """
    A/B Tester for comparing River vs Static weights.
    
    Usage:
        tester = ABTester()
        
        # Run baseline strategy
        tester.start_baseline()
        for step in simulation:
            pnl = run_baseline_strategy(...)
            tester.record_baseline(pnl)
        tester.end_baseline()
        
        # Run River strategy
        tester.start_river()
        for step in simulation:
            pnl = run_river_strategy(...)
            tester.record_river(pnl)
        tester.end_river()
        
        # Get results
        result = tester.analyze()
        print(result)
    """
    
    def __init__(self, min_samples: int = 100):
        self.min_samples = min_samples
        self.reset()
    
    def reset(self):
        self.baseline_pnls: List[float] = []
        self.river_pnls: List[float] = []
        self.current_mode = None
    
    def start_baseline(self):
        self.baseline_pnls = []
        self.current_mode = 'baseline'
    
    def start_river(self):
        self.river_pnls = []
        self.current_mode = 'river'
    
    def record(self, pnl: float):
        """Record a PnL observation for current mode"""
        if self.current_mode == 'baseline':
            self.baseline_pnls.append(pnl)
        elif self.current_mode == 'river':
            self.river_pnls.append(pnl)
    
    def record_baseline(self, pnl: float):
        self.baseline_pnls.append(pnl)
    
    def record_river(self, pnl: float):
        self.river_pnls.append(pnl)
    
    def end_baseline(self):
        self.current_mode = None
    
    def end_river(self):
        self.current_mode = None
    
    def analyze(self) -> ABTestResult:
        """
        Analyze A/B test results with statistical significance.
        Uses Welch's t-test for unequal variances.
        """
        result = ABTestResult()
        
        if not self.baseline_pnls or not self.river_pnls:
            return result
        
        # Basic stats
        baseline_arr = np.array(self.baseline_pnls)
        river_arr = np.array(self.river_pnls)
        
        result.baseline_pnl = float(np.sum(baseline_arr))
        result.river_pnl = float(np.sum(river_arr))
        result.baseline_trades = len(self.baseline_pnls)
        result.river_trades = len(self.river_pnls)
        
        # Improvement
        if result.baseline_pnl != 0:
            result.improvement_pct = (
                (result.river_pnl - result.baseline_pnl) / abs(result.baseline_pnl) * 100
            )
        else:
            result.improvement_pct = 0 if result.river_pnl == 0 else float('inf')
        
        # Statistical test (Welch's t-test)
        if len(baseline_arr) >= self.min_samples and len(river_arr) >= self.min_samples:
            n1, n2 = len(baseline_arr), len(river_arr)
            m1, m2 = np.mean(baseline_arr), np.mean(river_arr)
            v1, v2 = np.var(baseline_arr, ddof=1), np.var(river_arr, ddof=1)
            
            # Welch's t-statistic
            se = np.sqrt(v1/n1 + v2/n2)
            if se > 0:
                result.t_statistic = (m2 - m1) / se
                
                # Approximate degrees of freedom (Welch-Satterthwaite)
                df = (v1/n1 + v2/n2)**2 / (
                    (v1/n1)**2/(n1-1) + (v2/n2)**2/(n2-1)
                )
                
                # Two-tailed p-value approximation
                # Using normal approximation for large df
                result.p_value = 2 * (1 - self._norm_cdf(abs(result.t_statistic)))
                result.is_significant = result.p_value < 0.05
        
        return result
    
    @staticmethod
    def _norm_cdf(x: float) -> float:
        """Approximate normal CDF using error function"""
        return 0.5 * (1 + np.tanh(x * 0.7978845608))


def quick_ab_test(
    signal_generator,
    n_steps: int = 1000,
    baseline_weights: Dict[str, float] = None
) -> ABTestResult:
    """
    Quick A/B test for River vs static weights.
    
    Args:
        signal_generator: Function that yields (signals, realized_return) tuples
        n_steps: Number of steps to simulate
        baseline_weights: Static weights for baseline
    
    Returns:
        ABTestResult
    """
    from online_learning import OnlineAlphaLearner, AlphaSignals
    
    if baseline_weights is None:
        baseline_weights = {'micro': 0.3, 'mlofi': 0.5, 'slope': 0.2}
    
    tester = ABTester()
    learner = OnlineAlphaLearner(warmup_steps=50)
    
    # Generate test data
    np.random.seed(42)
    test_data = []
    mid_price = 10000.0
    
    for i in range(n_steps):
        # Random signals
        micro = np.random.randn() * 0.5
        mlofi = np.random.randn() * 0.8
        slope = np.random.randn() * 0.3
        
        # Price change (correlated with mlofi for realistic test)
        mid_price += mlofi * 0.5 + np.random.randn() * 2
        
        test_data.append({
            'micro': micro,
            'mlofi': mlofi,
            'slope': slope,
            'mid_price': mid_price
        })
    
    # Run baseline
    print("Running baseline (static weights)...")
    tester.start_baseline()
    prev_price = test_data[0]['mid_price']
    
    for i, data in enumerate(test_data[1:], 1):
        # Baseline forecast
        forecast = sum(baseline_weights.get(k, 0) * data[k] for k in ['micro', 'mlofi', 'slope'])
        realized = data['mid_price'] - prev_price
        
        # PnL: did we predict correctly?
        pnl = forecast * realized  # Positive if same sign
        tester.record_baseline(pnl)
        prev_price = data['mid_price']
    
    tester.end_baseline()
    
    # Run River
    print("Running River (online learning)...")
    tester.start_river()
    prev_price = test_data[0]['mid_price']
    
    for i, data in enumerate(test_data[1:], 1):
        signals = AlphaSignals(
            timestamp=i * 100_000_000,
            micro_price_alpha=data['micro'],
            mlofi_alpha=data['mlofi'],
            slope_alpha=data['slope'],
            mid_price=data['mid_price']
        )
        
        # River forecast (uses learned weights)
        forecast = learner.get_forecast(signals)
        learner.observe(signals)
        
        realized = data['mid_price'] - prev_price
        pnl = forecast * realized
        tester.record_river(pnl)
        prev_price = data['mid_price']
    
    tester.end_river()
    
    return tester.analyze()


if __name__ == '__main__':
    print("Running A/B Test: Static Weights vs River Online Learning")
    print("-" * 50)
    
    result = quick_ab_test(None, n_steps=2000)
    print(result)
    
    # Interpret
    print("\nInterpretation:")
    if result.is_significant and result.river_pnl > result.baseline_pnl:
        print("✓ River SIGNIFICANTLY improves PnL. Use it!")
    elif result.river_pnl > result.baseline_pnl:
        print("? River improves PnL but not statistically significant.")
        print("  Consider: more data, different parameters, or stick with baseline.")
    else:
        print("✗ River does NOT improve PnL. Consider:")
        print("  - Adjusting learning rate")
        print("  - Increasing warmup period")
        print("  - Using different features")
