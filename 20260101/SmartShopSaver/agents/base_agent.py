# agents/base_agent.py - 基礎代理人類別
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
import os

# 處理可選套件
try:
    from smolagents import CodeAgent, LiteLLMModel
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    CodeAgent = None
    LiteLLMModel = None
    logging.warning("smolagents 未安裝，部分功能可能受限")

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """基礎代理人抽象類別"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(agent_name)
        self.model = self._create_model()
        self.agent = self._create_agent()
        self.logger.info(f"{agent_name} 代理人初始化完成")
    
    def _create_model(self):
        """創建語言模型"""
        if SMOLAGENTS_AVAILABLE and LiteLLMModel:
            return LiteLLMModel(
                model_id="gpt-4o-mini",
                api_key=os.getenv('OPENAI_API_KEY')
            )
        else:
            # 返回 None 或一個簡單的替代實現
            return None
    
    @abstractmethod
    def _create_agent(self):
        """創建代理人實例（子類別必須實作）"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """獲取代理人工具（子類別必須實作）"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """獲取系統提示詞（子類別必須實作）"""
        pass
    
    def process_message(self, user_id: str, message: str) -> str:
        """
        處理用戶訊息的統一介面
        
        Args:
            user_id: 用戶ID
            message: 用戶訊息
            
        Returns:
            處理結果
        """
        try:
            self.logger.info(f"收到用戶 {user_id} 的訊息: {message}")
            
            # 調用子類別的具體處理邏輯
            result = self._process_message_internal(user_id, message)
            
            self.logger.info(f"處理完成，回應長度: {len(str(result))}")
            return str(result)
            
        except Exception as e:
            error_msg = f"{self.agent_name} 處理失敗: {e}"
            self.logger.error(error_msg, exc_info=True)
            return f"❌ {self.agent_name} 暫時無法使用，請稍後再試"
    
    @abstractmethod
    def _process_message_internal(self, user_id: str, message: str) -> str:
        """內部訊息處理邏輯（子類別必須實作）"""
        pass
    
    def validate_input(self, message: str) -> bool:
        """
        驗證輸入訊息
        
        Args:
            message: 用戶訊息
            
        Returns:
            是否有效
        """
        if not message or not message.strip():
            return False
        
        if len(message) > 1000:  # 限制輸入長度
            return False
        
        return True
    
    def format_response(self, response: str) -> str:
        """
        格式化回應訊息
        
        Args:
            response: 原始回應
            
        Returns:
            格式化後的回應
        """
        if not response:
            return "抱歉，無法處理您的請求"
        
        # 限制回應長度
        if len(response) > 5000:
            response = response[:4900] + "\n\n⚠️ 回應內容過長已截斷"
        
        return response.strip()
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        獲取代理人資訊
        
        Returns:
            代理人資訊字典
        """
        return {
            'name': self.agent_name,
            'model': "gpt-4o-mini",
            'tools_count': len(self.get_tools()),
            'status': 'active'
        }

class AgentRegistry:
    """代理人註冊管理器"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger('AgentRegistry')
    
    def register(self, agent_name: str, agent: BaseAgent):
        """註冊代理人"""
        self._agents[agent_name] = agent
        self.logger.info(f"註冊代理人: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """獲取代理人"""
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """列出所有代理人"""
        return list(self._agents.keys())
    
    def get_all_agents_info(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有代理人資訊"""
        return {
            name: agent.get_agent_info() 
            for name, agent in self._agents.items()
        }

# 全域代理人註冊器
agent_registry = AgentRegistry()
