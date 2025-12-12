"""
Test Result Manager
===================
系統化管理測試結果，支持版本比較和歷史記錄
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ..core.backtest import run_backtest
    from ..core.config_loader import load_config
    from ..utils.logger import get_logger
except ImportError:
    from core.backtest import run_backtest
    from core.config_loader import load_config
    from utils.logger import get_logger

logger = get_logger(__name__)


class TestResultManager:
    """測試結果管理器"""
    
    def __init__(self, results_dir: str = "../docs/results"):
        """
        初始化測試結果管理器
        
        Args:
            results_dir: 結果保存目錄
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.results_dir / "test_results.json"
        self.results: List[Dict] = []
        self._load_results()
    
    def _load_results(self):
        """載入歷史結果"""
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    self.results = json.load(f)
                logger.info(f"載入 {len(self.results)} 條歷史結果")
            except Exception as e:
                logger.warning(f"載入結果失敗: {e}")
                self.results = []
        else:
            self.results = []
    
    def _save_results(self):
        """保存結果到文件"""
        try:
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            logger.info(f"結果已保存到 {self.results_file}")
        except Exception as e:
            logger.error(f"保存結果失敗: {e}")
    
    def record_test(
        self,
        strategy_name: str,
        config_file: Optional[str],
        data_file: str,
        snapshot_file: Optional[str],
        result: Dict,
        notes: str = ""
    ):
        """
        記錄測試結果
        
        Args:
            strategy_name: 策略名稱
            config_file: 配置文件路徑
            data_file: 數據文件路徑
            snapshot_file: 快照文件路徑
            result: 回測結果字典
            notes: 備註
        """
        test_record = {
            "timestamp": datetime.now().isoformat(),
            "strategy_name": strategy_name,
            "config_file": config_file,
            "data_file": data_file,
            "snapshot_file": snapshot_file,
            "result": {
                "balance": float(result.get('balance', 0)),
                "position": float(result.get('position', 0)),
                "equity": float(result.get('equity', 0)),
                "pnl": float(result.get('pnl', 0)),
                "pnl_pct": float(result.get('pnl_pct', 0)),
                "elapsed_time": float(result.get('elapsed_time', 0)),
            },
            "notes": notes
        }
        
        self.results.append(test_record)
        self._save_results()
        logger.info(f"已記錄測試結果: {strategy_name} - PnL: {test_record['result']['pnl']:.2f}")
        
        return test_record
    
    def get_latest(self, strategy_name: Optional[str] = None) -> Optional[Dict]:
        """
        獲取最新的測試結果
        
        Args:
            strategy_name: 策略名稱（可選）
            
        Returns:
            最新的測試結果記錄
        """
        if strategy_name:
            filtered = [r for r in self.results if r['strategy_name'] == strategy_name]
            return filtered[-1] if filtered else None
        return self.results[-1] if self.results else None
    
    def compare_strategies(
        self,
        strategy1_name: str,
        strategy2_name: str,
        data_file: Optional[str] = None
    ) -> Dict:
        """
        比較兩個策略的結果
        
        Args:
            strategy1_name: 策略1名稱
            strategy2_name: 策略2名稱
            data_file: 數據文件（可選，用於過濾）
            
        Returns:
            比較結果字典
        """
        # 過濾結果
        filtered = self.results
        if data_file:
            filtered = [r for r in filtered if r['data_file'] == data_file]
        
        # 獲取每個策略的最新結果
        strategy1_results = [r for r in filtered if r['strategy_name'] == strategy1_name]
        strategy2_results = [r for r in filtered if r['strategy_name'] == strategy2_name]
        
        if not strategy1_results or not strategy2_results:
            logger.warning("無法找到足夠的結果進行比較")
            return {}
        
        # 使用最新的結果
        r1 = strategy1_results[-1]
        r2 = strategy2_results[-1]
        
        comparison = {
            "strategy1": {
                "name": strategy1_name,
                "pnl": r1['result']['pnl'],
                "pnl_pct": r1['result']['pnl_pct'],
                "equity": r1['result']['equity'],
                "timestamp": r1['timestamp']
            },
            "strategy2": {
                "name": strategy2_name,
                "pnl": r2['result']['pnl'],
                "pnl_pct": r2['result']['pnl_pct'],
                "equity": r2['result']['equity'],
                "timestamp": r2['timestamp']
            },
            "difference": {
                "pnl_diff": r2['result']['pnl'] - r1['result']['pnl'],
                "pnl_pct_diff": r2['result']['pnl_pct'] - r1['result']['pnl_pct'],
                "improvement_pct": ((r2['result']['pnl'] - r1['result']['pnl']) / abs(r1['result']['pnl']) * 100) if r1['result']['pnl'] != 0 else 0,
                "winner": strategy2_name if r2['result']['pnl'] > r1['result']['pnl'] else strategy1_name
            }
        }
        
        return comparison
    
    def get_history(self, strategy_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        獲取歷史記錄
        
        Args:
            strategy_name: 策略名稱（可選）
            limit: 返回數量限制
            
        Returns:
            歷史記錄列表
        """
        filtered = self.results
        if strategy_name:
            filtered = [r for r in filtered if r['strategy_name'] == strategy_name]
        
        return filtered[-limit:] if limit > 0 else filtered
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        生成測試報告
        
        Args:
            output_file: 輸出文件路徑（可選）
            
        Returns:
            報告內容
        """
        report_lines = [
            "# 測試結果報告",
            f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"總測試次數: {len(self.results)}",
            "",
            "## 測試歷史",
            ""
        ]
        
        # 按策略分組
        strategies = {}
        for result in self.results:
            name = result['strategy_name']
            if name not in strategies:
                strategies[name] = []
            strategies[name].append(result)
        
        for strategy_name, results in strategies.items():
            report_lines.append(f"### {strategy_name}")
            report_lines.append(f"測試次數: {len(results)}")
            report_lines.append("")
            report_lines.append("| 時間 | 數據集 | PnL | PnL % | Equity | 執行時間 |")
            report_lines.append("|------|--------|-----|-------|--------|----------|")
            
            for r in results[-10:]:  # 顯示最近10次
                data_name = Path(r['data_file']).stem
                report_lines.append(
                    f"| {r['timestamp'][:19]} | {data_name} | "
                    f"{r['result']['pnl']:+.2f} | {r['result']['pnl_pct']:+.2f}% | "
                    f"{r['result']['equity']:.2f} | {r['result']['elapsed_time']:.2f}s |"
                )
            report_lines.append("")
        
        # 策略對比
        if len(strategies) >= 2:
            report_lines.append("## 策略對比")
            report_lines.append("")
            
            strategy_names = list(strategies.keys())
            for i in range(len(strategy_names)):
                for j in range(i+1, len(strategy_names)):
                    comparison = self.compare_strategies(strategy_names[i], strategy_names[j])
                    if comparison:
                        report_lines.append(f"### {strategy_names[i]} vs {strategy_names[j]}")
                        report_lines.append("")
                        report_lines.append(f"- {strategy_names[i]}: PnL = {comparison['strategy1']['pnl']:+.2f}")
                        report_lines.append(f"- {strategy_names[j]}: PnL = {comparison['strategy2']['pnl']:+.2f}")
                        report_lines.append(f"- 差異: {comparison['difference']['pnl_diff']:+.2f}")
                        report_lines.append(f"- 改進: {comparison['difference']['improvement_pct']:+.2f}%")
                        report_lines.append(f"- 勝者: {comparison['difference']['winner']}")
                        report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"報告已保存到 {output_path}")
        
        return report_content


def run_test_with_recording(
    data_file: str,
    snapshot_file: Optional[str] = None,
    config_file: Optional[str] = None,
    strategy_name: str = "aggressive_mm",
    notes: str = "",
    visualize: bool = False
):
    """
    運行測試並自動記錄結果
    
    Args:
        data_file: 數據文件路徑
        snapshot_file: 快照文件路徑
        config_file: 配置文件路徑
        strategy_name: 策略名稱
        notes: 備註
        visualize: 是否顯示圖表
        
    Returns:
        測試結果記錄
    """
    manager = TestResultManager()
    
    logger.info(f"運行測試: {strategy_name}")
    logger.info(f"數據文件: {data_file}")
    
    try:
        # 運行回測
        result = run_backtest(
            data_file=data_file,
            snapshot_file=snapshot_file,
            visualize=visualize,
            save_report=False,
            config_file=config_file
        )
        
        # 記錄結果
        test_record = manager.record_test(
            strategy_name=strategy_name,
            config_file=config_file,
            data_file=data_file,
            snapshot_file=snapshot_file,
            result=result,
            notes=notes
        )
        
        logger.info(f"✅ 測試完成: PnL = {result['pnl']:+.2f}")
        
        return test_record
        
    except Exception as e:
        logger.error(f"測試失敗: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Result Manager')
    parser.add_argument('--data', required=True, help='Data file path')
    parser.add_argument('--snapshot', help='Snapshot file path')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--strategy', default='aggressive_mm', help='Strategy name')
    parser.add_argument('--notes', default='', help='Test notes')
    parser.add_argument('--report', action='store_true', help='Generate report')
    parser.add_argument('--compare', nargs=2, metavar=('STRATEGY1', 'STRATEGY2'), help='Compare two strategies')
    
    args = parser.parse_args()
    
    manager = TestResultManager()
    
    if args.compare:
        comparison = manager.compare_strategies(args.compare[0], args.compare[1])
        if comparison:
            print("\n" + "="*60)
            print("策略對比結果")
            print("="*60)
            print(f"{comparison['strategy1']['name']}: PnL = {comparison['strategy1']['pnl']:+.2f}")
            print(f"{comparison['strategy2']['name']}: PnL = {comparison['strategy2']['pnl']:+.2f}")
            print(f"差異: {comparison['difference']['pnl_diff']:+.2f}")
            print(f"改進: {comparison['difference']['improvement_pct']:+.2f}%")
            print(f"勝者: {comparison['difference']['winner']}")
    elif args.report:
        report = manager.generate_report("../docs/results/test_report.md")
        print(report)
    else:
        run_test_with_recording(
            data_file=args.data,
            snapshot_file=args.snapshot,
            config_file=args.config,
            strategy_name=args.strategy,
            notes=args.notes,
            visualize=False
        )

