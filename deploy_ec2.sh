#!/bin/bash
# ═══════════════════════════════════════════════════
# Phase 5: EC2 Deployment Script
# HomeMade Pickles & Snacks
# Run this on your EC2 Ubuntu instance
# ═══════════════════════════════════════════════════

echo "🚀 Starting deployment of HomeMade Pickles & Snacks..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nginx git

# Create app directory
mkdir -p /home/ubuntu/pickles_snacks
cd /home/ubuntu/pickles_snacks

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Create log directory
sudo mkdir -p /var/log/pickles_snacks
sudo chown ubuntu:ubuntu /var/log/pickles_snacks

# Initialize DynamoDB tables and seed data
python config/aws_setup.py

# Setup Nginx
sudo tee /etc/nginx/sites-available/pickles > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
    }

    location /static {
        alias /home/ubuntu/pickles_snacks/static;
        expires 30d;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/pickles /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl enable nginx

# Setup Systemd service
sudo tee /etc/systemd/system/pickles.service > /dev/null <<'EOF'
[Unit]
Description=HomeMade Pickles & Snacks Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/pickles_snacks
EnvironmentFile=/home/ubuntu/pickles_snacks/.env
ExecStart=/home/ubuntu/pickles_snacks/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pickles
sudo systemctl start pickles

echo ""
echo "✅ Deployment Complete!"
echo "🌐 Visit: http://$(curl -s ifconfig.me)"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status pickles    # Check app status"
echo "  sudo journalctl -u pickles -f    # View live logs"
echo "  sudo systemctl restart pickles   # Restart app"
