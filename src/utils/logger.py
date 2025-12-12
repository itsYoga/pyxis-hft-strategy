"""
Logging Module
==============
統一的日誌系統
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO",
    console: bool = True,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    設置日誌系統
    
    Args:
        name: Logger 名稱
        log_file: 日誌檔案路徑（可選）
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR)
        console: 是否輸出到控制台
        format_string: 自訂格式字串
        
    Returns:
        配置好的 Logger 實例
    """
    logger = logging.getLogger(name)
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 設置日誌級別
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 預設格式
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # 控制台輸出
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 檔案輸出
    if log_file:
        log_path = Path(log_file)
        # 建立目錄
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    獲取 Logger（如果不存在則建立預設的）
    
    Args:
        name: Logger 名稱
        
    Returns:
        Logger 實例
    """
    logger = logging.getLogger(name)
    
    # 如果還沒有配置，使用預設配置
    if not logger.handlers:
        setup_logger(name)
    
    return logger

