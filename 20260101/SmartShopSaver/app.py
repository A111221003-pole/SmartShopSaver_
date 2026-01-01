# app.py - SmartShopSaver LINE Bot 主應用程式
"""
SmartShopSaver - AI 驅動的智能購物助理
✅ 中文回覆 + AI 智能建議
✅ 非同步 webhook + 健康檢查
✅ Cloud Run / Heroku 相容
"""

import sys
import os
import threading
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, make_response, redirect
from dotenv import load_dotenv

load_dotenv()

# ========== 模組路徑修復 ==========
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# ========== LINE Bot SDK ==========
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ========== 設定 ==========
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    logger.error("❌ 缺少 LINE Bot 設定！請檢查環境變數")

app = Flask(__name__)
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(CHANNEL_SECRET) if CHANNEL_SECRET else None

# ========== MongoDB ==========
db = None
db_connected = False

try:
    from utils.database import get_db_manager
    db = get_db_manager()
    db_connected = True
    logger.info("✅ MongoDB 連接成功")
except Exception as e:
    logger.warning(f"⚠️ MongoDB 連接失敗: {e}")

# ========== 代理人載入 ==========
AGENT_MAPPING = {}

try:
    from agents.ai_intent_analyzer import AIIntentAnalyzer
    ai_intent_analyzer = AIIntentAnalyzer()
    logger.info("✅ AI 意圖分析器載入成功")
except Exception as e:
    logger.warning(f"⚠️ AI 意圖分析器載入失敗: {e}")
    ai_intent_analyzer = None

try:
    from agents.finance_agent import finance_agent
    AGENT_MAPPING["Finance"] = finance_agent
    logger.info("✅ 財務代理人載入成功")
except Exception as e:
    logger.warning(f"⚠️ 財務代理人載入失敗: {e}")

try:
    from agents.price_tracker_agent_improved import PriceTrackerAgent
    price_tracker_agent = PriceTrackerAgent(line_bot_api)
    AGENT_MAPPING["PriceTracker"] = price_tracker_agent
    logger.info("✅ 價格追蹤代理人載入成功")
except Exception as e:
    logger.warning(f"⚠️ 價格追蹤代理人載入失敗: {e}")

try:
    from agents.smart_recommendation_agent import smart_recommendation_agent
    AGENT_MAPPING["SmartRecommendation"] = smart_recommendation_agent
    logger.info("✅ 智能推薦代理人載入成功")
except Exception as e:
    logger.warning(f"⚠️ 智能推薦代理人載入失敗: {e}")

try:
    from agents.product_review_agent_improved import product_review_agent
    AGENT_MAPPING["ProductReview"] = product_review_agent
    logger.info("✅ 產品評論代理人載入成功")
except Exception as e:
    logger.warning(f"⚠️ 產品評論代理人載入失敗: {e}")

try:
    from agents.gmail_integration_agent import GmailIntegrationAgent
    gmail_agent = GmailIntegrationAgent()
    AGENT_MAPPING["Gmail"] = gmail_agent
    logger.info("✅ Gmail 代理人載入成功")
except Exception as e:
    logger.warning(f"⚠️ Gmail 代理人載入失敗: {e}")


# ========== 訊息處理 ==========
def _add_intelligent_suggestions(agent_name: str, response: str) -> str:
    """自動加上 💡 建議功能"""
    suggestions = {
        "Finance": [
            "💡 財務功能：",
            "• 查看本月支出統計",
            "• 設定預算上限",
            "• 分析消費類別"
        ],
        "ProductReview": [
            "💡 產品評論功能：",
            "• 顯示正負面評論比例",
            "• 整理主要優缺點",
            "• 比較多平台評價"
        ],
        "PriceTracker": [
            "💡 價格追蹤功能：",
            "• 設定降價通知",
            "• 追蹤歷史價格曲線",
            "• 顯示跨平台最低價"
        ],
        "Gmail": [
            "💡 Gmail 功能：",
            "• 同步購物郵件",
            "• 自動整理收據",
            "• 追蹤訂單狀態"
        ]
    }
    if "💡" in response:
        return response
    if agent_name in suggestions:
        response += "\n\n" + "\n".join(suggestions[agent_name])
    return response


def process_user_message(user_id: str, message: str) -> str:
    """處理用戶訊息"""
    try:
        # 增強口語化理解
        message = enhance_message_understanding(message)
        
        # 嘗試使用 AI 意圖分析
        if ai_intent_analyzer and OPENAI_API_KEY:
            try:
                agent_name, confidence, _ = ai_intent_analyzer.analyze_intent(message, user_id)
                logger.info(f"🧠 意圖分析: {agent_name} ({confidence:.2%})")
                
                if agent_name in AGENT_MAPPING:
                    agent = AGENT_MAPPING[agent_name]
                    response = agent.process_message(user_id, message)
                    response = _add_intelligent_suggestions(agent_name, response)
                    
                    if confidence < 0.5:
                        response += "\n\n💭 我還不太確定，您可以再多描述一點喔！"
                    
                    return response
            except Exception as e:
                logger.warning(f"AI 分析失敗，使用規則匹配: {e}")
        
        # 規則匹配（備用）
        return rule_based_routing(user_id, message)
        
    except Exception as e:
        logger.error(f"處理訊息失敗: {e}", exc_info=True)
        return "⚠️ 抱歉，目前無法理解您的需求，請稍後再試。"


def rule_based_routing(user_id: str, message: str) -> str:
    """規則匹配路由"""
    msg_lower = message.lower()
    
    # Gmail 相關
    if any(kw in msg_lower for kw in ['gmail', '郵件', '連接', '授權', '掃描']):
        if "Gmail" in AGENT_MAPPING:
            return AGENT_MAPPING["Gmail"].process_message(user_id, message)
    
    # 記帳相關
    if any(kw in msg_lower for kw in ['記帳', '支出', '花費', '預算', '本月']):
        if "Finance" in AGENT_MAPPING:
            return AGENT_MAPPING["Finance"].process_message(user_id, message)
    
    # 價格追蹤相關
    if any(kw in msg_lower for kw in ['價格', '追蹤', '比價', '查詢', '多少錢', '清單']):
        if "PriceTracker" in AGENT_MAPPING:
            return AGENT_MAPPING["PriceTracker"].process_message(user_id, message)
    
    # 評價相關
    if any(kw in msg_lower for kw in ['評價', '評論', '好不好', '值得買']):
        if "ProductReview" in AGENT_MAPPING:
            return AGENT_MAPPING["ProductReview"].process_message(user_id, message)
    
    # 推薦相關
    if any(kw in msg_lower for kw in ['推薦', '建議', '選擇']):
        if "SmartRecommendation" in AGENT_MAPPING:
            return AGENT_MAPPING["SmartRecommendation"].process_message(user_id, message)
    
    # 預設回應
    return get_help_message()


def enhance_message_understanding(msg: str) -> str:
    """增強口語化理解"""
    replacements = {
        "有啥": "有什麼", "咋樣": "怎麼樣", "啥時候": "什麼時候",
        "多少$": "多少錢", "多少￥": "多少錢", "想買個": "我想買",
        "想要個": "我想要", "幫我看看": "請幫我查詢", "有沒有": "是否有",
        "好不好用": "評價如何"
    }
    for old, new in replacements.items():
        msg = msg.replace(old, new)
    return msg


def get_help_message() -> str:
    """取得幫助訊息"""
    return """👋 您好！我是 SmartShopSaver 智能購物助手！

🔍 **比價功能**
• 查詢 iPhone 15 價格
• 追蹤 PS5 目標價格 15000

💰 **記帳功能**
• 記帳 午餐 150
• 本月支出

📧 **Gmail 自動記帳**
• 連接 Gmail
• 掃描郵件

🤖 **AI 顧問**
• 推薦電競滑鼠
• AirPods Pro 評價

輸入任何問題，我會盡力幫助您！"""


# ========== Flask 路由 ==========
@app.route("/")
@app.route("/health")
def health():
    """健康檢查"""
    return {
        "status": "ok",
        "message": "SmartShopSaver is running",
        "db_connected": db_connected,
        "ai_enabled": bool(OPENAI_API_KEY),
        "agents_loaded": list(AGENT_MAPPING.keys())
    }, 200


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhook"""
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    
    # 非同步處理
    threading.Thread(target=process_webhook, args=(body, signature)).start()
    return "OK", 200


def process_webhook(body, signature):
    """處理 Webhook"""
    try:
        if handler:
            handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("❌ Invalid signature")
    except Exception as e:
        logger.error(f"Webhook 處理錯誤: {e}", exc_info=True)


if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        """處理文字訊息"""
        try:
            user_id = event.source.user_id
            text = event.message.text.strip()
            reply_token = event.reply_token
            
            logger.info(f"📨 收到訊息: {text} from {user_id}")
            
            # 更新用戶活動
            if db_connected and db:
                try:
                    db.update_user_activity(user_id)
                    if not db.get_user(user_id):
                        try:
                            profile = line_bot_api.get_profile(user_id)
                            db.create_user(user_id, profile.display_name)
                        except:
                            db.create_user(user_id, "LINE用戶")
                except Exception as e:
                    logger.warning(f"用戶資料處理失敗: {e}")
            
            # 處理訊息
            response = process_user_message(user_id, text)
            
            # 夜間提醒
            hour = datetime.now().hour
            if hour >= 22 or hour < 5:
                response += "\n\n🌙 夜深了，記得早點休息喔！"
            
            # 回覆訊息（處理超長訊息）
            MAX_LENGTH = 4900
            if len(response) > MAX_LENGTH:
                parts = [response[i:i+MAX_LENGTH] for i in range(0, len(response), MAX_LENGTH)]
                line_bot_api.reply_message(reply_token, TextSendMessage(text=parts[0]))
                for part in parts[1:]:
                    line_bot_api.push_message(user_id, TextSendMessage(text=part))
            else:
                line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
            
            logger.info(f"✅ 已回覆 {user_id}")
            
        except Exception as e:
            logger.error(f"訊息處理失敗: {e}", exc_info=True)
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="🤖 系統暫時忙碌，請稍後再試一次喔～")
                )
            except:
                pass


# ========== Gmail OAuth 路由 ==========
@app.route("/google/start", methods=["GET"])
def google_oauth_start():
    """Gmail OAuth 入口"""
    uid = request.args.get("uid", "")
    if not uid:
        return "缺少用戶 ID", 400
    
    try:
        from utils.mail_utils.gmail_utils import start_google_oauth
        
        base_url = (os.getenv("PUBLIC_BASE_URL") or request.url_root).rstrip("/")
        redirect_uri = f"{base_url}/google/callback"
        
        result = start_google_oauth(uid, redirect_uri)
        auth_url = result[0] if isinstance(result, tuple) else result
        
        return f"""
        <html>
        <head><meta charset="utf-8"><title>連結 Gmail</title></head>
        <body style="font-family:Arial;text-align:center;margin-top:100px;">
            <h1>📧 連結 Gmail 帳號</h1>
            <p>請點擊下方按鈕授權</p>
            <a href="{auth_url}" style="display:inline-block;padding:12px 24px;
               background:#1a73e8;color:white;text-decoration:none;border-radius:8px;">
               使用 Google 帳號登入
            </a>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"OAuth 啟動失敗: {e}")
        return f"<h3>❌ 無法建立授權連結</h3><p>{e}</p>", 500


@app.route("/google/callback", methods=["GET"])
def google_oauth_callback():
    """Gmail OAuth 回調"""
    uid = request.args.get("state", "")
    code = request.args.get("code", "")
    
    if not uid or not code:
        return "授權參數缺失", 400
    
    try:
        from utils.mail_utils.gmail_utils import finish_google_oauth
        
        base_url = (os.getenv("PUBLIC_BASE_URL") or request.url_root).rstrip("/")
        if base_url.startswith("http://"):
            base_url = "https://" + base_url[7:]
        redirect_uri = f"{base_url}/google/callback"
        
        finish_google_oauth(code, redirect_uri, uid)
        
        return """
        <html>
        <head><meta charset="utf-8"><title>授權成功</title></head>
        <body style="font-family:Arial;text-align:center;margin-top:100px;">
            <h1>✅ 授權成功！</h1>
            <p>請返回 LINE 使用 Gmail 功能</p>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"OAuth 回調失敗: {e}")
        return f"<h3>❌ 授權失敗</h3><p>{e}</p>", 400


# ========== 主程式 ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    print("=" * 60)
    print("🚀 SmartShopSaver LINE Bot")
    print(f"🌐 運行於 http://0.0.0.0:{port}")
    print("=" * 60)
    print(f"✅ 資料庫: {'已連接' if db_connected else '未連接'}")
    print(f"✅ AI 模式: {'已啟用' if OPENAI_API_KEY else '未啟用'}")
    print(f"✅ 載入代理人: {list(AGENT_MAPPING.keys())}")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=False)
