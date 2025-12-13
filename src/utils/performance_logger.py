"""
Performance Logger
=================
記錄策略表現數據，用於後續分析
"""

import csv
import json
from datetime import datetime
from pathlib import Path


class PerformanceLogger:
    """記錄策略表現數據"""
    
    def __init__(self, log_dir='logs/trading'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # CSV log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_file = self.log_dir / f'performance_{timestamp}.csv'
        self.csv_writer = None
        self.csv_file_handle = None
        
        # JSON log file for detailed data
        self.json_file = self.log_dir / f'performance_{timestamp}.json'
        self.json_data = []
        
        self.setup_csv()
    
    def setup_csv(self):
        """設置 CSV 日誌文件"""
        self.csv_file_handle = open(self.csv_file, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file_handle)
        
        # Write header
        header = [
            'timestamp', 'mid_price', 'bid_price', 'ask_price', 'position',
            'mlofi', 'volatility', 'reservation_price', 'spread', 'skew',
            'balance', 'equity', 'pnl'
        ]
        self.csv_writer.writerow(header)
    
    def log(self, data):
        """
        記錄策略數據
        
        Args:
            data: dict containing strategy data
        """
        timestamp = datetime.now().isoformat()
        
        # CSV log
        row = [
            timestamp,
            data.get('mid_price', 0),
            data.get('bid_price', 0),
            data.get('ask_price', 0),
            data.get('position', 0),
            data.get('mlofi', 0),
            data.get('volatility', 0),
            data.get('reservation_price', 0),
            data.get('spread', 0),
            data.get('skew', 0),
            data.get('balance', 0),
            data.get('equity', 0),
            data.get('pnl', 0),
        ]
        self.csv_writer.writerow(row)
        self.csv_file_handle.flush()
        
        # JSON log (detailed)
        json_entry = {
            'timestamp': timestamp,
            **data
        }
        self.json_data.append(json_entry)
    
    def save_json(self):
        """保存 JSON 日誌文件"""
        try:
            with open(self.json_file, 'w') as f:
                json.dump(self.json_data, f, indent=2)
        except Exception:
            pass  # Silently fail if file is already closed
    
    def close(self):
        """關閉日誌文件"""
        if self.csv_file_handle:
            self.csv_file_handle.close()
        self.save_json()
    
    def __del__(self):
        """析構函數，確保文件關閉"""
        self.close()

