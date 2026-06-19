"""
Phase 5: EC2 Deployment Script
Phase 7: CloudWatch Monitoring
HomeMade Pickles & Snacks
"""

# ══════════════════════════════════════════════
# NGINX CONFIG  (save as: /etc/nginx/sites-available/pickles)
# ══════════════════════════════════════════════
NGINX_CONFIG = """
server {
    listen 80;
    server_name YOUR_EC2_PUBLIC_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /home/ubuntu/pickles_snacks/static;
        expires 30d;
    }
}
"""

# ══════════════════════════════════════════════
# SYSTEMD SERVICE  (save as: /etc/systemd/system/pickles.service)
# ══════════════════════════════════════════════
SYSTEMD_SERVICE = """
[Unit]
Description=HomeMade Pickles & Snacks - Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/pickles_snacks
Environment="PATH=/home/ubuntu/pickles_snacks/venv/bin"
ExecStart=/home/ubuntu/pickles_snacks/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
"""

# ══════════════════════════════════════════════
# Phase 7: CloudWatch Monitoring
# ══════════════════════════════════════════════

import boto3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_cloudwatch():
    return boto3.client(
        'cloudwatch',
        region_name=os.getenv('AWS_REGION', 'ap-south-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

def push_metric(metric_name, value, unit='Count'):
    """Push a custom metric to CloudWatch."""
    cw = get_cloudwatch()
    cw.put_metric_data(
        Namespace='PicklesSnacks/App',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.now()
        }]
    )
    print(f"[CloudWatch] {metric_name} = {value}")

def create_alarms():
    """Create CloudWatch alarms for monitoring."""
    cw = get_cloudwatch()

    # Low stock alarm
    cw.put_metric_alarm(
        AlarmName='LowInventoryAlert',
        MetricName='LowStockCount',
        Namespace='PicklesSnacks/App',
        Statistic='Average',
        Period=300,
        EvaluationPeriods=1,
        Threshold=5,
        ComparisonOperator='GreaterThanThreshold',
        AlarmDescription='Alert when more than 5 products are low on stock',
        TreatMissingData='notBreaching'
    )
    print("[OK] CloudWatch alarm created: LowInventoryAlert")

    # High order volume alarm
    cw.put_metric_alarm(
        AlarmName='HighOrderVolume',
        MetricName='OrdersPlaced',
        Namespace='PicklesSnacks/App',
        Statistic='Sum',
        Period=3600,
        EvaluationPeriods=1,
        Threshold=100,
        ComparisonOperator='GreaterThanThreshold',
        AlarmDescription='Alert on high order volume (>100/hour) - festival/promo spike',
        TreatMissingData='notBreaching'
    )
    print("[OK] CloudWatch alarm created: HighOrderVolume")

def monitor_inventory():
    """Scan inventory and push low-stock metrics to CloudWatch."""
    import boto3 as b3
    dynamodb = b3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    table = dynamodb.Table(os.getenv('INVENTORY_TABLE', 'PicklesInventory'))
    items = table.scan()['Items']
    low_stock = [i for i in items if int(i.get('Stock', 0)) < 20]
    push_metric('LowStockCount', len(low_stock))
    push_metric('TotalProducts', len(items))
    print(f"[Monitor] {len(low_stock)} low-stock products detected.")

if __name__ == "__main__":
    print("=== Setting up CloudWatch Monitoring ===")
    create_alarms()
    monitor_inventory()
