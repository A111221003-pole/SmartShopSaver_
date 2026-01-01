# -*- coding: utf-8 -*-
"""
MongoDB 適配器 - 將 PostgreSQL 操作轉換為 MongoDB
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB 版本的資料庫管理器，相容 mail_1027 的介面"""
    
    def __init__(self):
        # 從環境變數取得 MongoDB 連接
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError("請設定 MONGODB_URI 環境變數")
        
        self.client = MongoClient(mongodb_uri)
        self.db = self.client.smartshopsaver
        
        # 建立集合
        self.shopping_records = self.db.shopping_records
        self.gmail_processed = self.db.gmail_processed
        self.expenses = self.db.expenses
        self.users = self.db.users
        
        # 建立索引
        self._create_indexes()
        
        logger.info("MongoDB 適配器初始化完成")
    
    def _create_indexes(self):
        """建立索引"""
        # 購物記錄索引
        self.shopping_records.create_index([
            ("user_id", ASCENDING),
            ("message_id", ASCENDING)
        ], unique=True)
        
        # Gmail 處理記錄索引
        self.gmail_processed.create_index([
            ("user_id", ASCENDING),
            ("message_id", ASCENDING)
        ], unique=True)
        
        # 支出記錄索引
        self.expenses.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
    
    def has_processed_message(self, user_id: str, message_id: str) -> bool:
        """檢查郵件是否已處理"""
        result = self.gmail_processed.find_one({
            "user_id": user_id,
            "message_id": message_id
        })
        return result is not None
    
    def mark_message_processed(self, user_id: str, message_id: str, 
                               subject: str = "", email_date: Any = None):
        """標記郵件為已處理"""
        self.gmail_processed.update_one(
            {"user_id": user_id, "message_id": message_id},
            {"$set": {
                "user_id": user_id,
                "message_id": message_id,
                "subject": subject,
                "email_date": email_date,
                "processed_at": datetime.now()
            }},
            upsert=True
        )
    
    def insert_or_update_shopping_record(self, user_id: str, message_id: str,
                                        vendor: str, amount: float,
                                        category: str, email_date: Any,
                                        subject: str = "", snippet: str = "",
                                        confidence: float = 0.5,
                                        raw_source: str = "GMAIL",
                                        **kwargs) -> str:
        """插入或更新購物記錄"""
        record = {
            "user_id": user_id,
            "message_id": message_id,
            "vendor": vendor,
            "amount": amount,
            "category": category,
            "email_date": email_date,
            "subject": subject,
            "snippet": snippet,
            "confidence": confidence,
            "raw_source": raw_source,
            "created_at": datetime.now(),
            **kwargs
        }
        
        result = self.shopping_records.update_one(
            {"user_id": user_id, "message_id": message_id},
            {"$set": record},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            existing = self.shopping_records.find_one(
                {"user_id": user_id, "message_id": message_id}
            )
            return str(existing["_id"]) if existing else ""
    
    def insert_auto_expense_from_record(self, user_id: str,
                                       shopping_record_id: str,
                                       amount: float,
                                       category: str,
                                       description: str,
                                       occurred_at: Any) -> Optional[str]:
        """從購物記錄自動建立支出記錄"""
        expense = {
            "user_id": user_id,
            "shopping_record_id": shopping_record_id,
            "amount": amount,
            "category": category,
            "description": description,
            "occurred_at": occurred_at,
            "source": "GMAIL_AUTO",
            "created_at": datetime.now()
        }
        
        existing = self.expenses.find_one({
            "user_id": user_id,
            "shopping_record_id": shopping_record_id
        })
        
        if existing:
            return str(existing["_id"])
        
        result = self.expenses.insert_one(expense)
        return str(result.inserted_id) if result.inserted_id else None
    
    def list_shopping_records(self, user_id: str, start_date: Any,
                             end_date: Any, limit: int = 100) -> List[Dict]:
        """列出購物記錄"""
        records = self.shopping_records.find({
            "user_id": user_id,
            "email_date": {
                "$gte": start_date,
                "$lt": end_date
            }
        }).limit(limit).sort("email_date", DESCENDING)
        
        return list(records)
    
    def count_shopping_records(self, user_id: str, start_date: Any,
                              end_date: Any, raw_source: Optional[str] = None) -> int:
        """計算購物記錄數量"""
        query = {
            "user_id": user_id,
            "email_date": {
                "$gte": start_date,
                "$lt": end_date
            }
        }
        
        if raw_source:
            query["raw_source"] = raw_source
        
        return self.shopping_records.count_documents(query)
    
    def list_auto_expenses_in_range(self, user_id: str, start_date: str,
                                   end_date: str, limit: int = 100) -> List[Dict]:
        """列出自動記帳記錄"""
        expenses = self.expenses.find({
            "user_id": user_id,
            "source": "GMAIL_AUTO",
            "occurred_at": {
                "$gte": start_date,
                "$lt": end_date
            }
        }).limit(limit).sort("occurred_at", DESCENDING)
        
        return list(expenses)
    
    def close(self):
        """關閉資料庫連接"""
        if self.client:
            self.client.close()

# 為相容性提供別名
MongoDBAdapter = DatabaseManager

# 建立全域實例
_db_instance = None

def get_db_manager():
    """取得資料庫管理器實例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
