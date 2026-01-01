# config.py - 配置管理工具
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SmartShopSaverConfig:
    """SmartShopSaver 配置類別"""
    # LINE Bot 設定
    line_channel_access_token: str
    line_channel_secret: str
    
    # OpenAI 設定
    openai_api_key: str
    
    # 應用設定
    app_host: str = "0.0.0.0"
    app_port: int = 5000
    app_debug: bool = False
    
    # 資料存儲設定
    data_dir: str = "data"
    
    @classmethod
    def from_env(cls) -> 'SmartShopSaverConfig':
        """從環境變數創建配置"""
        return cls(
            line_channel_access_token=os.getenv('CHANNEL_ACCESS_TOKEN', ''),
            line_channel_secret=os.getenv('CHANNEL_SECRET', ''),
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            app_host=os.getenv('APP_HOST', '0.0.0.0'),
            app_port=int(os.getenv('APP_PORT', '5000')),
            app_debug=os.getenv('APP_DEBUG', 'False').lower() == 'true',
            data_dir=os.getenv('DATA_DIR', 'data')
        )
    
    @classmethod
    def from_file(cls, config_file: str) -> 'SmartShopSaverConfig':
        """從配置文件創建配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'line_channel_access_token': self.line_channel_access_token,
            'line_channel_secret': self.line_channel_secret,
            'openai_api_key': self.openai_api_key,
            'app_host': self.app_host,
            'app_port': self.app_port,
            'app_debug': self.app_debug,
            'data_dir': self.data_dir
        }
    
    def save_to_file(self, config_file: str):
        """保存到配置文件"""
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

class ConfigManager:
    """配置管理器"""
    
    _config: Optional[SmartShopSaverConfig] = None
    
    @classmethod
    def get_config(cls) -> SmartShopSaverConfig:
        """獲取配置"""
        if cls._config is None:
            # 優先從配置文件讀取，其次從環境變數
            config_file = "config/config.json"
            if os.path.exists(config_file):
                cls._config = SmartShopSaverConfig.from_file(config_file)
            else:
                cls._config = SmartShopSaverConfig.from_env()
        
        return cls._config
    
    @classmethod
    def set_config(cls, config: SmartShopSaverConfig):
        """設定配置"""
        cls._config = config
    
    @classmethod
    def reload_config(cls):
        """重新載入配置"""
        cls._config = None
        return cls.get_config()
