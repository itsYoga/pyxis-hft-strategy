"""
VPIN (Volume-Synchronized Probability of Informed Trading) Calculator
=====================================================================

VPIN provides a forward-looking metric for Flow Toxicity - the probability
that you are trading against informed traders.

Reference: Easley et al. on VPIN and Flow Toxicity
"""

import numpy as np
from numba import njit
from typing import Optional


@njit
def calculate_vpin_from_buckets(buy_volumes, sell_volumes, total_volume):
    """
    Calculate VPIN from volume buckets
    
    Args:
        buy_volumes: Array of buy volumes per bucket
        sell_volumes: Array of sell volumes per bucket
        total_volume: Total volume across all buckets
    
    Returns:
        VPIN value (0.0 to 1.0)
    """
    n_buckets = len(buy_volumes)
    if n_buckets == 0 or total_volume == 0:
        return 0.0
    
    volume_imbalance = 0.0
    for i in range(n_buckets):
        volume_imbalance += abs(buy_volumes[i] - sell_volumes[i])
    
    vpin = volume_imbalance / (n_buckets * total_volume)
    return min(1.0, max(0.0, vpin))


class VPINCalculator:
    """
    Calculate VPIN using volume bucketing (not time bars)
    
    Volume bucketing groups trades into buckets of constant volume,
    providing a more accurate measure of order flow imbalance.
    """
    
    def __init__(self, volume_bucket_size: float = 10000.0, window_size: int = 50):
        """
        Initialize VPIN Calculator
        
        Args:
            volume_bucket_size: Volume per bucket (e.g., 10,000 contracts)
            window_size: Number of buckets to use for VPIN calculation
        """
        self.volume_bucket_size = volume_bucket_size
        self.window_size = window_size
        
        # Current bucket
        self.current_bucket_buy = 0.0
        self.current_bucket_sell = 0.0
        self.current_bucket_volume = 0.0
        
        # Completed buckets (circular buffer)
        self.buy_volumes = np.zeros(window_size, dtype=np.float64)
        self.sell_volumes = np.zeros(window_size, dtype=np.float64)
        self.bucket_idx = 0
        self.n_buckets_filled = 0
        
        # VPIN history for CDF calculation
        self.vpin_history = []
        self.max_history = 1000
    
    def add_trade(self, volume: float, side: str):
        """
        Add a trade to the current bucket
        
        Args:
            volume: Trade volume
            side: 'buy' or 'sell' (or 'BUY'/'SELL')
        """
        side_upper = side.upper()
        
        # Add to current bucket
        self.current_bucket_volume += volume
        if side_upper == 'BUY' or side_upper == 'B':
            self.current_bucket_buy += volume
        else:
            self.current_bucket_sell += volume
        
        # Check if bucket is full
        if self.current_bucket_volume >= self.volume_bucket_size:
            self._finalize_bucket()
    
    def _finalize_bucket(self):
        """Move current bucket to history and start new bucket"""
        # Store current bucket
        self.buy_volumes[self.bucket_idx] = self.current_bucket_buy
        self.sell_volumes[self.bucket_idx] = self.current_bucket_sell
        
        # Update indices
        self.bucket_idx = (self.bucket_idx + 1) % self.window_size
        if self.n_buckets_filled < self.window_size:
            self.n_buckets_filled += 1
        
        # Reset current bucket (carry over excess volume)
        excess_volume = self.current_bucket_volume - self.volume_bucket_size
        excess_ratio = excess_volume / self.current_bucket_volume if self.current_bucket_volume > 0 else 0.0
        
        self.current_bucket_buy = self.current_bucket_buy * excess_ratio
        self.current_bucket_sell = self.current_bucket_sell * excess_ratio
        self.current_bucket_volume = excess_volume
    
    def calculate_vpin(self) -> float:
        """
        Calculate current VPIN value
        
        Returns:
            VPIN value (0.0 to 1.0)
        """
        if self.n_buckets_filled == 0:
            return 0.0
        
        # Use filled buckets
        n_buckets = self.n_buckets_filled
        buy_vols = self.buy_volumes[:n_buckets]
        sell_vols = self.sell_volumes[:n_buckets]
        total_volume = np.sum(buy_vols) + np.sum(sell_vols)
        
        if total_volume == 0:
            return 0.0
        
        vpin = calculate_vpin_from_buckets(buy_vols, sell_vols, total_volume)
        
        # Store in history
        self.vpin_history.append(vpin)
        if len(self.vpin_history) > self.max_history:
            self.vpin_history.pop(0)
        
        return vpin
    
    def get_toxicity_percentile(self) -> float:
        """
        Get CDF percentile of current VPIN
        
        Returns:
            Percentile (0.0 to 1.0), where 1.0 = highest toxicity
        """
        if len(self.vpin_history) < 10:
            return 0.5  # Not enough data
        
        current_vpin = self.calculate_vpin()
        history_array = np.array(self.vpin_history[:-1])  # Exclude current
        
        if len(history_array) == 0:
            return 0.5
        
        # Calculate percentile
        percentile = np.sum(history_array <= current_vpin) / len(history_array)
        return percentile
    
    def is_toxic(self, threshold: float = 0.9) -> bool:
        """
        Check if current market is toxic
        
        Args:
            threshold: Toxicity threshold (default 0.9 = top 10%)
        
        Returns:
            True if market is toxic
        """
        return self.get_toxicity_percentile() > threshold
    
    def reset(self):
        """Reset calculator state"""
        self.current_bucket_buy = 0.0
        self.current_bucket_sell = 0.0
        self.current_bucket_volume = 0.0
        self.buy_volumes.fill(0.0)
        self.sell_volumes.fill(0.0)
        self.bucket_idx = 0
        self.n_buckets_filled = 0
        self.vpin_history.clear()

