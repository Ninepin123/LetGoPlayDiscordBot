# 🚀 跨平台部署指南

本指南說明如何在不同作業系統和環境中部署 Discord Bot。

---

## 📋 目錄

- [Windows 部署](#windows-部署)
- [Linux 部署](#linux-部署)
- [Docker 部署](#docker-部署)
- [雲端伺服器部署](#雲端伺服器部署)

---

## 🪟 Windows 部署

### 安裝步驟

1. **安裝 Python 3.9+**
   ```bash
   # 從 https://www.python.org/downloads/ 下載並安裝
   ```

2. **安裝依賴套件**
   ```bash
   pip install -r requirements.txt
   ```

3. **安裝轉換工具（擇一）**
   
   **選項 A：LibreOffice（推薦）**
   - 下載：https://www.libreoffice.org/download/download/
   - 使用預設安裝路徑
   
   **選項 B：Microsoft Office**
   - 確保已安裝 Word 和 PowerPoint
   - 需要有效授權

4. **設定環境變數**
   ```bash
   # 建立 .env 檔案
   echo DISCORD_BOT_TOKEN=你的_Bot_Token > .env
   ```

5. **啟動 Bot**
   ```bash
   python main.py
   ```

---

## 🐧 Linux 部署

### Ubuntu/Debian

```bash
# 1. 更新系統
sudo apt update && sudo apt upgrade -y

# 2. 安裝 Python 和 pip
sudo apt install python3 python3-pip -y

# 3. 安裝 LibreOffice
sudo apt install libreoffice -y

# 4. 克隆專案
git clone https://github.com/your-repo/discord_bot.git
cd discord_bot

# 5. 安裝 Python 依賴
pip3 install -r requirements.txt

# 6. 設定環境變數
nano .env
# 加入: DISCORD_BOT_TOKEN=你的_Token

# 7. 啟動 Bot
python3 main.py
```

### CentOS/RHEL

```bash
# 1. 安裝 EPEL Repository
sudo yum install epel-release -y

# 2. 安裝 Python 和 pip
sudo yum install python3 python3-pip -y

# 3. 安裝 LibreOffice
sudo yum install libreoffice -y

# 4. 其他步驟同 Ubuntu
```

### Arch Linux

```bash
# 1. 安裝套件
sudo pacman -S python python-pip libreoffice-fresh

# 2. 其他步驟同 Ubuntu
```

---

## 🐳 Docker 部署

### Dockerfile

建立 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製專案檔案
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 啟動 Bot
CMD ["python", "main.py"]
```

### docker-compose.yml

建立 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  discord-bot:
    build: .
    container_name: discord-bot
    restart: unless-stopped
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
    volumes:
      - ./events.json:/app/events.json
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

### 使用 Docker Compose

```bash
# 1. 建立 .env 檔案
echo "DISCORD_BOT_TOKEN=你的_Token" > .env

# 2. 啟動容器
docker-compose up -d

# 3. 查看日誌
docker-compose logs -f

# 4. 停止容器
docker-compose down
```

### 使用 Docker（不用 Compose）

```bash
# 1. 建置映像
docker build -t discord-bot .

# 2. 執行容器
docker run -d \
  --name discord-bot \
  --restart unless-stopped \
  -e DISCORD_BOT_TOKEN="你的_Token" \
  -v $(pwd)/events.json:/app/events.json \
  discord-bot

# 3. 查看日誌
docker logs -f discord-bot

# 4. 停止容器
docker stop discord-bot
docker rm discord-bot
```

---

## ☁️ 雲端伺服器部署

### AWS EC2

```bash
# 1. 啟動 Ubuntu EC2 實例

# 2. SSH 連線
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. 安裝依賴（同 Linux 部署）
sudo apt update && sudo apt install python3 python3-pip libreoffice -y

# 4. 克隆專案並設定
git clone https://github.com/your-repo/discord_bot.git
cd discord_bot
pip3 install -r requirements.txt

# 5. 使用 systemd 設定自動啟動
sudo nano /etc/systemd/system/discord-bot.service
```

systemd 服務檔案：

```ini
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/discord_bot
Environment="DISCORD_BOT_TOKEN=你的_Token"
ExecStart=/usr/bin/python3 /home/ubuntu/discord_bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

啟動服務：

```bash
# 重新載入 systemd
sudo systemctl daemon-reload

# 啟動服務
sudo systemctl start discord-bot

# 設定開機自動啟動
sudo systemctl enable discord-bot

# 查看狀態
sudo systemctl status discord-bot

# 查看日誌
sudo journalctl -u discord-bot -f
```

### Google Cloud Platform (GCP)

```bash
# 1. 建立 Compute Engine 實例（Ubuntu）

# 2. SSH 連線（使用 GCP Console 或 gcloud）
gcloud compute ssh your-instance-name

# 3. 其餘步驟同 AWS EC2
```

### Azure VM

```bash
# 1. 建立 Ubuntu VM

# 2. SSH 連線
ssh azureuser@your-vm-ip

# 3. 其餘步驟同 AWS EC2
```

### Heroku（免費層級）

建立 `Procfile`：

```
worker: python main.py
```

建立 `runtime.txt`：

```
python-3.11.0
```

部署步驟：

```bash
# 1. 安裝 Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# 2. 登入
heroku login

# 3. 建立應用程式
heroku create your-bot-name

# 4. 新增 buildpack（LibreOffice）
heroku buildpacks:add https://github.com/rishson/heroku-buildpack-libreoffice.git
heroku buildpacks:add heroku/python

# 5. 設定環境變數
heroku config:set DISCORD_BOT_TOKEN="你的_Token"

# 6. 部署
git push heroku main

# 7. 啟動 worker
heroku ps:scale worker=1

# 8. 查看日誌
heroku logs --tail
```

### Railway

```bash
# 1. 前往 https://railway.app/
# 2. 連結 GitHub 儲存庫
# 3. 設定環境變數 DISCORD_BOT_TOKEN
# 4. 自動部署
```

### Replit

1. 前往 https://replit.com/
2. 建立新的 Python Repl
3. 上傳專案檔案
4. 在 Secrets 中設定 `DISCORD_BOT_TOKEN`
5. 點擊 Run

---

## 🔍 系統需求比較

| 平台 | Python | LibreOffice | Microsoft Office | 備註 |
|------|--------|-------------|------------------|------|
| Windows | ✅ | ✅ | ✅ | 所有方法都支援 |
| Linux | ✅ | ✅ | ❌ | 只能用 LibreOffice |
| Mac | ✅ | ✅ | ❌ | 只能用 LibreOffice |
| Docker | ✅ | ✅ | ❌ | 建議用 LibreOffice |

---

## 📊 效能建議

### 最低配置
- **CPU：** 1 核心
- **RAM：** 512 MB
- **儲存：** 2 GB
- **適用：** 低流量 bot

### 建議配置
- **CPU：** 2 核心
- **RAM：** 2 GB
- **儲存：** 10 GB
- **適用：** 中等流量 bot

### 生產環境
- **CPU：** 4 核心
- **RAM：** 4 GB
- **儲存：** 20 GB
- **適用：** 高流量 bot

---

## 🛡️ 安全性建議

1. **環境變數**
   - 永遠使用 `.env` 檔案存放 Token
   - 不要將 `.env` 加入 Git

2. **防火牆**
   ```bash
   # Linux: 只開放 SSH（如果需要）
   sudo ufw allow ssh
   sudo ufw enable
   ```

3. **自動更新**
   ```bash
   # Ubuntu: 啟用自動更新
   sudo apt install unattended-upgrades -y
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

4. **限制權限**
   ```bash
   # 建立專用使用者
   sudo useradd -m -s /bin/bash discord-bot
   sudo su - discord-bot
   ```

---

## 🔧 疑難排解

### LibreOffice 找不到

**Linux:**
```bash
# 檢查是否已安裝
which soffice
libreoffice --version

# 重新安裝
sudo apt install --reinstall libreoffice
```

**Docker:**
```bash
# 進入容器檢查
docker exec -it discord-bot bash
which soffice
```

### 權限問題

```bash
# 給予執行權限
chmod +x main.py

# 檢查檔案擁有者
ls -la

# 修改擁有者
sudo chown -R your-user:your-group .
```

### 記憶體不足

```bash
# 檢查記憶體使用
free -h

# 增加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📝 維護腳本

### 自動重啟腳本

建立 `restart.sh`：

```bash
#!/bin/bash
echo "重啟 Discord Bot..."
pkill -f main.py
sleep 2
nohup python3 main.py > bot.log 2>&1 &
echo "Bot 已重啟"
```

給予執行權限：

```bash
chmod +x restart.sh
```

### 備份腳本

建立 `backup.sh`：

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR
cp events.json $BACKUP_DIR/events_$DATE.json
echo "已備份到 $BACKUP_DIR/events_$DATE.json"
```

### Crontab 定時任務

```bash
# 編輯 crontab
crontab -e

# 每天凌晨 3 點備份
0 3 * * * /path/to/backup.sh

# 每小時檢查 bot 是否運行
0 * * * * pgrep -f main.py || /path/to/restart.sh
```

---

## 🌐 多實例部署

如果需要運行多個 bot 實例：

```bash
# 使用不同的工作目錄
cd /path/to/bot1
python3 main.py &

cd /path/to/bot2
python3 main.py &
```

或使用 Docker Compose：

```yaml
version: '3.8'

services:
  bot1:
    build: .
    environment:
      - DISCORD_BOT_TOKEN=${BOT1_TOKEN}
    volumes:
      - ./bot1_events.json:/app/events.json

  bot2:
    build: .
    environment:
      - DISCORD_BOT_TOKEN=${BOT2_TOKEN}
    volumes:
      - ./bot2_events.json:/app/events.json
```

---

## 📚 相關連結

- [Docker 官網](https://www.docker.com/)
- [AWS EC2 文件](https://aws.amazon.com/ec2/)
- [Heroku 文件](https://devcenter.heroku.com/)
- [LibreOffice 下載](https://www.libreoffice.org/download/download/)

---

**最後更新：** 2025-10-16


