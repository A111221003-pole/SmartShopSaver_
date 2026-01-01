# utils/mail_utils/gmail_utils.py
# -*- coding: utf-8 -*-
"""Gmail OAuth 和郵件處理工具"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Token 存儲目錄
TOKENS_DIR = Path("tokens")
TOKENS_DIR.mkdir(exist_ok=True)


def has_token(user_id: str) -> bool:
    """檢查用戶是否有有效的 OAuth token"""
    token_path = TOKENS_DIR / f"{user_id}.json"
    return token_path.exists()


def get_token_path(user_id: str) -> Path:
    """取得用戶 token 檔案路徑"""
    return TOKENS_DIR / f"{user_id}.json"


def start_google_oauth(user_id: str, redirect_uri: str) -> Tuple[str, str]:
    """
    開始 Google OAuth 流程
    
    Args:
        user_id: LINE 用戶 ID
        redirect_uri: OAuth 回調 URI
        
    Returns:
        (auth_url, state) 元組
    """
    try:
        from google_auth_oauthlib.flow import Flow
        
        client_secret_path = os.getenv("GMAIL_CLIENT_SECRET", "client_secret.json")
        
        if not os.path.exists(client_secret_path):
            raise FileNotFoundError(f"找不到 {client_secret_path}")
        
        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/userinfo.email"
        ]
        
        flow = Flow.from_client_secrets_file(
            client_secret_path,
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        
        # 設定 state 為用戶 ID
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=user_id,
            prompt="consent"
        )
        
        return auth_url, state
        
    except ImportError:
        logger.error("請安裝 google-auth-oauthlib: pip install google-auth-oauthlib")
        raise
    except Exception as e:
        logger.error(f"建立 OAuth 連結失敗: {e}")
        raise


def finish_google_oauth(code: str, redirect_uri: str, user_id: str) -> bool:
    """
    完成 Google OAuth 流程
    
    Args:
        code: OAuth 授權碼
        redirect_uri: OAuth 回調 URI
        user_id: LINE 用戶 ID
        
    Returns:
        是否成功
    """
    try:
        from google_auth_oauthlib.flow import Flow
        
        client_secret_path = os.getenv("GMAIL_CLIENT_SECRET", "client_secret.json")
        
        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/userinfo.email"
        ]
        
        flow = Flow.from_client_secrets_file(
            client_secret_path,
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # 儲存 token
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "created_at": datetime.now().isoformat()
        }
        
        token_path = get_token_path(user_id)
        with open(token_path, "w") as f:
            json.dump(token_data, f)
        
        logger.info(f"OAuth token 已儲存: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"完成 OAuth 失敗: {e}")
        return False


def build_gmail_service(user_id: str):
    """
    建立 Gmail API 服務
    
    Args:
        user_id: LINE 用戶 ID
        
    Returns:
        Gmail API service 物件
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        token_path = get_token_path(user_id)
        
        if not token_path.exists():
            raise FileNotFoundError(f"找不到用戶 {user_id} 的 token")
        
        with open(token_path) as f:
            token_data = json.load(f)
        
        credentials = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes")
        )
        
        service = build("gmail", "v1", credentials=credentials)
        return service
        
    except ImportError:
        logger.error("請安裝 google-api-python-client: pip install google-api-python-client")
        raise
    except Exception as e:
        logger.error(f"建立 Gmail 服務失敗: {e}")
        raise


class GmailShoppingTracker:
    """Gmail 購物郵件追蹤器"""
    
    def __init__(self, user_id: str, db=None):
        self.user_id = user_id
        self.db = db
        self.service = None
        
        if has_token(user_id):
            try:
                self.service = build_gmail_service(user_id)
            except Exception as e:
                logger.error(f"建立 Gmail 服務失敗: {e}")
    
    def process_recent_emails(self, days: int = 30, force: bool = False) -> Dict:
        """
        處理最近的購物郵件
        
        Args:
            days: 處理最近幾天的郵件
            force: 是否強制重新處理
            
        Returns:
            處理結果統計
        """
        result = {
            "total_emails": 0,
            "shopping_records": 0,
            "total_amount": 0,
            "gpt_analyzed": 0,
            "auto_recorded": 0
        }
        
        if not self.service:
            logger.warning("Gmail 服務未連接")
            return result
        
        try:
            # 搜尋購物相關郵件
            query = "subject:(訂單 OR 收據 OR 發票 OR 付款 OR 購買)"
            messages = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=100
            ).execute()
            
            items = messages.get("messages", [])
            result["total_emails"] = len(items)
            
            logger.info(f"找到 {len(items)} 封可能的購物郵件")
            
            # 這裡可以進一步處理每封郵件
            # 實際實作時會解析郵件內容並用 GPT 分析
            
            return result
            
        except Exception as e:
            logger.error(f"處理郵件失敗: {e}")
            return result
