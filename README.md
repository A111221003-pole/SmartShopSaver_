# SmartShopSaver 🛒💰

智能購物助手 LINE Bot - 結合 AI 技術的比價、記帳、購物建議平台

## ✨ 功能特色

### 🔍 智能比價
- 多平台商品搜尋（PChome、MOMO、蝦皮）
- 即時價格追蹤與降價通知
- 目標價格設定與監控

### 💸 自動記帳
- Gmail 購物郵件自動識別
- AI 智能分類消費類別
- 月度支出統計與分析

### 🤖 AI 購物顧問
- GPT 驅動的商品推薦
- 產品評價分析
- 個人化購物建議

### 📊 財務管理
- 支出追蹤與分類
- 預算設定與監控
- 消費趨勢分析

## 🏗️ 專案結構

```
SmartShopSaver/
├── app.py                    # Flask 主應用程式
├── start.py                  # 智能啟動腳本
├── requirements.txt          # Python 依賴套件
├── Dockerfile               # Docker 容器配置
├── Procfile                 # Heroku/Cloud Run 部署配置
├── .env.example             # 環境變數範例
├── .gitignore               # Git 忽略規則
│
├── agents/                  # AI 代理人模組
│   ├── __init__.py
│   ├── base_agent.py                    # 代理人基礎類別
│   ├── ai_intent_analyzer.py            # AI 意圖分析器
│   ├── finance_agent.py                 # 財務管理代理人
│   ├── gmail_integration_agent.py       # Gmail 整合代理人
│   ├── gmail_mongodb_agent.py           # Gmail MongoDB 版本
│   ├── price_tracker_agent_improved.py  # 價格追蹤代理人
│   ├── product_review_agent_improved.py # 產品評論代理人
│   ├── smart_recommendation_agent.py    # 智能推薦代理人
│   ├── multi_platform_search.py         # 多平台搜尋
│   ├── response_formatter.py            # 回應格式化工具
│   └── mail_agents/                     # 郵件處理子代理人
│       ├── __init__.py
│       ├── expense_agent.py
│       ├── gmail_agent.py
│       └── purchase_query_agent.py
│
├── utils/                   # 工具模組
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── database.py         # MongoDB 資料庫管理
│   ├── logger.py           # 日誌管理
│   └── mail_utils/         # 郵件工具
│       ├── __init__.py
│       ├── gmail_utils.py
│       └── mongodb_adapter.py
│
└── docs/                    # 文件
    └── SETUP.md            # 安裝設定指南
```

## 🚀 快速開始

### 1. 環境準備

```bash
# 複製專案
git clone https://github.com/YOUR_USERNAME/SmartShopSaver.git
cd SmartShopSaver

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 2. 環境變數設定

```bash
cp .env.example .env
# 編輯 .env 填入實際值
```

必要的環境變數：
```env
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
CHANNEL_SECRET=your_line_channel_secret
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
OPENAI_API_KEY=your_openai_api_key  # 選用但建議
```

### 3. 啟動服務

```bash
python app.py
# 或使用智能啟動
python start.py
```

## 📱 使用說明

加入 LINE Bot 好友後，可以使用以下功能：

### 比價功能
```
查詢 iPhone 15 價格
追蹤 PS5 目標價格 15000
我的追蹤清單
```

### 記帳功能
```
記帳 午餐 150
本月支出
設定預算 30000
```

### Gmail 自動記帳
```
連接 Gmail
掃描郵件
消費統計
```

### AI 推薦
```
推薦電競滑鼠
RTX 4070 評價
筆電選購建議
```

## 🔧 技術架構

- **後端框架**: Flask + Gunicorn
- **資料庫**: MongoDB Atlas
- **AI 引擎**: OpenAI GPT-4o
- **訊息平台**: LINE Messaging API
- **部署**: Docker / Cloud Run / Heroku

## 📊 資料庫結構

### Collections
- `users` - 用戶資料
- `products` - 商品資料
- `price_history` - 價格歷史
- `user_tracking` - 用戶追蹤
- `expenses` - 支出記錄
- `shopping_records` - 購物記錄

## 🔐 安全性

- 所有 API 金鑰透過環境變數管理
- MongoDB 連接使用 TLS 加密
- Gmail OAuth 2.0 安全授權
- 不儲存敏感的原始郵件內容

## 📖 文件

| 文件 | 說明 |
|------|------|
| [USER_GUIDE.md](docs/USER_GUIDE.md) | 使用者操作手冊 |
| [SETUP.md](docs/SETUP.md) | 安裝與設定指南 |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | 部署指南 |
| [API.md](docs/API.md) | API 文件 |

## 📄 授權
世新大學李柏諺

MIT License

## 🤝 貢獻
世新大學
歡迎提交 Issue 和 Pull Request！

## 📞 聯絡

如有問題，請透過 GitHub Issues 回報。
