# agents/ai_intent_analyzer.py
"""
AI 意圖分析器 - 使用 OpenAI 理解用戶真實意圖
完全不依賴關鍵字，純 AI 理解
"""

import os
import json
import logging
import requests
from typing import Dict, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AIIntentAnalyzer:
    """AI 意圖分析器 - 理解用戶的真實需求"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("GPT_MODEL", "gpt-4o-mini")
        
        # 代理人能力描述
        self.agents_capabilities = {
            "UniversalRecommendation": {
                "description": "通用推薦代理人",
                "capabilities": [
                    "推薦任何產品",
                    "不受資料庫限制",
                    "AI動態生成推薦",
                    "根據預算推薦",
                    "根據用途推薦"
                ],
                "examples": [
                    "我想買吹風機",
                    "推薦相機",
                    "有什麼好的咖啡機",
                    "幫我選電餵",
                    "任何產品推薦"
                ]
            },
            "SmartRecommendation": {
                "description": "智能推薦代理人",
                "capabilities": [
                    "產品推薦和建議",
                    "比較不同產品",
                    "選購指南",
                    "根據預算推薦",
                    "根據用途推薦"
                ],
                "examples": [
                    "我想買滑鼠",
                    "推薦好用的鍵盤",
                    "有什麼耳機推薦",
                    "幫我選手機",
                    "哪個比較好"
                ]
            },
            "PriceTracker": {
                "description": "價格追蹤代理人",
                "capabilities": [
                    "查詢商品價格",
                    "設定價格追蹤",
                    "降價通知",
                    "價格歷史",
                    "管理追蹤清單"
                ],
                "examples": [
                    "iPhone 15 多少錢",
                    "追蹤價格",
                    "設定降價提醒",
                    "查看我的追蹤清單",
                    "最低價是多少"
                ]
            },
            "ProductReview": {
                "description": "產品評論代理人",
                "capabilities": [
                    "查詢產品評價",
                    "分析優缺點",
                    "用戶評論整理",
                    "評分統計",
                    "使用心得"
                ],
                "examples": [
                    "這個好用嗎",
                    "評價如何",
                    "用戶怎麼說",
                    "值得買嗎",
                    "有什麼缺點"
                ]
            },
            "Finance": {
                "description": "財務管理代理人",
                "capabilities": [
                    "記帳功能",
                    "消費統計",
                    "預算管理",
                    "支出分析",
                    "財務報表"
                ],
                "examples": [
                    "記帳午餐150",
                    "這個月花了多少",
                    "查看支出",
                    "設定預算",
                    "消費統計"
                ]
            },
            "Gmail": {
                "description": "Gmail整合代理人",
                "capabilities": [
                    "連接Gmail帳號",
                    "讀取購物郵件",
                    "同步購物記錄",
                    "郵件提醒",
                    "自動整理"
                ],
                "examples": [
                    "連接Gmail",
                    "查看購物郵件",
                    "同步郵件",
                    "郵件記錄",
                    "Gmail授權"
                ]
            }
        }
        
        # 對話歷史（用於上下文理解）
        self.conversation_history = {}
        
        logger.info("AI 意圖分析器初始化完成")
    
    def analyze_intent(self, message: str, user_id: str = None) -> Tuple[str, float, Dict]:
        """
        使用 AI 分析用戶意圖
        返回: (代理人名稱, 信心度, 詳細分析)
        """
        # 獲取用戶對話歷史
        context = self._get_user_context(user_id) if user_id else []
        
        if not self.api_key:
            # 沒有 API Key 時使用進階規則分析
            return self._advanced_fallback_analysis(message, context)
        
        try:
            # 構建 AI prompt
            prompt = self._build_advanced_prompt(message, context)
            
            # 調用 OpenAI API
            result = self._call_openai(prompt)
            
            if result:
                agent = result.get("agent", "SmartRecommendation")
                confidence = result.get("confidence", 0.5)
                analysis = result.get("analysis", {})
                
                # 記錄對話歷史
                if user_id:
                    self._update_conversation_history(user_id, message, agent)
                
                logger.info(f"AI 分析結果 - Agent: {agent}, Confidence: {confidence}")
                return agent, confidence, analysis
            
        except Exception as e:
            logger.error(f"AI 分析失敗: {e}")
        
        # 失敗時使用進階備用方案
        return self._advanced_fallback_analysis(message, context)
    
    def _build_advanced_prompt(self, message: str, context: List[Dict]) -> str:
        """構建進階分析 prompt"""
        
        # 構建代理人說明
        agents_desc = ""
        for name, info in self.agents_capabilities.items():
            agents_desc += f"\n{name}:\n"
            agents_desc += f"  描述: {info['description']}\n"
            agents_desc += f"  能力: {', '.join(info['capabilities'][:3])}\n"
        
        # 構建上下文
        context_str = ""
        if context:
            recent = context[-3:]  # 最近3條對話
            for item in recent:
                context_str += f"用戶: {item.get('message', '')}\n"
                context_str += f"處理: {item.get('agent', '')}\n"
        
        return f"""你是一個智能助理的意圖分析器。請分析用戶訊息，判斷應該由哪個代理人處理。

可用代理人：{agents_desc}

對話歷史：
{context_str if context_str else "（新對話）"}

當前用戶訊息："{message}"

分析規則：
1. 仔細理解用戶的真實需求，不要只看表面關鍵字
2. 考慮對話上下文，理解用戶可能的後續問題
3. 如果用戶想買東西、需要建議、比較產品 → SmartRecommendation
4. 如果詢問價格、要追蹤降價 → PriceTracker
5. 如果問產品好不好、評價、用戶體驗 → ProductReview
6. 如果要記錄花費、查看消費 → Finance
7. 如果提到郵件、Gmail → Gmail
8. 不確定時，優先選擇 SmartRecommendation

請返回 JSON 格式：
{{
    "agent": "最適合的代理人名稱",
    "confidence": 0.0-1.0的信心度,
    "analysis": {{
        "intent": "用戶真實意圖（中文）",
        "keywords": ["識別到的關鍵概念"],
        "context": "上下文理解",
        "reasoning": "選擇此代理人的原因",
        "alternative": "備選代理人（如果有）"
    }}
}}

只返回 JSON，不要其他文字。"""
    
    def _call_openai(self, prompt: str) -> Optional[Dict]:
        """調用 OpenAI API"""
        try:
            url = f"{self.api_base.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一個精準的意圖分析器，擅長理解用戶的真實需求，不被表面文字迷惑。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return json.loads(content)
            else:
                logger.error(f"OpenAI API 錯誤: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"調用 OpenAI 失敗: {e}")
            return None
    
    def _advanced_fallback_analysis(self, message: str, context: List[Dict]) -> Tuple[str, float, Dict]:
        """進階備用分析方案（無 API 時）"""
        message_lower = message.lower()
        
        # 分析各個代理人的匹配度
        scores = {}
        
        # SmartRecommendation - 推薦相關
        recommendation_score = 0
        if any(word in message_lower for word in ['買', '推薦', '建議', '想要', '需要', '選', '哪個', '什麼', '好']):
            recommendation_score += 0.5
        if any(word in message_lower for word in ['滑鼠', '鍵盤', '耳機', '手機', '筆電', '平板']):
            recommendation_score += 0.3
        if '?' in message or '？' in message or '嗎' in message:
            recommendation_score += 0.2
        scores['SmartRecommendation'] = recommendation_score
        
        # PriceTracker - 價格相關
        price_score = 0
        if any(word in message_lower for word in ['價格', '多少錢', '追蹤', '降價', '便宜', '特價']):
            price_score += 0.7
        if any(word in message_lower for word in ['通知', '提醒', '目標價']):
            price_score += 0.3
        scores['PriceTracker'] = price_score
        
        # ProductReview - 評價相關
        review_score = 0
        if any(word in message_lower for word in ['評價', '評論', '好不好', '好用', '值得', '怎麼樣']):
            review_score += 0.7
        if any(word in message_lower for word in ['優點', '缺點', '心得', '體驗']):
            review_score += 0.3
        scores['ProductReview'] = review_score
        
        # Finance - 財務相關
        finance_score = 0
        if any(word in message_lower for word in ['記帳', '記錄', '花費', '花了', '消費', '支出']):
            finance_score += 0.7
        if any(word in message_lower for word in ['預算', '統計', '這個月', '本月', '今天']):
            finance_score += 0.3
        scores['Finance'] = finance_score
        
        # Gmail - 郵件相關
        gmail_score = 0
        if any(word in message_lower for word in ['gmail', 'mail', '郵件', '信件', 'email']):
            gmail_score += 0.8
        if any(word in message_lower for word in ['連接', '連結', '授權', '同步']):
            gmail_score += 0.2
        scores['Gmail'] = gmail_score
        
        # 選擇最高分的代理人
        if max(scores.values()) == 0:
            # 沒有明確匹配，預設推薦
            best_agent = 'SmartRecommendation'
            confidence = 0.3
        else:
            best_agent = max(scores, key=scores.get)
            confidence = min(scores[best_agent], 0.9)
        
        # 構建分析結果
        analysis = {
            "intent": self._guess_intent(message),
            "keywords": self._extract_keywords(message),
            "context": "基於規則分析",
            "reasoning": f"匹配度最高的功能是{best_agent}"
        }
        
        return best_agent, confidence, analysis
    
    def _guess_intent(self, message: str) -> str:
        """猜測用戶意圖"""
        message_lower = message.lower()
        
        if '買' in message_lower or '推薦' in message_lower:
            return "尋求產品推薦"
        elif '價格' in message_lower or '多少錢' in message_lower:
            return "查詢價格資訊"
        elif '評價' in message_lower or '好不好' in message_lower:
            return "了解產品評價"
        elif '記帳' in message_lower or '花' in message_lower:
            return "記錄財務資訊"
        elif 'gmail' in message_lower or '郵件' in message_lower:
            return "Gmail相關操作"
        else:
            return "一般諮詢"
    
    def _extract_keywords(self, message: str) -> List[str]:
        """提取關鍵詞"""
        keywords = []
        message_lower = message.lower()
        
        # 產品關鍵詞
        products = ['滑鼠', '鍵盤', '耳機', '手機', '筆電', '平板', 'iphone', 'airpods']
        for product in products:
            if product in message_lower:
                keywords.append(product)
        
        # 動作關鍵詞
        actions = ['買', '推薦', '價格', '評價', '記帳', '追蹤']
        for action in actions:
            if action in message_lower:
                keywords.append(action)
        
        return keywords[:5]  # 最多返回5個關鍵詞
    
    def _get_user_context(self, user_id: str) -> List[Dict]:
        """獲取用戶對話歷史"""
        if user_id and user_id in self.conversation_history:
            return self.conversation_history[user_id]
        return []
    
    def _update_conversation_history(self, user_id: str, message: str, agent: str):
        """更新對話歷史"""
        if not user_id:
            return
        
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "agent": agent
        })
        
        # 只保留最近10條記錄
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
    
    def get_agent_suggestion(self, agent_name: str) -> str:
        """獲取代理人的使用建議"""
        if agent_name in self.agents_capabilities:
            examples = self.agents_capabilities[agent_name]['examples']
            return f"您可以試試：\n• " + "\n• ".join(examples[:3])
        return ""


# 創建全局實例
ai_intent_analyzer = AIIntentAnalyzer()
