# SmartShopSaver API 文件

## 📚 目錄

1. [概述](#概述)
2. [LINE Webhook API](#line-webhook-api)
3. [Gmail OAuth API](#gmail-oauth-api)
4. [代理人系統](#代理人系統)
5. [資料庫結構](#資料庫結構)
6. [錯誤處理](#錯誤處理)

---

## 概述

SmartShopSaver 是一個基於 Flask 的 LINE Bot 服務，提供以下主要 API 端點：

| 端點 | 方法 | 說明 |
|------|------|------|
| `/callback` | POST | LINE Webhook 回調 |
| `/health` | GET | 健康檢查 |
| `/google/start` | GET | 開始 Gmail OAuth |
| `/google/callback` | GET | Gmail OAuth 回調 |
| `/pubsub` | POST | Gmail Push 通知 |

---

## LINE Webhook API

### POST /callback

LINE Bot 訊息接收端點。

**Headers:**
```
X-Line-Signature: {signature}
Content-Type: application/json
```

**Request Body:**
```json
{
  "events": [
    {
      "type": "message",
      "replyToken": "xxx",
      "source": {
        "userId": "Uxxxxxxxx",
        "type": "user"
      },
      "message": {
        "type": "text",
        "text": "查詢 iPhone 15 價格"
      }
    }
  ]
}
```

**Response:**
- `200 OK` - 處理成功
- `400 Bad Request` - 簽名驗證失敗

---

## Gmail OAuth API

### GET /google/start

開始 Gmail OAuth 授權流程。

**Query Parameters:**
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `uid` | string | 是 | LINE 用戶 ID |

**Response:**
重新導向至 Google 授權頁面

**範例：**
```
GET /google/start?uid=Uxxxxxxxx
```

---

### GET /google/callback

Gmail OAuth 回調端點。

**Query Parameters:**
| 參數 | 類型 | 說明 |
|------|------|------|
| `code` | string | OAuth 授權碼 |
| `state` | string | 用戶 ID |
| `error` | string | 錯誤訊息（如果失敗）|

**Response:**
```html
<!-- 成功 -->
<h1>✅ Gmail 連接成功！</h1>
<p>您可以關閉此頁面，回到 LINE 繼續使用。</p>

<!-- 失敗 -->
<h1>❌ 授權失敗</h1>
<p>錯誤原因: {error}</p>
```

---

### POST /pubsub

Gmail Push 通知端點（用於即時郵件處理）。

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": {
    "data": "base64_encoded_data",
    "messageId": "xxx",
    "publishTime": "2024-01-01T00:00:00.000Z"
  },
  "subscription": "projects/xxx/subscriptions/xxx"
}
```

**Query Parameters:**
| 參數 | 類型 | 說明 |
|------|------|------|
| `token` | string | 驗證 Token |

**Response:**
- `200 OK` - 處理成功
- `403 Forbidden` - Token 驗證失敗

---

## 代理人系統

### 架構概述

```
┌─────────────────┐
│   LINE 訊息     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AIIntentAnalyzer│  ← 意圖分析
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│           Agent Registry            │
├─────────┬─────────┬─────────┬───────┤
│ Finance │ Price   │ Gmail   │ Smart │
│ Agent   │ Tracker │ Agent   │ Rec.  │
└─────────┴─────────┴─────────┴───────┘
```

### BaseAgent 介面

所有代理人必須實作以下方法：

```python
class BaseAgent(ABC):
    @abstractmethod
    def can_handle(self, message: str) -> bool:
        """判斷是否可以處理此訊息"""
        pass
    
    @abstractmethod
    def _process_message_internal(self, user_id: str, message: str) -> str:
        """處理訊息並返回回應"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """返回代理人可用的工具"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """返回系統提示詞"""
        pass
```

### 可用代理人

| 代理人 | 類別 | 處理的訊息類型 |
|--------|------|----------------|
| FinanceAgent | 財務管理 | 記帳、支出、預算 |
| PriceTrackerAgent | 價格追蹤 | 比價、追蹤、清單 |
| GmailIntegrationAgent | Gmail 整合 | 郵件、同步、授權 |
| SmartRecommendationAgent | 智能推薦 | 推薦、建議、比較 |
| ProductReviewAgent | 產品評論 | 評價、心得、開箱 |

### 註冊自定義代理人

```python
from agents.base_agent import BaseAgent, agent_registry

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyCustom")
    
    def can_handle(self, message: str) -> bool:
        return "自定義關鍵字" in message
    
    def _process_message_internal(self, user_id: str, message: str) -> str:
        return "自定義回應"
    
    def get_tools(self):
        return []
    
    def get_system_prompt(self):
        return "你是自定義代理人"
    
    def _create_agent(self):
        return None

# 註冊
my_agent = MyCustomAgent()
agent_registry.register("MyCustom", my_agent)
```

---

## 資料庫結構

### MongoDB Collections

#### users
```javascript
{
  "_id": ObjectId,
  "line_user_id": "Uxxxxxxxx",      // LINE 用戶 ID
  "display_name": "用戶名稱",
  "created_at": ISODate,
  "last_active": ISODate,
  "preferences": {},
  "settings": {
    "price_alert_threshold": 0.1,
    "notifications_enabled": true
  }
}
```

#### expenses
```javascript
{
  "_id": ObjectId,
  "user_id": "Uxxxxxxxx",
  "amount": 150.0,                   // 金額
  "category": "飲食",                // 分類
  "description": "午餐",             // 描述
  "source": "manual",                // 來源: manual/gmail_auto
  "shopping_record_id": ObjectId,    // 關聯購物記錄（如果有）
  "occurred_at": "2024-01-15",       // 實際發生日期
  "created_at": ISODate
}
```

#### product_name_tracking
```javascript
{
  "_id": ObjectId,
  "user_id": "Uxxxxxxxx",
  "product_name": "iPhone 15 Pro",   // 用戶輸入的名稱
  "actual_product_name": "Apple...", // 實際找到的商品
  "target_price": 35000,             // 目標價格
  "current_lowest_price": 38900,     // 目前最低價
  "lowest_price_platform": "PChome", // 最低價平台
  "lowest_price_url": "https://...", // 商品連結
  "is_active": true,
  "notification_sent": false,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

#### shopping_records
```javascript
{
  "_id": ObjectId,
  "user_id": "Uxxxxxxxx",
  "message_id": "gmail_message_id",  // Gmail 郵件 ID
  "vendor": "PChome",                // 商家
  "amount": 1500.0,                  // 金額
  "category": "購物",                // 分類
  "email_date": "2024-01-15",        // 郵件日期
  "subject": "訂單確認",             // 郵件主旨
  "snippet": "感謝您的訂購...",      // 郵件摘要
  "confidence": 0.95,                // AI 信心度
  "raw_source": "GPT",               // 分析來源
  "created_at": ISODate
}
```

#### gmail_processed
```javascript
{
  "_id": ObjectId,
  "user_id": "Uxxxxxxxx",
  "message_id": "gmail_message_id",
  "subject": "訂單確認",
  "email_date": "2024-01-15",
  "processed_at": ISODate
}
```

#### user_budget
```javascript
{
  "_id": ObjectId,
  "user_id": "Uxxxxxxxx",
  "budget": 30000,                   // 月預算
  "updated_at": ISODate
}
```

### 索引設計

```javascript
// users
db.users.createIndex({ "line_user_id": 1 }, { unique: true })

// expenses
db.expenses.createIndex({ "user_id": 1, "created_at": -1 })
db.expenses.createIndex({ "user_id": 1, "occurred_at": -1 })

// product_name_tracking
db.product_name_tracking.createIndex({ "user_id": 1, "product_name": 1 })
db.product_name_tracking.createIndex({ "user_id": 1, "is_active": 1 })

// shopping_records
db.shopping_records.createIndex({ "user_id": 1, "message_id": 1 }, { unique: true })
db.shopping_records.createIndex({ "user_id": 1, "email_date": -1 })

// gmail_processed
db.gmail_processed.createIndex({ "user_id": 1, "message_id": 1 }, { unique: true })
```

---

## 錯誤處理

### 錯誤回應格式

```python
# 一般錯誤
"❌ 系統錯誤，請稍後再試"

# 參數錯誤
"❌ 請提供商品名稱\n\n範例：追蹤 iPhone 15 Pro 目標價格 35000"

# 資料庫錯誤
"❌ 資料庫未連接，請聯繫管理員"

# API 錯誤
"❌ 無法連接到服務，請稍後再試"
```

### HTTP 狀態碼

| 狀態碼 | 說明 |
|--------|------|
| 200 | 成功 |
| 400 | 請求參數錯誤 |
| 403 | 驗證失敗 |
| 500 | 伺服器內部錯誤 |

### 日誌記錄

```python
import logging

logger = logging.getLogger(__name__)

# 記錄等級
logger.debug("詳細除錯資訊")
logger.info("一般操作資訊")
logger.warning("警告訊息")
logger.error("錯誤訊息")
```

---

## 環境變數

| 變數名 | 必填 | 說明 |
|--------|------|------|
| `CHANNEL_ACCESS_TOKEN` | ✅ | LINE Channel Access Token |
| `CHANNEL_SECRET` | ✅ | LINE Channel Secret |
| `MONGODB_URI` | ✅ | MongoDB 連接字串 |
| `OPENAI_API_KEY` | ❌ | OpenAI API Key（AI 功能需要）|
| `PUBLIC_BASE_URL` | ❌ | 公開網址（Gmail OAuth 需要）|
| `GPT_MODEL` | ❌ | GPT 模型名稱（預設 gpt-4o-mini）|
| `PORT` | ❌ | 服務端口（預設 5000）|
