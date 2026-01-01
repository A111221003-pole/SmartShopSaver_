# logger.py - 統一日誌管理工具
import logging
import os
from datetime import datetime
from typing import Optional

class Logger:
    """統一日誌管理類別"""
    
    _instances = {}
    
    @classmethod
    def get_logger(cls, name: str, level: int = logging.INFO, 
                   log_file: Optional[str] = None) -> logging.Logger:
        """
        獲取或創建日誌記錄器
        
        Args:
            name: 日誌記錄器名稱
            level: 日誌級別
            log_file: 日誌文件路徑（可選）
            
        Returns:
            配置好的日誌記錄器
        """
        if name not in cls._instances:
            logger = logging.getLogger(name)
            logger.setLevel(level)
            
            # 如果還沒有處理器，添加處理器
            if not logger.handlers:
                # 控制台處理器
                console_handler = logging.StreamHandler()
                console_handler.setLevel(level)
                
                # 格式化器
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
                
                # 文件處理器（如果指定了文件路徑）
                if log_file:
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
                    file_handler = logging.FileHandler(log_file, encoding='utf-8')
                    file_handler.setLevel(level)
                    file_handler.setFormatter(formatter)
                    logger.addHandler(file_handler)
            
            cls._instances[name] = logger
        
        return cls._instances[name]

    @staticmethod
    def setup_basic_logging(level: int = logging.INFO):
        """設定基本日誌配置"""
        os.makedirs("logs", exist_ok=True)
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    f"logs/smartshopsaver_{datetime.now().strftime('%Y%m%d')}.log",
                    encoding='utf-8'
                )
            ]
        )
