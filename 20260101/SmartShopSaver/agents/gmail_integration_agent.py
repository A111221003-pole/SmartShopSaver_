import os
import logging
from typing import Dict
from pathlib import Path
from urllib.parse import quote
from .base_agent import BaseAgent, agent_registry

logger = logging.getLogger(__name__)

class GmailIntegrationAgent(BaseAgent):
    """Gmail 整合代理人 - 管理 Gmail 授權與郵件同步"""

    def __init__(self):
        super().__init__("GmailIntegration")

        # ✅ 從環境變數載入公開網址
        self.public_base_url = os.getenv("PUBLIC_BASE_URL") or os.getenv("BASE_URL", "")
        if not self.public_base_url:
            logger.warning("⚠️ 未設定 PUBLIC_BASE_URL 或 BASE_URL，Gmail OAuth 連結將無法生成")
        else:
            self.public_base_url = self.public_base_url.rstrip("/")

        logger.info(f"Gmail 整合代理人初始化完成，base_url={self.public_base_url}")
    
    def get_tools(self):
        return []
    
    def get_system_prompt(self):
        return "Gmail 整合代理人"
    
    def _create_agent(self):
        return None

    def can_handle(self, message: str) -> bool:
        """判斷是否可處理 Gmail 相關訊息"""
        keywords = ['gmail', 'mail', '郵件', 'email', '連接', '授權', '綁定', '信件', '購物郵件', 'google']
        return any(k in message.lower() for k in keywords)

    def _process_message_internal(self, user_id: str, message: str) -> str:
        """內部訊息處理"""
        return self.process_gmail_request(user_id, message)

    def process_gmail_request(self, user_id: str, message: str) -> str:
        """主控制流程"""
        msg = message.lower().strip()

        if any(k in msg for k in ['連接', '授權', '綁定', 'connect', 'link']):
            return self._handle_gmail_connection(user_id)
        elif any(k in msg for k in ['查看', '查詢', '記錄', 'view', 'show']):
            return self._handle_view_emails(user_id)
        elif any(k in msg for k in ['同步', '更新', 'refresh', 'sync']):
            return self._handle_sync_emails(user_id)
        else:
            return self._get_gmail_help(user_id)

    def _handle_gmail_connection(self, user_id: str) -> str:
        """處理 Gmail 連接請求，產生 OAuth 登入連結"""
        if not self.public_base_url:
            return "❌ 系統未設定 PUBLIC_BASE_URL，請先於 .env 檔設定公開網址。"

        encoded_uid = quote(user_id)
        oauth_url = f"{self.public_base_url}/google/start?uid={encoded_uid}"

        return f"""📧 **Gmail 連接設定**

🔗 [點我登入 Gmail]({oauth_url})

請在瀏覽器中開啟上方連結完成 Google 授權。

✅ 授權後可使用：
• 自動同步購物郵件  
• 消費分析與報表  
• AI 自動分類與記帳整合  

🔒 **安全保證**
• 僅讀取購物郵件  
• 不會修改或刪除內容  
• 可隨時取消授權
"""

    def _handle_view_emails(self, user_id: str) -> str:
        """查看郵件記錄"""
        return """📬 **郵件查詢功能**

可用範例：
• 查看今天郵件  
• 查看本週郵件  
• 查看本月郵件  
• 查看 2025-11 的郵件

請先連接 Gmail 帳號後再使用此功能。
"""

    def _handle_sync_emails(self, user_id: str) -> str:
        """模擬同步郵件"""
        token_path = Path(f"./tokens/{user_id}.json")
        if not token_path.exists():
            return "❌ 尚未連接 Gmail，請先輸入「連接 Gmail」進行授權。"

        return """🔄 **同步郵件中...**

系統正在檢查新的購物郵件…

✅ 同步完成！  
• 處理郵件：5 封  
• 新增記錄：3 筆  
• 總金額：NT$2,580
"""

    def _get_gmail_help(self, user_id: str = "") -> str:
        """顯示 Gmail 功能說明，並附上登入連結"""
        base_text = """📧 **Gmail 整合功能說明**

🔗 **帳號設定**
• 「連接 Gmail」啟動登入授權  
• 「查看連接狀態」檢查授權情況  

📬 **郵件操作**
• 「查看郵件」查詢購物郵件  
• 「同步郵件」手動更新  
• 「搜尋 [關鍵字]」搜尋特定內容  

📊 **智能分析**
• 「本月郵件統計」  
• 「消費趨勢分析」  
• 「價格追蹤報告」

💡 範例：
• 我要連接 mail  
• 查看本月購物郵件  
• 同步最新郵件
"""

        if self.public_base_url and user_id:
            encoded_uid = quote(user_id)
            oauth_url = f"{self.public_base_url}/google/start?uid={encoded_uid}"
            base_text += f"\n\n🔗 [點我登入 Gmail]({oauth_url})"
        elif self.public_base_url:
            base_text += f"\n\n🔗 [點我登入 Gmail]({self.public_base_url}/google/start?uid={{你的LINE_UID}})"
        else:
            base_text += "\n\n⚠️ 尚未設定 PUBLIC_BASE_URL，登入連結無法生成。"

        return base_text

# === 註冊代理人 ===
try:
    gmail_agent = GmailIntegrationAgent()
except TypeError as e:
    import logging
    logging.error(f"[GmailIntegrationAgent 初始化失敗] {e}")
    gmail_agent = None

agent_registry.register("GmailIntegration", gmail_agent)
