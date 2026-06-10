# CabinetCraft Pro — Ubuntu 服务器部署文档

本文档说明如何在 Ubuntu 22.04/24.04 服务器上部署 CabinetCraft Pro。

## 环境要求

- Ubuntu 22.04 或 24.04 LTS
- 2GB+ RAM
- 10GB+ 磁盘空间
- 开放端口：8000（后端 API）、80（Nginx 反代）

## 一、系统准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git build-essential

# 安装 Python 3.11+（Ubuntu 22.04 默认 3.10，需升级）
sudo apt install -y python3 python3-pip python3-venv

# 验证 Python 版本（需 3.10+）
python3 --version

# 安装 Node.js 20 LTS（前端构建需要）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 验证 Node.js
node --version
npm --version
```

## 二、获取代码

```bash
# 克隆项目（替换为实际仓库地址）
cd /opt
sudo git clone https://your-repo/cabinetcraft-pro.git
sudo chown -R $USER:$USER cabinetcraft-pro
cd cabinetcraft-pro

# 或者从本地上传
# scp -r ./LLMtoThreejs user@server:/opt/cabinetcraft-pro
```

## 三、部署后端

```bash
cd /opt/cabinetcraft-pro/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 安装生产级 ASGI 服务器
pip install gunicorn uvicorn[standard]

# 配置环境变量
cp .env.example .env  # 如果有的话，否则手动创建
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./cabinet_craft.db
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4o
CORS_ORIGINS=http://localhost,http://your-server-ip,https://your-domain.com
EOF

# 初始化数据库并验证
python3 -c "from main import app; print('Backend OK')"

# 测试启动
python3 main.py
# 按 Ctrl+C 停止，接下来用 systemd 管理
```

## 四、配置 Systemd 服务

```bash
sudo tee /etc/systemd/system/cabinetcraft-backend.service > /dev/null << 'EOF'
[Unit]
Description=CabinetCraft Pro Backend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/cabinetcraft-pro/backend
Environment="PATH=/opt/cabinetcraft-pro/backend/venv/bin"
ExecStart=/opt/cabinetcraft-pro/backend/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/cabinetcraft/access.log \
    --error-logfile /var/log/cabinetcraft/error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 创建日志目录
sudo mkdir -p /var/log/cabinetcraft
sudo chown www-data:www-data /var/log/cabinetcraft

# 设置文件权限
sudo chown -R www-data:www-data /opt/cabinetcraft-pro/backend

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable cabinetcraft-backend
sudo systemctl start cabinetcraft-backend

# 检查状态
sudo systemctl status cabinetcraft-backend
```

## 五、构建前端

```bash
cd /opt/cabinetcraft-pro/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 将构建产物复制到 Nginx 目录
sudo mkdir -p /var/www/cabinetcraft
sudo cp -r dist/* /var/www/cabinetcraft/
sudo chown -R www-data:www-data /var/www/cabinetcraft
```

## 六、配置 Nginx

```bash
# 安装 Nginx
sudo apt install -y nginx

# 创建站点配置
sudo tee /etc/nginx/sites-available/cabinetcraft > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;  # 替换为你的域名

    # 前端静态文件
    root /var/www/cabinetcraft;
    index index.html;

    # 前端路由（Vue Router history 模式）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 反代
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持（AI 对话流式响应）
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # 后端健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/cabinetcraft /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 七、配置防火墙

```bash
# 如果使用 UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS（如需）
sudo ufw enable
sudo ufw status
```

## 八、验证部署

```bash
# 检查后端服务
curl http://localhost:8000/health
# 预期: {"status":"ok"}

# 检查 API 文档
curl http://localhost:8000/docs | head -5

# 检查前端
curl -I http://localhost/
# 预期: HTTP/1.1 200 OK

# 检查 API 反代
curl http://localhost/api/cabinets
# 预期: {"success":true,"data":{"items":[],"total":0}}
```

浏览器访问 `http://你的服务器IP` 即可看到 CabinetCraft Pro。

## 九、HTTPS 配置（可选）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书（替换为你的域名）
sudo certbot --nginx -d your-domain.com

# 自动续期已由 certbot 配置，验证续期
sudo certbot renew --dry-run
```

## 十、维护操作

### 查看日志

```bash
# 后端日志
sudo tail -f /var/log/cabinetcraft/error.log
sudo tail -f /var/log/cabinetcraft/access.log

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Systemd 服务日志
sudo journalctl -u cabinetcraft-backend -f
```

### 重启服务

```bash
# 重启后端
sudo systemctl restart cabinetcraft-backend

# 重启 Nginx
sudo systemctl restart nginx
```

### 更新代码

```bash
cd /opt/cabinetcraft-pro

# 拉取最新代码
git pull origin main

# 更新后端依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cabinetcraft-backend

# 重新构建前端
cd ../frontend
npm install
npm run build
sudo cp -r dist/* /var/www/cabinetcraft/
```

### 数据库备份

```bash
# 备份 SQLite 数据库
cp /opt/cabinetcraft-pro/backend/cabinet_craft.db /backup/cabinet_craft_$(date +%Y%m%d).db

# 定时备份（添加 crontab）
# 每天凌晨 3 点备份
echo "0 3 * * * cp /opt/cabinetcraft-pro/backend/cabinet_craft.db /backup/cabinet_craft_\$(date +\%Y\%m\%d).db" | crontab -
```

### 更换 LLM API Key

```bash
sudo nano /opt/cabinetcraft-pro/backend/.env
# 修改 LLM_API_KEY=...
sudo systemctl restart cabinetcraft-backend
```

## 故障排除

### 后端启动失败

```bash
# 查看详细错误
sudo systemctl status cabinetcraft-backend
sudo journalctl -u cabinetcraft-backend -n 50

# 常见原因：
# 1. 端口占用：sudo lsof -i :8000
# 2. 权限问题：sudo chown -R www-data:www-data /opt/cabinetcraft-pro/backend
# 3. 依赖缺失：cd backend && source venv/bin/activate && pip install -r requirements.txt
```

### 前端白屏

```bash
# 检查静态文件是否部署
ls /var/www/cabinetcraft/index.html

# 检查 Nginx 配置
sudo nginx -t

# 检查 API 反代是否正常
curl http://localhost/api/cabinets
```

### SSE 流式响应中断

```bash
# 检查 Nginx SSE 配置（proxy_buffering off）
sudo grep -A5 "proxy_buffering" /etc/nginx/sites-available/cabinetcraft

# 检查后端超时设置
# 在 systemd 服务中已设 --timeout 120
```

### AI 功能不工作

```bash
# 检查 API Key 配置
grep LLM_API_KEY /opt/cabinetcraft-pro/backend/.env

# 检查 LLM 连通性
curl -H "Authorization: Bearer $(grep LLM_API_KEY /opt/cabinetcraft-pro/backend/.env | cut -d= -f2)" \
     "$(grep LLM_BASE_URL /opt/cabinetcraft-pro/backend/.env | cut -d= -f2)/models"
```

## 生产环境建议

| 项目 | 建议 |
|------|------|
| Gunicorn workers | `2 × CPU核心数 + 1` |
| SQLite → PostgreSQL | 并发高时迁移至 PostgreSQL |
| 日志轮转 | 配置 logrotate 防止日志占满磁盘 |
| 监控 | 使用 `systemctl status` 或接入 Prometheus |
| 备份 | 每日自动备份数据库，保留 30 天 |
| HTTPS | 生产环境务必启用 HTTPS |
