# agents/product_review_agent_improved.py
# -*- coding: utf-8 -*-
"""產品評論代理人"""

import logging
import os
from typing import Dict, List, Optional
from .base_agent import BaseAgent, agent_registry

logger = logging.getLogger(__name__)


class ProductReviewAgent(BaseAgent):
    """產品評論代理人 - 使用 GPT 分析產品評價"""
    
    def __init__(self):
        super().__init__("ProductReview")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        logger.info("產品評論代理人初始化完成")
    
    def get_tools(self) -> List:
        return []
    
    def get_system_prompt(self) -> str:
        return """你是專業的產品評論分析師。
請根據用戶詢問的產品，提供：
1. 產品優點
2. 產品缺點
3. 適合人群
4. 購買建議
5. 價格參考範圍"""
    
    def _create_agent(self) -> None:
        return None
    
    def can_handle(self, message: str) -> bool:
        """判斷是否可以處理此訊息"""
        review_keywords = ['評價', '評論', '好不好', '值得買', '推不推', '心得', '開箱', '使用感想']
        return any(kw in message.lower() for kw in review_keywords)
    
    def _process_message_internal(self, user_id: str, message: str) -> str:
        return self.analyze_product(message)
    
    def analyze_product(self, query: str) -> str:
        """分析產品評價"""
        if not self.openai_api_key:
            return self._get_fallback_response(query)
        
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model=os.getenv("GPT_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": f"請分析這個產品的評價：{query}"}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"GPT 分析失敗: {e}")
            return self._get_fallback_response(query)
    
    def _get_fallback_response(self, query: str) -> str:
        """備用回應"""
        return f"""📦 **{query} 評價分析**

由於 AI 服務暫時不可用，以下是一般性建議：

💡 **購買建議**
• 先確認自己的需求和預算
• 比較不同平台的價格
• 查看官方規格和保固條款
• 參考網路上的開箱評測

🔍 **資訊來源建議**
• Mobile01 論壇
• PTT 相關版面
• YouTube 開箱影片
• 電商平台評論

如需更詳細的分析，請稍後再試！"""


# 註冊代理人
try:
    product_review_agent = ProductReviewAgent()
    agent_registry.register("ProductReview", product_review_agent)
    logger.info("✅ 產品評論代理人已註冊")
except Exception as e:
    logger.error(f"❌ 產品評論代理人註冊失敗: {e}")
