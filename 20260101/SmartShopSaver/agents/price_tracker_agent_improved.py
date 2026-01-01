# agents/price_tracker_agent_improved.py
# -*- coding: utf-8 -*-
"""價格追蹤代理人 - 簡化版"""

import logging
import requests
import re
import urllib.parse
from typing import Dict, List, Optional
from datetime import datetime
from .base_agent import BaseAgent, agent_registry

logger = logging.getLogger(__name__)


class PriceTrackerAgent(BaseAgent):
    """價格追蹤代理人"""
    
    def __init__(self, line_bot_api=None):
        self.line_bot_api = line_bot_api
        super().__init__("PriceTracker")
        
        try:
            from utils.database import get_db_manager
            self.db = get_db_manager()
            self.db_connected = True
            logger.info("MongoDB 連接成功")
        except Exception as e:
            logger.warning(f"MongoDB 連接失敗: {e}")
            self.db = None
            self.db_connected = False
        
        logger.info("價格追蹤代理人初始化完成")
    
    def get_tools(self) -> List:
        return []
    
    def get_system_prompt(self) -> str:
        return "你是 SmartShopSaver 價格追蹤專家"
    
    def _create_agent(self) -> None:
        return None
    
    def set_line_bot_api(self, line_bot_api):
        self.line_bot_api = line_bot_api
    
    def can_handle(self, message: str) -> bool:
        """判斷是否可以處理此訊息"""
        price_keywords = [
            '價格', '多少錢', '比價', '追蹤', '監控', '通知', '降價',
            '便宜', '特價', '折扣', '優惠', '目標價', '低於', '售價',
            '加入考慮', '考慮清單', '考慮', '想買', '猶豫',
            '清單', '列表', '移除', '刪除', '取消', '查詢', '查看', '查價',
            '最低價'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in price_keywords)
    
    def _process_message_internal(self, user_id: str, message: str) -> str:
        return self.process_user_request(user_id, message)
    
    def process_user_request(self, user_id: str, message: str) -> str:
        """處理用戶請求"""
        try:
            message_lower = message.strip().lower()
            
            # 1. 移除/刪除/取消功能
            if any(kw in message_lower for kw in ['移除', '刪除', '取消']):
                return self._handle_remove_tracking(user_id, message)
            
            # 2. 查看清單功能
            elif any(kw in message_lower for kw in ['清單', '列表']) or \
                 ('查看' in message_lower and '追蹤' in message_lower):
                return self._handle_list_request(user_id)
            
            # 3. 追蹤功能
            elif any(kw in message_lower for kw in ['追蹤', '監控']):
                return self._handle_track_request(user_id, message)
            
            # 4. 查詢最低價功能
            elif any(kw in message_lower for kw in ['查詢', '查價', '價格', '多少錢', '最低價']):
                return self._handle_price_query(user_id, message)
            
            # 5. 預設情況
            else:
                return self._get_help_message()
                
        except Exception as e:
            logger.error(f"處理請求失敗: {e}")
            return "❌ 系統錯誤，請稍後再試"
    
    def _handle_track_request(self, user_id: str, message: str) -> str:
        """處理追蹤請求"""
        try:
            product_name = self._extract_product_name(message)
            target_price = self._extract_target_price(message)
            
            if not product_name:
                return "❌ 請提供商品名稱\n\n範例：追蹤 iPhone 15 Pro 目標價格 35000"
            
            if not target_price:
                return f"❌ 請提供目標價格\n\n範例：追蹤 {product_name} 目標價格 [金額]"
            
            return self._track_product_by_name(user_id, product_name, target_price)
            
        except Exception as e:
            logger.error(f"追蹤失敗: {e}")
            return "❌ 追蹤失敗"
    
    def _handle_price_query(self, user_id: str, message: str) -> str:
        """處理價格查詢"""
        product_name = self._extract_product_name(message)
        if not product_name:
            return "❌ 請提供要查詢的商品名稱"
        
        results = self._search_pchome(product_name)
        if not results:
            return f"❌ 找不到「{product_name}」的商品"
        
        response = f"🔍 「{product_name}」查詢結果\n\n"
        response += f"💰 最低價: NT${results.get('min_price', 0):,}\n"
        response += f"🏪 平台: {results.get('platform', 'PChome 24h')}\n"
        response += f"📦 商品: {results.get('product_name', '')[:40]}...\n"
        response += f"🔗 {results.get('url', '')}"
        
        return response
    
    def _handle_list_request(self, user_id: str) -> str:
        """查看追蹤清單"""
        if not self.db_connected:
            return "❌ 資料庫未連接"
        
        try:
            trackings = list(self.db.db.product_name_tracking.find(
                {"user_id": user_id, "is_active": True}
            ))
            
            if not trackings:
                return "📊 您的追蹤清單目前是空的\n\n💡 輸入：追蹤 [商品名] 目標價格 [金額]"
            
            response = f"📊 **您的追蹤清單** (共 {len(trackings)} 項)\n\n"
            
            for i, t in enumerate(trackings, 1):
                name = t.get('product_name', '商品')
                target = t.get('target_price', 0)
                current = t.get('current_lowest_price', 0)
                
                response += f"📱 **{i}. {name}**\n"
                response += f"   🎯 目標: NT${target:,}\n"
                response += f"   💰 目前: NT${current:,}\n"
                
                if current > 0 and current <= target:
                    response += "   ✅ 已達標！\n"
                elif current > 0:
                    response += f"   📈 需降: NT${current - target:,}\n"
                
                response += "\n"
            
            return response
            
        except Exception as e:
            logger.error(f"查詢清單失敗: {e}")
            return "❌ 查詢失敗"
    
    def _handle_remove_tracking(self, user_id: str, message: str) -> str:
        """移除追蹤"""
        if not self.db_connected:
            return "❌ 資料庫未連接"
        
        try:
            if '全部' in message or '所有' in message:
                result = self.db.db.product_name_tracking.update_many(
                    {"user_id": user_id, "is_active": True},
                    {"$set": {"is_active": False}}
                )
                return f"✅ 已移除全部 {result.modified_count} 個追蹤項目"
            
            # 提取商品名稱
            product_name = self._extract_product_name(message)
            if not product_name:
                return "❌ 請指定要移除的商品名稱\n\n範例：移除追蹤 iPhone 15"
            
            result = self.db.db.product_name_tracking.update_one(
                {"user_id": user_id, "product_name": {"$regex": product_name, "$options": "i"}, "is_active": True},
                {"$set": {"is_active": False}}
            )
            
            if result.modified_count > 0:
                return f"✅ 已移除「{product_name}」的追蹤"
            else:
                return f"❌ 找不到「{product_name}」的追蹤記錄"
                
        except Exception as e:
            logger.error(f"移除追蹤失敗: {e}")
            return "❌ 移除失敗"
    
    def _extract_product_name(self, message: str) -> Optional[str]:
        """提取產品名稱"""
        try:
            # 移除價格相關的數字
            price_pattern = r'(目標價格|價格|元|\$|NT\$?)\s*\d+'
            clean = re.sub(price_pattern, '', message)
            
            # 移除關鍵字
            remove_keywords = ['追蹤', '監控', '通知', '降價', '請幫我', '幫我', 
                             '查詢', '查價', '移除', '刪除', '取消']
            for kw in remove_keywords:
                clean = clean.replace(kw, ' ')
            
            # 移除標點符號和多餘空白
            clean = re.sub(r'[，,。.！!？?]', ' ', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            
            if len(clean) > 2:
                return clean
            
            return None
            
        except Exception as e:
            logger.error(f"提取產品名稱失敗: {e}")
            return None
    
    def _extract_target_price(self, message: str) -> Optional[float]:
        """提取目標價格"""
        patterns = [
            r'目標價格\s*[::：]?\s*(\d+)',
            r'目標\s*[::：]?\s*(\d+)',
            r'價格\s*[::：]?\s*(\d+)',
            r'(\d{4,})\s*元',
            r'NT\$?\s*(\d+)',
            r'\$\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                price = float(match.group(1))
                if price >= 100:
                    return price
        
        return None
    
    def _track_product_by_name(self, user_id: str, product_name: str, target_price: float) -> str:
        """追蹤商品"""
        try:
            results = self._search_pchome(product_name)
            
            if not results:
                return f"❌ 找不到「{product_name}」\n\n💡 建議使用更簡單的關鍵字"
            
            if self.db_connected and self.db:
                tracking_data = {
                    "user_id": user_id,
                    "product_name": product_name,
                    "actual_product_name": results.get('product_name', ''),
                    "target_price": target_price,
                    "current_lowest_price": results.get('min_price', 0),
                    "lowest_price_platform": results.get('platform', ''),
                    "lowest_price_url": results.get('url', ''),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "is_active": True
                }
                
                self.db.db.product_name_tracking.update_one(
                    {"user_id": user_id, "product_name": product_name},
                    {"$set": tracking_data},
                    upsert=True
                )
                
                current_price = results.get('min_price', 0)
                
                response = f"✅ **追蹤成功！**\n\n"
                response += f"📱 商品：{product_name}\n"
                response += f"💰 目前最低價：NT${current_price:,}\n"
                response += f"🎯 目標價格：NT${target_price:,}\n"
                response += f"🏪 平台：{results.get('platform', 'PChome 24h')}\n"
                
                if current_price <= target_price:
                    response += f"\n🔥 **已達目標價格！立即購買！**\n"
                    response += f"🛒 {results.get('url', '')}"
                else:
                    diff = current_price - target_price
                    response += f"\n📈 還需降價：NT${diff:,}"
                
                return response
            else:
                return "❌ 資料庫連接失敗"
                
        except Exception as e:
            logger.error(f"追蹤失敗: {e}")
            return "❌ 追蹤失敗"
    
    def _search_pchome(self, product_name: str) -> Optional[Dict]:
        """搜尋 PChome"""
        try:
            encoded = urllib.parse.quote(product_name)
            url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={encoded}&page=1&sort=rel/dc"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                products = data.get('prods', [])
                
                if products:
                    # 過濾配件
                    filtered = self._filter_products(products, product_name)
                    if filtered:
                        prices = [p.get('price', 0) for p in filtered if p.get('price')]
                        if prices:
                            min_price = min(prices)
                            cheapest = min(filtered, key=lambda x: x.get('price', float('inf')))
                            
                            return {
                                'platform': 'PChome 24h',
                                'min_price': min_price,
                                'url': f"https://24h.pchome.com.tw/prod/{cheapest.get('Id', '')}",
                                'product_name': cheapest.get('name', ''),
                                'product_id': cheapest.get('Id', '')
                            }
            
            return None
        except Exception as e:
            logger.error(f"PChome 搜尋失敗: {e}")
            return None
    
    def _filter_products(self, products: List[Dict], query: str) -> List[Dict]:
        """過濾配件商品"""
        exclude_keywords = [
            '保護套', '保護殼', '手機殼', '皮套', '充電器', '充電線',
            '傳輸線', '電池', '行動電源', '耳機套', '支架', '貼膜',
            '保護貼', '配件', '周邊', '專用', '適用於'
        ]
        
        filtered = []
        for p in products:
            name = p.get('name', '').lower()
            if not any(ex in name for ex in exclude_keywords):
                filtered.append(p)
        
        return filtered[:10] if filtered else products[:10]
    
    def _get_help_message(self) -> str:
        """取得幫助訊息"""
        return """📊 **價格追蹤功能說明**

🔍 **查詢價格**
• 查詢 iPhone 15 價格
• iPhone 15 多少錢

📌 **追蹤商品**
• 追蹤 iPhone 15 Pro 目標價格 35000
• 監控 PS5 目標價格 15000

📋 **查看清單**
• 我的追蹤清單
• 查看追蹤列表

🗑️ **移除追蹤**
• 移除追蹤 iPhone 15
• 取消全部追蹤

💡 系統會自動監控價格變化並通知您！"""


# 註冊代理人
try:
    price_tracker_agent = PriceTrackerAgent()
    agent_registry.register("PriceTracker", price_tracker_agent)
    logger.info("✅ 價格追蹤代理人已註冊")
except Exception as e:
    logger.error(f"❌ 價格追蹤代理人註冊失敗: {e}")
