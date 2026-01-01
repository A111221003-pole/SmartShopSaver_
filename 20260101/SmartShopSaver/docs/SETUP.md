# SmartShopSaver 安裝與設定指南

## 📋 目錄

1. [系統需求](#系統需求)
2. [安裝步驟](#安裝步驟)
3. [環境變數設定](#環境變數設定)
4. [LINE Bot 設定](#line-bot-設定)
5. [MongoDB 設定](#mongodb-設定)
6. [Gmail OAuth 設定](#gmail-oauth-設定)
7. [部署方式](#部署方式)
8. [常見問題](#常見問題)

---

## 系統需求

- Python 3.11 或更高版本
- MongoDB Atlas 帳號（免費版即可）
- LINE Developers 帳號
- OpenAI API Key（選用但強烈建議）
- Google Cloud Console 帳號（若需 Gmail 功能）

---

## 安裝步驟

### 1. 複製專案

```bash
git clone https://github.com/YOUR_USERNAME/SmartShopSaver.git
cd SmartShopSaver
```

### 2. 建立虛擬環境（建議）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 4. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env 檔案，填入實際值
```

### 5. 啟動服務

```bash
python app.py
# 或使用智能啟動腳本
python start.py
```

---

## 環境變數設定

建立 `.env` 檔案並設定以下變數：

### 必要設定

```env
# LINE Bot（必要）
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
CHANNEL_SECRET=your_line_channel_secret

# MongoDB（必要）
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=smartshopsaver
```

### 建議設定

```env
# OpenAI（強烈建議，啟用 AI 功能）
OPENAI_API_KEY=your_openai_api_key
GPT_MODEL=gpt-4o-mini
```

### 選用設定

```env
# Gmail OAuth（選用）
PUBLIC_BASE_URL=https://your-domain.com
GMAIL_CLIENT_SECRET=client_secret.json

# Gmail Push 通知（進階）
GMAIL_WATCH_TOPIC=projects/your-project/topics/your-topic
PUBSUB_VERIFY_TOKEN=your_random_token
```

---

## LINE Bot 設定

### 1. 建立 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立 Provider 和 Channel（Messaging API）
3. 取得 Channel Access Token 和 Channel Secret

### 2. 設定 Webhook

1. 在 Channel 設定中啟用 Webhook
2. 設定 Webhook URL：`https://your-domain.com/callback`
3. 關閉自動回覆訊息

### 3. 加入好友

掃描 QR Code 或搜尋 Bot ID 加入好友即可開始使用。

---

## MongoDB 設定

### 1. 建立 MongoDB Atlas 帳號

1. 前往 [MongoDB Atlas](https://www.mongodb.com/atlas)
2. 建立免費叢集

### 2. 設定資料庫存取

1. 建立資料庫使用者
2. 設定 IP 白名單（開發時可設定 0.0.0.0/0）
3. 取得連接字串

### 3. 連接字串格式

```
mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
```

**注意**：如果密碼包含特殊字元，需要進行 URL 編碼：
- `>` → `%3E`
- `<` → `%3C`
- `@` → `%40`

---

## Gmail OAuth 設定

### 1. 建立 Google Cloud 專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案

### 2. 啟用 Gmail API

1. 在 API 程式庫中搜尋「Gmail API」
2. 啟用 API

### 3. 建立 OAuth 2.0 憑證

1. 前往「憑證」頁面
2. 建立 OAuth 2.0 用戶端 ID
3. 應用程式類型選擇「網頁應用程式」
4. 設定授權重新導向 URI：
   - `https://your-domain.com/google/callback`

### 4. 下載憑證

1. 下載 JSON 檔案
2. 重新命名為 `client_secret.json`
3. 放到專案根目錄

### 5. 設定 OAuth 同意畫面

1. 設定應用程式名稱和圖示
2. 新增範圍：
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/userinfo.email`

---

## 部署方式

### 方式一：Heroku

```bash
heroku create your-app-name
heroku config:set CHANNEL_ACCESS_TOKEN=xxx
heroku config:set CHANNEL_SECRET=xxx
heroku config:set MONGODB_URI=xxx
heroku config:set OPENAI_API_KEY=xxx
git push heroku main
```

### 方式二：Google Cloud Run

```bash
# 建立映像
gcloud builds submit --tag gcr.io/PROJECT_ID/smartshopsaver

# 部署
gcloud run deploy smartshopsaver \
  --image gcr.io/PROJECT_ID/smartshopsaver \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated
```

### 方式三：Docker

```bash
# 建立映像
docker build -t smartshopsaver .

# 執行
docker run -p 8080:8080 --env-file .env smartshopsaver
```

---

## 常見問題

### Q: MongoDB 連接失敗？

1. 檢查連接字串格式是否正確
2. 確認 IP 白名單設定
3. 確認使用者密碼是否包含特殊字元（需 URL 編碼）

### Q: LINE Bot 沒有回應？

1. 確認 Webhook URL 設定正確
2. 檢查 HTTPS 證書是否有效
3. 查看伺服器日誌確認錯誤

### Q: AI 功能無法使用？

1. 確認 OPENAI_API_KEY 設定正確
2. 檢查 API 額度是否用完
3. 確認網路可以連接 OpenAI API

### Q: Gmail OAuth 失敗？

1. 確認 `client_secret.json` 檔案存在
2. 檢查重新導向 URI 設定是否正確
3. 確認 PUBLIC_BASE_URL 與實際網址一致

---

## 聯絡方式

如有問題，請透過 GitHub Issues 回報。
