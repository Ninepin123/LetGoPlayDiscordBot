# Discord Bot Dockerfile - 跨平台檔案轉換支援

FROM python:3.11-slim

# 設定環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安裝系統依賴和 LibreOffice
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-impress \
    libreoffice-calc \
    libreoffice-common \
    && rm -rf /var/lib/apt/lists/*

# 驗證 LibreOffice 安裝
RUN which soffice && soffice --version

# 建立工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 建立資料目錄
RUN mkdir -p /app/data

# 健康檢查（可選）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('main.py') else 1)"

# 啟動 Bot
CMD ["python", "main.py"]


