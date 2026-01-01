import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import json

logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB 管理器類"""
    
    def __init__(self, connection_string: str = None, database_name: str = "smartshopsaver"):
        """
        初始化 MongoDB 連接
        
        Args:
            connection_string: MongoDB 連接字串
            database_name: 資料庫名稱
        """
        # 從環境變數讀取連接字串
        if connection_string is None:
            connection_string = os.getenv("MONGODB_URI")
            if not connection_string:
                raise ValueError("請設定 MONGODB_URI 環境變數")
        
        if database_name == "smartshopsaver" and os.getenv("DATABASE_NAME"):
            database_name = os.getenv("DATABASE_NAME")
        
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        
        self._connect()
    
    def _connect(self):
        """建立資料庫連接"""
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000  # 5秒超時
            )
            # 測試連接
            self.client.server_info()
            self.db = self.client[self.database_name]
            logger.info(f"成功連接到 MongoDB 資料庫: {self.database_name}")
            
            # 建立索引
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"無法連接到 MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """建立資料庫索引"""
        try:
            # 用戶集合索引
            self.db.users.create_index([("line_user_id", ASCENDING)], unique=True)
            
            # 商品集合索引
            self.db.products.create_index([("url", ASCENDING)], unique=True)
            self.db.products.create_index([("name", ASCENDING)])
            
            # 價格歷史索引
            self.db.price_history.create_index([("product_id", ASCENDING), ("timestamp", DESCENDING)])
            
            # 追蹤列表索引
            self.db.user_tracking.create_index([("user_id", ASCENDING), ("product_id", ASCENDING)], unique=True)
            
            # 考慮清單索引
            self.db.user_consideration.create_index([("user_id", ASCENDING)])
            self.db.user_consideration.create_index([("user_id", ASCENDING), ("product_name", ASCENDING)])
            self.db.user_consideration.create_index([("created_at", DESCENDING)])
            
            # 財務助理索引
            self.db.expenses.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            self.db.expenses.create_index([("category", ASCENDING)])
            self.db.expenses.create_index([("shopping_record_id", ASCENDING)])
            self.db.expenses.create_index([("source", ASCENDING)])
            
            # 預算索引
            self.db.user_budget.create_index([("user_id", ASCENDING)], unique=True)
            
            # Gmail 自動記帳索引
            self.db.gmail_processed.create_index([("user_id", ASCENDING), ("message_id", ASCENDING)], unique=True)
            self.db.gmail_processed.create_index([("processed_at", DESCENDING)])
            
            # 購物記錄索引
            self.db.shopping_records.create_index([("user_id", ASCENDING), ("message_id", ASCENDING)], unique=True)
            self.db.shopping_records.create_index([("user_id", ASCENDING), ("email_date", DESCENDING)])
            self.db.shopping_records.create_index([("category", ASCENDING)])
            self.db.shopping_records.create_index([("created_at", DESCENDING)])
            
            logger.info("資料庫索引建立完成")
            
        except Exception as e:
            logger.error(f"建立索引時發生錯誤: {e}")
    
    def close_connection(self):
        """關閉資料庫連接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 連接已關閉")
    
    # ========== 用戶管理 ==========
    
    def create_user(self, line_user_id: str, display_name: str = None) -> bool:
        """創建新用戶"""
        try:
            user_data = {
                "line_user_id": line_user_id,
                "display_name": display_name,
                "created_at": datetime.now(),
                "last_active": datetime.now(),
                "preferences": {},
                "settings": {
                    "price_alert_threshold": 0.1,
                    "notifications_enabled": True
                }
            }
            
            result = self.db.users.insert_one(user_data)
            logger.info(f"用戶創建成功: {line_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"創建用戶失敗: {e}")
            return False
    
    def get_user(self, line_user_id: str) -> Optional[Dict]:
        """獲取用戶資料"""
        try:
            return self.db.users.find_one({"line_user_id": line_user_id})
        except Exception as e:
            logger.error(f"獲取用戶資料失敗: {e}")
            return None
    
    def update_user_activity(self, line_user_id: str):
        """更新用戶最後活動時間"""
        try:
            self.db.users.update_one(
                {"line_user_id": line_user_id},
                {"$set": {"last_active": datetime.now()}}
            )
        except Exception as e:
            logger.error(f"更新用戶活動時間失敗: {e}")
    
    # ========== 商品管理 ==========
    
    def save_product(self, product_data: Dict) -> Optional[str]:
        """保存商品資料"""
        try:
            existing = self.db.products.find_one({"url": product_data["url"]})
            
            if existing:
                self.db.products.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        **product_data,
                        "updated_at": datetime.now()
                    }}
                )
                return str(existing["_id"])
            else:
                product_data.update({
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                })
                result = self.db.products.insert_one(product_data)
                return str(result.inserted_id)
                
        except Exception as e:
            logger.error(f"保存商品失敗: {e}")
            return None
    
    def get_product(self, product_id: str = None, url: str = None) -> Optional[Dict]:
        """獲取商品資料"""
        try:
            from bson import ObjectId
            
            if product_id:
                return self.db.products.find_one({"_id": ObjectId(product_id)})
            elif url:
                return self.db.products.find_one({"url": url})
            
        except Exception as e:
            logger.error(f"獲取商品資料失敗: {e}")
            return None
    
    # ========== 價格歷史管理 ==========
    
    def save_price_history(self, product_id: str, price: float, source: str = "scraped"):
        """保存價格歷史"""
        try:
            from bson import ObjectId
            
            price_data = {
                "product_id": ObjectId(product_id),
                "price": price,
                "source": source,
                "timestamp": datetime.now()
            }
            
            self.db.price_history.insert_one(price_data)
            logger.info(f"價格歷史保存成功: 商品 {product_id}, 價格 {price}")
            
        except Exception as e:
            logger.error(f"保存價格歷史失敗: {e}")
    
    def get_price_history(self, product_id: str, limit: int = 30) -> List[Dict]:
        """獲取價格歷史"""
        try:
            from bson import ObjectId
            
            cursor = self.db.price_history.find(
                {"product_id": ObjectId(product_id)}
            ).sort("timestamp", DESCENDING).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"獲取價格歷史失敗: {e}")
            return []
    
    # ========== 用戶追蹤管理 ==========
    
    def add_user_tracking(self, line_user_id: str, product_id: str, target_price: float = None) -> bool:
        """添加用戶追蹤商品"""
        try:
            from bson import ObjectId
            
            user = self.get_user(line_user_id)
            if not user:
                self.create_user(line_user_id)
            
            tracking_data = {
                "user_id": line_user_id,
                "product_id": ObjectId(product_id),
                "target_price": target_price,
                "created_at": datetime.now(),
                "is_active": True
            }
            
            self.db.user_tracking.update_one(
                {"user_id": line_user_id, "product_id": ObjectId(product_id)},
                {"$set": tracking_data},
                upsert=True
            )
            
            logger.info(f"用戶追蹤添加成功: {line_user_id} -> 商品 {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加用戶追蹤失敗: {e}")
            return False
    
    def get_user_tracking_products(self, line_user_id: str) -> List[Dict]:
        """獲取用戶追蹤的商品列表"""
        try:
            pipeline = [
                {"$match": {"user_id": line_user_id, "is_active": True}},
                {
                    "$lookup": {
                        "from": "products",
                        "localField": "product_id",
                        "foreignField": "_id",
                        "as": "product"
                    }
                },
                {"$unwind": "$product"},
                {
                    "$project": {
                        "target_price": 1,
                        "created_at": 1,
                        "product.name": 1,
                        "product.current_price": 1,
                        "product.url": 1,
                        "product.image_url": 1
                    }
                }
            ]
            
            return list(self.db.user_tracking.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"獲取用戶追蹤商品失敗: {e}")
            return []
    
    def remove_user_tracking(self, line_user_id: str, product_id: str) -> bool:
        """移除用戶追蹤"""
        try:
            from bson import ObjectId
            
            result = self.db.user_tracking.update_one(
                {"user_id": line_user_id, "product_id": ObjectId(product_id)},
                {"$set": {"is_active": False}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"移除用戶追蹤失敗: {e}")
            return False
    
    # ========== 考慮清單管理 ==========
    
    def add_user_consideration(self, user_id: str, product_name: str, price_info: Dict = None) -> bool:
        """添加商品到用戶考慮清單"""
        try:
            user = self.get_user(user_id)
            if not user:
                self.create_user(user_id)
            
            consideration_data = {
                "user_id": user_id,
                "product_name": product_name,
                "price_info": price_info or {},
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            }
            
            if price_info:
                consideration_data["price_range"] = price_info.get("price_range", "")
                consideration_data["main_platform"] = price_info.get("main_platform", "")
                consideration_data["min_price"] = price_info.get("min_price", 0)
                consideration_data["max_price"] = price_info.get("max_price", 0)
            
            result = self.db.user_consideration.update_one(
                {"user_id": user_id, "product_name": product_name, "is_active": True},
                {"$set": consideration_data},
                upsert=True
            )
            
            logger.info(f"用戶考慮清單添加成功: {user_id} -> {product_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加考慮清單失敗: {e}")
            return False
    
    def get_user_considerations(self, user_id: str) -> List[Dict]:
        """獲取用戶的考慮清單"""
        try:
            cursor = self.db.user_consideration.find(
                {"user_id": user_id, "is_active": True},
                sort=[("created_at", DESCENDING)]
            )
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"獲取考慮清單失敗: {e}")
            return []
    
    def get_user_consideration(self, user_id: str, product_name: str) -> Optional[Dict]:
        """獲取特定商品的考慮記錄"""
        try:
            return self.db.user_consideration.find_one({
                "user_id": user_id,
                "product_name": product_name,
                "is_active": True
            })
            
        except Exception as e:
            logger.error(f"獲取考慮記錄失敗: {e}")
            return None
    
    def remove_user_consideration(self, user_id: str, product_name: str) -> bool:
        """從考慮清單中移除商品"""
        try:
            result = self.db.user_consideration.update_one(
                {"user_id": user_id, "product_name": product_name},
                {"$set": {"is_active": False, "updated_at": datetime.now()}}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"考慮清單移除成功: {user_id} -> {product_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"移除考慮清單失敗: {e}")
            return False
    
    def update_consideration_price(self, user_id: str, product_name: str, price_info: Dict) -> bool:
        """更新考慮清單中商品的價格資訊"""
        try:
            update_data = {
                "price_info": price_info,
                "updated_at": datetime.now()
            }
            
            if price_info:
                update_data["price_range"] = price_info.get("price_range", "")
                update_data["main_platform"] = price_info.get("main_platform", "")
                update_data["min_price"] = price_info.get("min_price", 0)
                update_data["max_price"] = price_info.get("max_price", 0)
            
            result = self.db.user_consideration.update_one(
                {"user_id": user_id, "product_name": product_name, "is_active": True},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新考慮清單價格失敗: {e}")
            return False
    
    # ========== 財務管理功能 ==========
    
    def get_user_finance_summary(self, user_id: str, last_month: bool = False) -> Optional[Dict]:
        """獲取用戶的財務摘要"""
        try:
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            now = datetime.now()
            
            if last_month:
                month_start = datetime(now.year, now.month, 1) - relativedelta(months=1)
                next_month = datetime(now.year, now.month, 1)
            else:
                month_start = datetime(now.year, now.month, 1)
                next_month = month_start + relativedelta(months=1)
            
            expenses_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "created_at": {"$gte": month_start, "$lt": next_month}
                    }
                },
                {
                    "$group": {
                        "_id": "$category",
                        "total": {"$sum": "$amount"}
                    }
                }
            ]
            
            category_expenses = list(self.db.expenses.aggregate(expenses_pipeline))
            categories = {item["_id"]: item["total"] for item in category_expenses}
            total_spending = sum(categories.values())
            
            budget_doc = self.db.user_budget.find_one({"user_id": user_id})
            budget = budget_doc.get("budget", 0) if budget_doc else 0
            
            return {
                "total_spending": total_spending,
                "budget": budget,
                "categories": categories
            }
            
        except ImportError:
            logger.error("請安裝 python-dateutil: pip install python-dateutil")
            try:
                expenses = list(self.db.expenses.find({"user_id": user_id}))
                total = sum(e.get("amount", 0) for e in expenses)
                budget_doc = self.db.user_budget.find_one({"user_id": user_id})
                budget = budget_doc.get("budget", 0) if budget_doc else 0
                
                return {
                    "total_spending": total,
                    "budget": budget,
                    "categories": []
                }
            except Exception as e:
                logger.error(f"獲取財務摘要失敗: {e}")
                return None
        except Exception as e:
            logger.error(f"獲取財務摘要失敗: {e}")
            return None
    
    def add_user_expense(self, user_id: str, amount: float, category: str, description: str = "") -> bool:
        """新增用戶支出記錄"""
        try:
            expense_data = {
                "user_id": user_id,
                "amount": amount,
                "category": category,
                "description": description,
                "created_at": datetime.now()
            }
            
            self.db.expenses.insert_one(expense_data)
            logger.info(f"支出記錄新增成功: {user_id} - {category} NT${amount}")
            return True
            
        except Exception as e:
            logger.error(f"新增支出記錄失敗: {e}")
            return False
    
    def set_user_budget(self, user_id: str, budget: float) -> bool:
        """設定用戶月預算"""
        try:
            budget_data = {
                "user_id": user_id,
                "budget": budget,
                "updated_at": datetime.now()
            }
            
            self.db.user_budget.update_one(
                {"user_id": user_id},
                {"$set": budget_data},
                upsert=True
            )
            
            logger.info(f"預算設定成功: {user_id} - NT${budget}")
            return True
            
        except Exception as e:
            logger.error(f"設定預算失敗: {e}")
            return False
    
    def get_user_expenses(self, user_id: str, limit: int = 50) -> List[Dict]:
        """獲取用戶的支出記錄"""
        try:
            cursor = self.db.expenses.find(
                {"user_id": user_id},
                sort=[("created_at", DESCENDING)]
            ).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"獲取支出記錄失敗: {e}")
            return []
    
    # ========== Gmail 自動記帳功能 ==========
    
    def is_gmail_message_processed(self, user_id: str, message_id: str) -> bool:
        """檢查 Gmail 訊息是否已處理"""
        try:
            result = self.db.gmail_processed.find_one({
                "user_id": user_id,
                "message_id": message_id
            })
            return result is not None
        except Exception as e:
            logger.error(f"檢查郵件處理狀態失敗: {e}")
            return False
    
    def mark_gmail_message_processed(self, user_id: str, message_id: str, 
                                     subject: str = "", email_date: str = "") -> bool:
        """標記 Gmail 訊息為已處理"""
        try:
            self.db.gmail_processed.update_one(
                {"user_id": user_id, "message_id": message_id},
                {"$set": {
                    "user_id": user_id,
                    "message_id": message_id,
                    "subject": subject,
                    "email_date": email_date,
                    "processed_at": datetime.now(),
                    "created_at": datetime.now()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"標記郵件處理失敗: {e}")
            return False
    
    def save_shopping_record(self, user_id: str, message_id: str, 
                            vendor: str, amount: float, category: str,
                            email_date: str, subject: str = "", 
                            snippet: str = "", confidence: float = 0.0,
                            raw_source: str = "GPT") -> Optional[str]:
        """儲存購物記錄"""
        try:
            from bson import ObjectId
            
            record_data = {
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
                "updated_at": datetime.now()
            }
            
            result = self.db.shopping_records.update_one(
                {"user_id": user_id, "message_id": message_id},
                {"$set": record_data},
                upsert=True
            )
            
            if result.upserted_id:
                return str(result.upserted_id)
            else:
                existing = self.db.shopping_records.find_one({
                    "user_id": user_id, 
                    "message_id": message_id
                })
                return str(existing["_id"]) if existing else None
            
        except Exception as e:
            logger.error(f"儲存購物記錄失敗: {e}")
            return None
    
    def get_shopping_record_by_message(self, user_id: str, message_id: str) -> Optional[Dict]:
        """根據訊息 ID 獲取購物記錄"""
        try:
            return self.db.shopping_records.find_one({
                "user_id": user_id,
                "message_id": message_id
            })
        except Exception as e:
            logger.error(f"獲取購物記錄失敗: {e}")
            return None
    
    def add_gmail_expense(self, user_id: str, shopping_record_id: str,
                         amount: float, category: str, description: str,
                         occurred_at: str = None) -> bool:
        """從購物記錄新增 Gmail 自動支出"""
        try:
            from bson import ObjectId
            
            existing = self.db.expenses.find_one({
                "user_id": user_id,
                "shopping_record_id": shopping_record_id,
                "source": "gmail_auto"
            })
            
            if existing:
                self.db.expenses.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "amount": amount,
                        "category": category,
                        "description": description,
                        "updated_at": datetime.now()
                    }}
                )
                logger.info(f"更新 Gmail 自動記帳: {description} NT${amount}")
            else:
                expense_data = {
                    "user_id": user_id,
                    "shopping_record_id": shopping_record_id,
                    "amount": amount,
                    "category": category,
                    "description": description,
                    "source": "gmail_auto",
                    "created_at": datetime.now()
                }
                
                if occurred_at:
                    expense_data["occurred_at"] = occurred_at
                
                self.db.expenses.insert_one(expense_data)
                logger.info(f"新增 Gmail 自動記帳: {description} NT${amount}")
            
            return True
            
        except Exception as e:
            logger.error(f"新增 Gmail 支出失敗: {e}")
            return False
    
    def get_shopping_records(self, user_id: str, limit: int = 50) -> List[Dict]:
        """獲取用戶的購物記錄列表"""
        try:
            cursor = self.db.shopping_records.find(
                {"user_id": user_id},
                sort=[("email_date", DESCENDING)]
            ).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"獲取購物記錄列表失敗: {e}")
            return []
    
    def count_shopping_records_in_range(self, user_id: str, 
                                       start_date: str, end_date: str) -> int:
        """統計時間範圍內的購物記錄數量"""
        try:
            count = self.db.shopping_records.count_documents({
                "user_id": user_id,
                "email_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
            return count
        except Exception as e:
            logger.error(f"統計購物記錄失敗: {e}")
            return 0
    
    def get_shopping_records_in_range(self, user_id: str, 
                                     start_date: str, end_date: str,
                                     limit: int = 100) -> List[Dict]:
        """獲取時間範圍內的購物記錄"""
        try:
            cursor = self.db.shopping_records.find(
                {
                    "user_id": user_id,
                    "email_date": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                },
                sort=[("email_date", DESCENDING)]
            ).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"獲取時間範圍購物記錄失敗: {e}")
            return []
    
    def delete_shopping_record(self, user_id: str, record_id: str) -> bool:
        """刪除購物記錄及相關的自動記帳"""
        try:
            from bson import ObjectId
            
            self.db.expenses.delete_many({
                "user_id": user_id,
                "shopping_record_id": record_id,
                "source": "gmail_auto"
            })
            
            result = self.db.shopping_records.delete_one({
                "_id": ObjectId(record_id),
                "user_id": user_id
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"刪除購物記錄失敗: {e}")
            return False

# 全局資料庫實例
db_manager = None

def get_db_manager() -> MongoDBManager:
    """獲取資料庫管理器實例"""
    global db_manager
    if db_manager is None:
        connection_string = os.getenv("MONGODB_URI")
        if not connection_string:
            raise ValueError("請設定 MONGODB_URI 環境變數")
        db_manager = MongoDBManager(connection_string)
    return db_manager
