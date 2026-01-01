# finance_agent.py - 財務助理代理人（修復上個月查詢）
import logging
import re
from typing import Dict, Optional, List
from smolagents import tool, CodeAgent
from agents.base_agent import BaseAgent, agent_registry
from utils.database import get_db_manager

logger = logging.getLogger(__name__)

@tool
def get_financial_summary(user_id: str, question: str) -> str:
    """
    根據使用者的財務資料回答問題。

    Args:
        user_id (str): 使用者 ID
        question (str): 使用者輸入的財務問題
    
    Returns:
        str: 自然語言的回答內容
    """
    try:
        db = get_db_manager()
        
        # 判斷是查詢這個月還是上個月
        is_last_month = any(keyword in question for keyword in ['上個月', '上月', '前一個月', '前個月'])
        
        # 根據查詢類型獲取資料
        if is_last_month:
            data = db.get_user_finance_summary(user_id, last_month=True)
            month_text = "上個月"
        else:
            data = db.get_user_finance_summary(user_id, last_month=False)
            month_text = "本月"
        
        if not data:
            return f"⚠️ 您在{month_text}還沒有任何消費記錄。"

        total = data["total_spending"]
        budget = data["budget"]
        categories = data["categories"]
        
        # 格式化分類花費
        category_text = ""
        if categories:
            for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                category_text += f"\n• {cat}：NT${amt:,}"
        
        # 構建回應
        if budget > 0:
            status = "✅ 尚未超支" if total <= budget else f"⚠️ 已超支 NT${total - budget:,}"
            response = (
                f"💰 財務摘要\n\n"
                f"📊 {month_text}總花費：NT${total:,}\n"
                f"💵 {month_text}預算：NT${budget:,}\n"
                f"{status}\n\n"
                f"📂 分類花費：{category_text if category_text else '暫無記錄'}\n\n"
                f"💡 {('繼續保持！' if total <= budget else '建議減少非必要開支')}"
            )
        else:
            # 如果沒有設定預算
            response = (
                f"💰 財務摘要\n\n"
                f"📊 {month_text}總花費：NT${total:,}\n"
                f"💵 {month_text}預算：NT$0（未設定）\n\n"
                f"📂 分類花費：{category_text if category_text else '暫無記錄'}\n\n"
                f"💡 建議設定預算以便更好地管理財務！"
            )
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"財務摘要查詢失敗: {e}", exc_info=True)
        return "⚠️ 抱歉，我無法取得您的財務資料，請稍後再試。"

@tool
def add_expense(user_id: str, amount: float, category: str, description: str = "") -> str:
    """
    新增支出記錄
    
    Args:
        user_id: 使用者ID
        amount: 金額
        category: 分類（如：飲食、交通、娛樂等）
        description: 描述
    
    Returns:
        str: 新增結果訊息
    """
    try:
        db = get_db_manager()
        success = db.add_user_expense(user_id, amount, category, description)
        
        if success:
            return f"✅ 已記錄支出：NT${amount:,} ({category})"
        else:
            return "❌ 記錄支出失敗，請稍後再試"
            
    except Exception as e:
        logger.error(f"新增支出失敗: {e}")
        return "❌ 系統錯誤，請稍後再試"

@tool
def set_budget(user_id: str, budget: float) -> str:
    """
    設定月預算
    
    Args:
        user_id: 使用者ID
        budget: 預算金額
    
    Returns:
        str: 設定結果訊息
    """
    try:
        db = get_db_manager()
        success = db.set_user_budget(user_id, budget)
        
        if success:
            return f"✅ 已設定本月預算為 NT${budget:,}"
        else:
            return "❌ 設定預算失敗，請稍後再試"
            
    except Exception as e:
        logger.error(f"設定預算失敗: {e}")
        return "❌ 系統錯誤，請稍後再試"

class FinanceAgent(BaseAgent):
    """財務助理代理人 - 負責記帳、預算管理和財務諮詢"""
    
    def __init__(self):
        super().__init__(agent_name="FinanceAgent")
    
    def get_tools(self) -> List:
        """獲取財務相關工具"""
        return [get_financial_summary, add_expense, set_budget]
    
    def get_system_prompt(self) -> str:
        """獲取系統提示詞"""
        return """你是財務助理代理人，負責幫助用戶管理個人財務。

你的職責：
1. 提供財務摘要和支出統計（支持查詢「這個月」和「上個月」）
2. 記錄用戶的支出
3. 管理預算設定
4. 提供理財建議

回應原則：
- 使用友善、專業的語氣
- 提供清晰的財務資訊
- 使用表情符號增加可讀性
- 適時提供理財建議

重要：你只處理財務相關的請求。如果用戶詢問商品評價、價格等非財務問題，請禮貌地告知這不是你的專業範圍。"""
    
    def _create_agent(self) -> CodeAgent:
        """創建代理人實例"""
        if self.model:
            return CodeAgent(
                tools=self.get_tools(),
                model=self.model,
                additional_authorized_imports=["re", "json"]
            )
        return None
    
    def can_handle(self, message: str) -> bool:
        """判斷是否可以處理此訊息"""
        finance_keywords = [
            '財務', '記帳', '支出', '花費', '預算', '超支',
            '花了多少', '這個月', '本月', '上個月', '上月', '開銷',
            '省錢', '存錢', '理財', '帳單', '設定預算'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in finance_keywords)
    
    def _process_message_internal(self, user_id: str, message: str) -> str:
        """處理用戶訊息"""
        try:
            logger.info(f"💵 財務代理人處理: {message}")
            
            # 使用 CodeAgent 處理
            if self.agent:
                result = self.agent.run(
                    f"""用戶ID: {user_id}
用戶訊息: {message}

請分析用戶需求並使用適當的工具處理。
- 如果用戶要記帳，請識別金額和分類
- 如果用戶查詢消費，請調用 get_financial_summary，並將完整的問題傳入 question 參數
- 注意：question 參數很重要，用於判斷是查詢「這個月」還是「上個月」"""
                )
                return str(result)
            else:
                return self._fallback_process(user_id, message)
            
        except Exception as e:
            logger.error(f"財務代理人處理失敗: {e}", exc_info=True)
            return "❌ 處理您的財務請求時發生錯誤，請稍後再試"
    
    def _fallback_process(self, user_id: str, message: str) -> str:
        """備用處理邏輯"""
        message_lower = message.lower()
        
        # 記帳
        amount_match = re.search(r'(\d+)', message)
        if amount_match and any(kw in message_lower for kw in ['記帳', '記錄', '花了', '花費']):
            amount = float(amount_match.group(1))
            category = "其他"
            if '午餐' in message_lower or '早餐' in message_lower or '晚餐' in message_lower or '吃' in message_lower:
                category = "飲食"
            elif '交通' in message_lower or '車' in message_lower or '油' in message_lower:
                category = "交通"
            elif '娛樂' in message_lower or '電影' in message_lower or '遊戲' in message_lower:
                category = "娛樂"
            return add_expense(user_id, amount, category, "")
        
        # 查詢
        if any(kw in message_lower for kw in ['多少', '統計', '花費', '支出']):
            return get_financial_summary(user_id, message)
        
        # 設定預算
        if '預算' in message_lower:
            if amount_match:
                budget = float(amount_match.group(1))
                return set_budget(user_id, budget)
        
        return get_financial_summary(user_id, message)

# 創建財務代理人實例
try:
    finance_agent = FinanceAgent()
    agent_registry.register("FinanceAgent", finance_agent)
    logger.info("✅ 財務助理代理人已註冊")
except Exception as e:
    logger.error(f"❌ 財務助理代理人初始化失敗: {e}")
    finance_agent = None
