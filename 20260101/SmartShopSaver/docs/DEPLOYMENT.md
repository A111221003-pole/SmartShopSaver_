# SmartShopSaver 部署指南

## 📚 目錄

1. [部署方式總覽](#部署方式總覽)
2. [Google Cloud Run 部署](#google-cloud-run-部署)
3. [Heroku 部署](#heroku-部署)
4. [Docker 本地部署](#docker-本地部署)
5. [傳統伺服器部署](#傳統伺服器部署)
6. [LINE Bot 設定](#line-bot-設定)
7. [MongoDB Atlas 設定](#mongodb-atlas-設定)
8. [Gmail API 設定](#gmail-api-設定)
9. [部署後檢查](#部署後檢查)
10. [常見問題排解](#常見問題排解)

---

## 部署方式總覽

| 方式 | 難度 | 成本 | 適合對象 |
|------|------|------|----------|
| Google Cloud Run | ⭐⭐ | 免費額度充足 | 推薦大多數用戶 |
| Heroku | ⭐ | 免費/付費方案 | 快速測試 |
| Docker | ⭐⭐⭐ | 取決於主機 | 自有伺服器 |
| 傳統伺服器 | ⭐⭐⭐ | 取決於主機 | 進階用戶 |

---

## Google Cloud Run 部署

### 前置準備

1. 建立 [Google Cloud 帳號](https://cloud.google.com/)
2. 安裝 [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3. 建立專案並啟用 Cloud Run API

### 步驟

#### 1. 登入 Google Cloud

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 2. 建立 Docker 映像

```bash
# 在專案根目錄執行
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/smartshopsaver
```

#### 3. 部署到 Cloud Run

```bash
gcloud run deploy smartshopsaver \
  --image gcr.io/YOUR_PROJECT_ID/smartshopsaver \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars "CHANNEL_ACCESS_TOKEN=xxx,CHANNEL_SECRET=xxx,MONGODB_URI=xxx,OPENAI_API_KEY=xxx"
```

#### 4. 取得服務網址

部署完成後會顯示服務網址，例如：
```
https://smartshopsaver-xxxxxxxxxx-de.a.run.app
```

#### 5. 設定 LINE Webhook

將上述網址加上 `/callback` 設定為 LINE Bot 的 Webhook URL：
```
https://smartshopsaver-xxxxxxxxxx-de.a.run.app/callback
```

### 環境變數設定（Cloud Run Console）

也可以在 Cloud Run Console 設定環境變數：

1. 進入 Cloud Run Console
2. 選擇服務 → 編輯並部署新修訂版本
3. 在「變數與密鑰」區塊新增環境變數

---

## Heroku 部署

### 前置準備

1. 建立 [Heroku 帳號](https://heroku.com/)
2. 安裝 [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

### 步驟

#### 1. 登入 Heroku

```bash
heroku login
```

#### 2. 建立應用程式

```bash
heroku create smartshopsaver-your-name
```

#### 3. 設定環境變數

```bash
heroku config:set CHANNEL_ACCESS_TOKEN=your_token
heroku config:set CHANNEL_SECRET=your_secret
heroku config:set MONGODB_URI=your_mongodb_uri
heroku config:set OPENAI_API_KEY=your_openai_key
heroku config:set PUBLIC_BASE_URL=https://smartshopsaver-your-name.herokuapp.com
```

#### 4. 部署

```bash
git push heroku main
```

#### 5. 檢查日誌

```bash
heroku logs --tail
```

---

## Docker 本地部署

### 前置準備

1. 安裝 [Docker](https://docs.docker.com/get-docker/)
2. 安裝 [Docker Compose](https://docs.docker.com/compose/install/)（選用）

### 步驟

#### 1. 建立 Docker 映像

```bash
docker build -t smartshopsaver .
```

#### 2. 執行容器

```bash
docker run -d \
  -p 8080:8080 \
  -e CHANNEL_ACCESS_TOKEN=xxx \
  -e CHANNEL_SECRET=xxx \
  -e MONGODB_URI=xxx \
  -e OPENAI_API_KEY=xxx \
  -e PUBLIC_BASE_URL=https://your-domain.com \
  --name smartshopsaver \
  smartshopsaver
```

#### 3. 使用 Docker Compose（推薦）

建立 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  smartshopsaver:
    build: .
    ports:
      - "8080:8080"
    environment:
      - CHANNEL_ACCESS_TOKEN=${CHANNEL_ACCESS_TOKEN}
      - CHANNEL_SECRET=${CHANNEL_SECRET}
      - MONGODB_URI=${MONGODB_URI}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PUBLIC_BASE_URL=${PUBLIC_BASE_URL}
    restart: unless-stopped
```

執行：

```bash
docker-compose up -d
```

---

## 傳統伺服器部署

### 前置準備

- Ubuntu 20.04+ 或 CentOS 8+
- Python 3.11+
- Nginx（反向代理）
- SSL 證書（Let's Encrypt）

### 步驟

#### 1. 安裝依賴

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv nginx certbot python3-certbot-nginx
```

#### 2. 建立專案目錄

```bash
mkdir -p /var/www/smartshopsaver
cd /var/www/smartshopsaver
git clone https://github.com/YOUR_USERNAME/SmartShopSaver.git .
```

#### 3. 建立虛擬環境

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. 設定環境變數

```bash
cp .env.example .env
nano .env  # 編輯填入實際值
```

#### 5. 建立 Systemd 服務

建立 `/etc/systemd/system/smartshopsaver.service`：

```ini
[Unit]
Description=SmartShopSaver LINE Bot
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/smartshopsaver
Environment="PATH=/var/www/smartshopsaver/venv/bin"
EnvironmentFile=/var/www/smartshopsaver/.env
ExecStart=/var/www/smartshopsaver/venv/bin/gunicorn -w 4 -b 127.0.0.1:8080 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

啟動服務：

```bash
sudo systemctl daemon-reload
sudo systemctl enable smartshopsaver
sudo systemctl start smartshopsaver
```

#### 6. 設定 Nginx

建立 `/etc/nginx/sites-available/smartshopsaver`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

啟用網站：

```bash
sudo ln -s /etc/nginx/sites-available/smartshopsaver /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. 設定 SSL

```bash
sudo certbot --nginx -d your-domain.com
```

---

## LINE Bot 設定

### 1. 建立 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立 Provider（如果沒有）
3. 建立 Messaging API Channel

### 2. 取得憑證

在 Channel 設定頁面取得：
- **Channel Secret**：在 Basic settings 頁籤
- **Channel Access Token**：在 Messaging API 頁籤（點擊 Issue）

### 3. 設定 Webhook

1. 在 Messaging API 頁籤
2. 設定 Webhook URL：`https://your-domain.com/callback`
3. 開啟「Use webhook」
4. 關閉「Auto-reply messages」
5. 關閉「Greeting messages」（或自訂）

### 4. 測試 Webhook

點擊「Verify」按鈕測試連線。

---

## MongoDB Atlas 設定

### 1. 建立帳號

前往 [MongoDB Atlas](https://www.mongodb.com/atlas) 建立帳號。

### 2. 建立叢集

1. 選擇 Free Tier（M0）
2. 選擇雲端供應商和區域（建議 GCP asia-east1）
3. 命名叢集

### 3. 設定資料庫存取

1. Database Access → Add New Database User
2. 選擇 Password 驗證
3. 設定用戶名和密碼
4. 權限選擇 Read and write to any database

### 4. 設定網路存取

1. Network Access → Add IP Address
2. 開發階段可選 Allow Access from Anywhere（0.0.0.0/0）
3. 生產環境建議限制 IP

### 5. 取得連接字串

1. Clusters → Connect → Connect your application
2. 複製連接字串
3. 替換 `<password>` 為實際密碼

**注意**：如果密碼包含特殊字元，需要 URL 編碼：
- `>` → `%3E`
- `<` → `%3C`
- `@` → `%40`
- `:` → `%3A`

---

## Gmail API 設定

### 1. 建立 Google Cloud 專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案

### 2. 啟用 Gmail API

1. APIs & Services → Library
2. 搜尋「Gmail API」
3. 點擊 Enable

### 3. 設定 OAuth 同意畫面

1. APIs & Services → OAuth consent screen
2. 選擇 External
3. 填寫應用程式名稱、支援信箱
4. 新增 Scopes：
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/userinfo.email`

### 4. 建立 OAuth 憑證

1. APIs & Services → Credentials
2. Create Credentials → OAuth client ID
3. 應用程式類型：Web application
4. 新增授權重新導向 URI：
   - `https://your-domain.com/google/callback`
5. 下載 JSON 檔案
6. 重新命名為 `client_secret.json`
7. 上傳到伺服器

---

## 部署後檢查

### 檢查清單

- [ ] LINE Webhook 驗證成功
- [ ] 傳送訊息有回應
- [ ] MongoDB 連線正常
- [ ] OpenAI API 運作正常（如有設定）
- [ ] Gmail OAuth 流程正常（如有設定）
- [ ] SSL 證書有效

### 健康檢查端點

```bash
curl https://your-domain.com/health
# 應返回: {"status": "ok", "message": "SmartShopSaver is running"}
```

### 日誌檢查

```bash
# Cloud Run
gcloud run services logs read smartshopsaver

# Heroku
heroku logs --tail

# Docker
docker logs smartshopsaver

# Systemd
sudo journalctl -u smartshopsaver -f
```

---

## 常見問題排解

### LINE Webhook 驗證失敗

1. 確認 URL 正確（包含 `/callback`）
2. 確認 SSL 證書有效
3. 確認服務正在運行
4. 檢查 CHANNEL_SECRET 是否正確

### MongoDB 連線失敗

1. 確認連接字串格式正確
2. 確認密碼已 URL 編碼
3. 確認 IP 白名單設定
4. 確認用戶權限

### Gmail OAuth 失敗

1. 確認 `client_secret.json` 存在
2. 確認重新導向 URI 設定正確
3. 確認 PUBLIC_BASE_URL 設定
4. 檢查 OAuth 同意畫面狀態

### 訊息沒有回應

1. 檢查日誌是否有錯誤
2. 確認環境變數設定正確
3. 確認代理人註冊成功
4. 測試資料庫連線
