# -*- coding: utf-8 -*-
"""
Gmail 整合代理人 - MongoDB 版本
整合所有 mail_1027 的子代理人功能
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# 加入路徑
current_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(current_dir))

logger = logging.getLogger(__name__)

# 匯入 MongoDB 適配器
from utils.mail_utils.mongodb_adapter import get_db_manager

# 嘗試匯入 Gmail 工具
try:
    from utils.mail_utils.gmail_utils import (
        GmailShoppingTracker,
        start_google_oauth,
        finish_google_oauth,
        has_token,
        build_gmail_service
    )
    GMAIL_UTILS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Gmail utils 匯入失敗: {e}")
    GMAIL_UTILS_AVAILABLE = False

# 嘗試匯入子代理人
try:
    from agents.mail_agents.expense_agent import category_stats_30d
    from agents.mail_agents.purchase_query_agent import query_and_analyze
    from agents.mail_agents.gmail_agent import GmailAgent as OriginalGmailAgent
    MAIL_AGENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Mail agents 匯入失敗: {e}")
    MAIL_AGENTS_AVAILABLE = False
    category_stats_30d = None
    query_and_analyze = None
    OriginalGmailAgent = None

from agents.base_agent import BaseAgent, agent_registry


class GmailIntegrationAgent(BaseAgent):
    """Gmail 整合代理人 - 統整所有子代理人功能"""
    
    def __init__(self):
        super().__init__("GmailIntegration")
        
        # 使用 MongoDB
        try:
            self.db = get_db_manager()
            self.db_connected = True
            logger.info("MongoDB 連接成功")
        except Exception as e:
            logger.warning(f"MongoDB 連接失敗: {e}")
            self.db = None
            self.db_connected = False
        
        # 初始化子代理人
        self.sub_agents = {}
        if MAIL_AGENTS_AVAILABLE and OriginalGmailAgent:
            try:
                self.sub_agents["gmail"] = OriginalGmailAgent(
                    user_id="default",
                    service=None
                )
                logger.info("Gmail 子代理人初始化成功")
            except Exception as e:
                logger.warning(f"Gmail 子代理人初始化失敗: {e}")
        
        self.tokens_dir = Path("mail_module/tokens")
        self.tokens_dir.mkdir(parents=True, exist_ok=True)
        
        # 新增 BASE_URL（用於顯示 OAuth 連結）
        self.public_base_url = os.getenv("BASE_URL") or os.getenv("PUBLIC_BASE_URL", "")
        if not self.public_base_url:
            logger.warning("⚠️ 未設定 BASE_URL 或 PUBLIC_BASE_URL，OAuth 連結將無法生成")
        else:
            self.public_base_url = self.public_base_url.rstrip("/")
        
        logger.info("Gmail 整合代理人初始化完成")
    
    def get_tools(self) -> List:
        return []
    
    def get_system_prompt(self) -> str:
        return """你是 Gmail 整合專家，可以幫助用戶：
1. 連結 Gmail 帳號 (OAuth 授權)
2. 掃描和識別購物郵件
3. 自動記帳到 MongoDB
4. 查詢消費記錄
5. 生成統計報表
6. 管理支出分類"""
    
    def _create_agent(self):
        return None
    
    def can_handle(self, message: str) -> bool:
        """判斷是否可以處理此訊息"""
        gmail_keywords = [
            "gmail", "郵件", "email", "信件", "收據", "發票",
            "自動記帳", "購物記錄", "消費記錄", "掃描郵件",
            "支出", "統計", "報表", "消費統計", "消費查詢"
        ]
        return any(kw in message.lower() for kw in gmail_keywords)
    
    def _process_message_internal(self, user_id: str, message: str) -> str:
        """處理訊息 - 路由到適當的子代理人"""
        
        if not self.db_connected:
            return "❌ 資料庫未連接，請檢查 MongoDB 設定"
        
        message_lower = message.lower()
        
        # 路由邏輯
        if "連結" in message_lower or "授權" in message_lower:
            return self._handle_oauth(user_id)
        
        elif "掃描" in message_lower or "同步" in message_lower:
            return self._handle_scan(user_id, message)
        
        elif "查詢" in message_lower or "查看" in message_lower or "記錄" in message_lower:
            return self._handle_query(user_id, message)
        
        elif "統計" in message_lower or "分析" in message_lower or "報表" in message_lower:
            return self._handle_stats(user_id, message)
        
        elif "支出" in message_lower or "消費" in message_lower:
            return self._handle_expense(user_id, message)
        
        else:
            return self._get_help(user_id)
    
    def _handle_oauth(self, user_id: str):
        """處理 OAuth 授權"""
        if not GMAIL_UTILS_AVAILABLE:
            return "❌ Gmail 功能未正確安裝"
    
        if has_token(user_id):
            return "✅ Gmail 已連結！可以開始使用了"
    
        base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
        if not base_url:
            return "❌ 請先在 .env 設定 PUBLIC_BASE_URL"
    
        redirect_uri = f"{base_url}/google/callback"
    
        try:
            auth_url, _ = start_google_oauth(user_id, redirect_uri)
            return f"""📧 **Gmail 授權設定**

🔗 [點我登入 Gmail]({auth_url})

授權後可使用：
✅ 自動掃描購物郵件  
✅ AI 識別收據  
✅ 自動記帳到 MongoDB  
✅ 生成消費統計"""
        except Exception as e:
            return f"❌ 建立授權連結失敗: {e}"
    
    def _handle_scan(self, user_id: str, message: str):
        """處理掃描郵件"""
        if not GMAIL_UTILS_AVAILABLE:
            return "❌ Gmail 功能未安裝"
        
        if not has_token(user_id):
            return "❌ 請先連結 Gmail (輸入：連結 Gmail)"
        
        days = 30
        if "7" in message or "七" in message or "週" in message:
            days = 7
        elif "14" in message:
            days = 14
        elif "30" in message or "月" in message:
            days = 30
        
        try:
            tracker = GmailShoppingTracker(user_id, self.db)
            result = tracker.process_recent_emails(days=days, force=True)
            
            return f"""✅ 掃描完成！

📊 掃描結果：
• 檢查郵件：{result.get("total_emails", 0)} 封
• 購物記錄：{result.get("shopping_records", 0)} 筆
• 總金額：NT$ {result.get("total_amount", 0):,.0f}
• AI 分析：{result.get("gpt_analyzed", 0)} 筆
• 自動記帳：{result.get("auto_recorded", 0)} 筆

💾 資料已儲存到 MongoDB"""
            
        except Exception as e:
            logger.error(f"掃描失敗: {e}")
            return f"❌ 掃描失敗：{str(e)}"
    
    def _handle_query(self, user_id: str, message: str):
        """處理查詢"""
        if query_and_analyze:
            try:
                return query_and_analyze(user_id, message, self.db)
            except Exception as e:
                logger.error(f"查詢失敗: {e}")
                return f"❌ 查詢失敗：{str(e)}"
        else:
            return self._simple_query(user_id, message)
    
    def _handle_stats(self, user_id: str, message: str):
        """處理統計"""
        if category_stats_30d:
            try:
                return category_stats_30d(user_id, self.db)
            except Exception as e:
                logger.error(f"統計失敗: {e}")
                return f"❌ 統計失敗：{str(e)}"
        else:
            return "📊 統計功能開發中..."
    
    def _handle_expense(self, user_id: str, message: str):
        """處理支出"""
        if "gmail" in self.sub_agents:
            return self.sub_agents["gmail"].process_emails_in_range(
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                force=False
            )
        else:
            return "💰 支出管理功能開發中..."
    
    def _simple_query(self, user_id: str, message: str):
        """簡單查詢"""
        try:
            records = self.db.list_shopping_records(
                user_id,
                datetime.now() - timedelta(days=7),
                datetime.now(),
                limit=5
            )
            
            if not records:
                return "📭 最近沒有購物記錄"
            
            result = "📊 最近的購物記錄：\n\n"
            for i, record in enumerate(records, 1):
                result += f"{i}. {record.get('vendor', '未知')}\n"
                result += f"   💰 NT$ {record.get('amount', 0):,.0f}\n"
                result += f"   📅 {record.get('email_date', '')}\n\n"
            return result
        except Exception as e:
            logger.error(f"查詢失敗: {e}")
            return "❌ 查詢失敗"
    
    def _get_help(self, user_id: str = ""):
        """幫助訊息，附上登入 Gmail 按鈕"""
        text = """📧 Gmail 整合功能

🔗 **連結帳號**
• 「連結 Gmail」- OAuth 授權

📥 **郵件處理**
• 「掃描郵件」- 同步最新郵件
• 「掃描最近7天」- 指定天數

📊 **查詢功能**
• 「查看購物記錄」- 最近消費
• 「本月消費」- 當月統計

📈 **統計分析**
• 「消費統計」- 分類統計
• 「支出報表」- 詳細報表

💡 提示：所有資料儲存在 MongoDB"""

        if self.public_base_url:
            oauth_url = f"{self.public_base_url}/google/start?uid={user_id or '{YOUR_LINE_UID}'}"
            text += f"\n\n🔗 [點我登入 Gmail]({oauth_url})"
        else:
            text += "\n\n⚠️ 尚未設定 BASE_URL，登入連結無法生成。"

        return text


# 建立並註冊代理人
gmail_integration_agent = GmailIntegrationAgent()

try:
    agent_registry.register("GmailIntegration", gmail_integration_agent)
    logger.info("✅ Gmail 整合代理人已註冊成功")
except Exception as e:
    logger.error(f"❌ 註冊 Gmail 整合代理人失敗: {e}")
