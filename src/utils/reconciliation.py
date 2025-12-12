"""
Reconciliation Module for HFT Backtest
======================================
對賬機制：驗證交易記錄、倉位變化和餘額的一致性

Based on Kronos (hftbacktest) PnL methodology:
- Equity = Balance + Position * Price * ContractSize - Fee
- PnL = Equity_end - Equity_start
"""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
from datetime import datetime


@dataclass
class TradeRecord:
    """單筆成交記錄"""
    timestamp: int           # 納秒時間戳
    order_id: int
    side: str               # 'BUY' or 'SELL'
    price: float
    quantity: float
    fee: float
    balance_after: float
    position_after: float
    
    @property
    def trade_value(self) -> float:
        """交易金額 (不含手續費)"""
        return self.price * self.quantity
    
    @property
    def side_sign(self) -> float:
        """BUY = +1, SELL = -1"""
        return 1.0 if self.side == 'BUY' else -1.0


@dataclass
class ReconciliationResult:
    """對賬結果"""
    is_valid: bool
    balance_expected: float
    balance_actual: float
    balance_diff: float
    position_expected: float
    position_actual: float
    position_diff: float
    fee_expected: float
    fee_actual: float
    fee_diff: float
    trade_count: int
    errors: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        lines = [
            f"\n{'='*50}",
            f"RECONCILIATION REPORT - {status}",
            f"{'='*50}",
            f"Trade Count: {self.trade_count}",
            f"",
            f"Balance:",
            f"   Expected:   {self.balance_expected:>12,.4f}",
            f"   Actual:     {self.balance_actual:>12,.4f}",
            f"   Diff:       {self.balance_diff:>+12,.4f}",
            f"",
            f"Position:",
            f"   Expected:   {self.position_expected:>12,.4f}",
            f"   Actual:     {self.position_actual:>12,.4f}",
            f"   Diff:       {self.position_diff:>+12,.4f}",
            f"",
            f"Fees:",
            f"   Expected:   {self.fee_expected:>12,.4f}",
            f"   Actual:     {self.fee_actual:>12,.4f}",
            f"   Diff:       {self.fee_diff:>+12,.4f}",
            f"{'='*50}",
        ]
        
        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                lines.append(f"   - {err}")
        
        return "\n".join(lines)


class Reconciler:
    """
    對賬器：追蹤交易並驗證最終狀態
    
    Usage:
        reconciler = Reconciler()
        # During trading:
        reconciler.record_trade(timestamp, order_id, 'BUY', price, qty, fee, balance, position)
        # After backtest:
        result = reconciler.reconcile(final_balance, final_position, final_fee)
        print(result)
    """
    
    def __init__(self, contract_size: float = 1.0, tolerance: float = 1e-6):
        self.contract_size = contract_size
        self.tolerance = tolerance
        self.trades: List[TradeRecord] = []
        self.initial_balance = 0.0
        self.initial_position = 0.0
        
    def set_initial_state(self, balance: float = 0.0, position: float = 0.0):
        """設定初始狀態"""
        self.initial_balance = balance
        self.initial_position = position
        
    def record_trade(
        self,
        timestamp: int,
        order_id: int,
        side: str,
        price: float,
        quantity: float,
        fee: float,
        balance_after: float,
        position_after: float
    ):
        """記錄一筆成交"""
        trade = TradeRecord(
            timestamp=timestamp,
            order_id=order_id,
            side=side.upper(),
            price=price,
            quantity=quantity,
            fee=fee,
            balance_after=balance_after,
            position_after=position_after
        )
        self.trades.append(trade)
        
    def reconcile(
        self,
        actual_balance: float,
        actual_position: float,
        actual_fee: float
    ) -> ReconciliationResult:
        """
        執行對賬
        
        驗證邏輯:
        - Balance: 初始餘額 - Σ(trade_value * side_sign)
        - Position: 初始持倉 + Σ(quantity * side_sign)  
        - Fee: Σ(fee)
        """
        errors = []
        
        # Calculate expected values from trades
        expected_balance = self.initial_balance
        expected_position = self.initial_position
        expected_fee = 0.0
        
        for trade in self.trades:
            # Balance decreases when buying, increases when selling
            expected_balance -= trade.trade_value * trade.side_sign
            # Position increases when buying, decreases when selling
            expected_position += trade.quantity * trade.side_sign
            # Fees accumulate
            expected_fee += trade.fee
        
        # Calculate differences
        balance_diff = actual_balance - expected_balance
        position_diff = actual_position - expected_position
        fee_diff = actual_fee - expected_fee
        
        # Check validity
        is_valid = True
        
        if abs(balance_diff) > self.tolerance:
            is_valid = False
            errors.append(f"Balance mismatch: expected {expected_balance:.4f}, got {actual_balance:.4f}")
            
        if abs(position_diff) > self.tolerance:
            is_valid = False
            errors.append(f"Position mismatch: expected {expected_position:.4f}, got {actual_position:.4f}")
            
        if abs(fee_diff) > self.tolerance:
            is_valid = False
            errors.append(f"Fee mismatch: expected {expected_fee:.4f}, got {actual_fee:.4f}")
        
        return ReconciliationResult(
            is_valid=is_valid,
            balance_expected=expected_balance,
            balance_actual=actual_balance,
            balance_diff=balance_diff,
            position_expected=expected_position,
            position_actual=actual_position,
            position_diff=position_diff,
            fee_expected=expected_fee,
            fee_actual=actual_fee,
            fee_diff=fee_diff,
            trade_count=len(self.trades),
            errors=errors
        )
    
    def get_trade_summary(self) -> dict:
        """取得交易摘要"""
        if not self.trades:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_volume': 0.0,
                'total_value': 0.0,
                'total_fee': 0.0,
            }
        
        buy_trades = [t for t in self.trades if t.side == 'BUY']
        sell_trades = [t for t in self.trades if t.side == 'SELL']
        
        return {
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_volume': sum(t.quantity for t in self.trades),
            'total_value': sum(t.trade_value for t in self.trades),
            'total_fee': sum(t.fee for t in self.trades),
            'avg_price': sum(t.price for t in self.trades) / len(self.trades),
        }
    
    def export_to_csv(self, filepath: str):
        """輸出交易記錄到 CSV"""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'order_id', 'side', 'price', 'quantity',
                'trade_value', 'fee', 'balance_after', 'position_after'
            ])
            
            for trade in self.trades:
                writer.writerow([
                    trade.timestamp,
                    trade.order_id,
                    trade.side,
                    trade.price,
                    trade.quantity,
                    trade.trade_value,
                    trade.fee,
                    trade.balance_after,
                    trade.position_after
                ])
        
        print(f"Exported {len(self.trades)} trades to {filepath}")


def calculate_pnl_kronos(
    balance: float,
    position: float,
    price: float,
    fee: float,
    contract_size: float = 1.0
) -> dict:
    """
    Kronos PnL 計算方法
    
    Args:
        balance: 當前餘額
        position: 當前持倉
        price: 當前價格 (mid price)
        fee: 累計手續費
        contract_size: 合約大小
        
    Returns:
        dict with equity_wo_fee, equity, pnl components
    """
    equity_wo_fee = balance + position * price * contract_size
    equity = equity_wo_fee - fee
    
    return {
        'balance': balance,
        'position': position,
        'price': price,
        'fee': fee,
        'equity_wo_fee': equity_wo_fee,
        'equity': equity,
        'position_value': position * price * contract_size,
    }


# Test case
if __name__ == '__main__':
    print("Testing Reconciliation Module...")
    print("-" * 50)
    
    # Create reconciler
    reconciler = Reconciler()
    reconciler.set_initial_state(balance=0.0, position=0.0)
    
    # Simulate trades
    # Buy 1 unit at 100
    reconciler.record_trade(
        timestamp=1000000000,
        order_id=1,
        side='BUY',
        price=100.0,
        quantity=1.0,
        fee=0.02,
        balance_after=-100.0,
        position_after=1.0
    )
    
    # Sell 0.5 unit at 105
    reconciler.record_trade(
        timestamp=2000000000,
        order_id=2,
        side='SELL',
        price=105.0,
        quantity=0.5,
        fee=0.01,
        balance_after=-47.5,  # -100 + 52.5
        position_after=0.5
    )
    
    # Check reconciliation
    result = reconciler.reconcile(
        actual_balance=-47.5,
        actual_position=0.5,
        actual_fee=0.03
    )
    print(result)
    
    # Get trade summary
    print("\nTrade Summary:")
    summary = reconciler.get_trade_summary()
    for k, v in summary.items():
        print(f"   {k}: {v}")
    
    # Test Kronos PnL calculation
    print("\n" + "-" * 50)
    print("Testing Kronos PnL Calculation...")
    
    pnl_result = calculate_pnl_kronos(
        balance=-47.5,
        position=0.5,
        price=110.0,  # Current mid price
        fee=0.03
    )
    
    print("\nPnL Breakdown:")
    for k, v in pnl_result.items():
        print(f"   {k}: {v:,.4f}")
    
    print(f"\nFinal PnL: {pnl_result['equity']:,.4f}")
