# agents/smart_recommendation_agent.py
# -*- coding: utf-8 -*-
"""智能推薦代理人"""

import logging
import os
from typing import Dict, List, Optional
from .base_agent import BaseAgent, agent_registry

logger = logging.getLogger(__name__)


class SmartRecommendationAgent(BaseAgent):
    """智能推薦代理人 - 使用 GPT 提供購物建議"""
    
    def __init__(self):
        super().__init__("SmartRecommendation")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        logger.info("智能推薦代理人初始化完成")
    
    def get_tools(self) -> List:
        return []
    
    def get_system_prompt(self) -> str:
        return """你是專業的購物顧問，專精於3C產品、家電和各類消費品。
請根據用戶的需求和預算，提供：
1. 3-5 個具體的產品推薦（包含品牌、型號、大約價格）
2. 每個產品的優缺點
3. 最適合的使用情境
4. 購買建議和注意事項"""
    
    def _create_agent(self) -> None:
        return None
    
    def can_handle(self, message: str) -> bool:
        """判斷是否可以處理此訊息"""
        keywords = ['推薦', '建議', '哪個好', '選擇', '比較', '該買', '想買']
        return any(kw in message.lower() for kw in keywords)
    
    def _process_message_internal(self, user_id: str, message: str) -> str:
        return self.get_recommendation(message)
    
    def get_recommendation(self, query: str) -> str:
        """取得產品推薦"""
        if not self.openai_api_key:
            return self._get_fallback_response(query)
        
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model=os.getenv("GPT_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": query}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"GPT 推薦失敗: {e}")
            return self._get_fallback_response(query)
    
    def _get_fallback_response(self, query: str) -> str:
        """備用回應"""
        return f"""🎯 **購物建議**

關於「{query}」，以下是一般性建議：

💡 **選購要點**
1. 先確認自己的實際需求
2. 設定合理的預算範圍
3. 比較不同品牌的規格和價格
4. 查看用戶評論和專業評測

🔍 **推薦資訊來源**
• 電商平台比價
• Mobile01 討論區
• PTT 相關版面
• YouTube 評測影片

📱 **下一步**
輸入更具體的需求（如預算、用途），我可以提供更精準的建議！

如需 AI 智能推薦，請確認 OpenAI API Key 已正確設定。"""


# 註冊代理人
try:
    smart_recommendation_agent = SmartRecommendationAgent()
    agent_registry.register("SmartRecommendation", smart_recommendation_agent)
    logger.info("✅ 智能推薦代理人已註冊")
except Exception as e:
    logger.error(f"❌ 智能推薦代理人註冊失敗: {e}")
