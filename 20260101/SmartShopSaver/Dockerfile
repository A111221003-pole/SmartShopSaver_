# 使用 Python 基礎映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製程式碼
COPY . /app

# 安裝套件
RUN pip install --no-cache-dir -r requirements.txt

# 暴露 Cloud Run 預設埠
EXPOSE 8080

# 使用 Gunicorn 啟動 Flask（正式伺服器）
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
