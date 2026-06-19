# 🥒 HomeMade Pickles & Snacks — AWS Cloud Platform

A complete cloud-enabled e-commerce platform for homemade pickles and snacks,
built with Flask + DynamoDB + EC2 + CloudWatch.

---

## 📁 Project Structure

```
pickles_snacks/
├── app.py                    # Phase 3: Flask application (all routes)
├── requirements.txt          # Python dependencies
├── gunicorn_config.py        # Phase 5: Production server config
├── deploy_ec2.sh             # Phase 5: EC2 deployment script
├── tests.py                  # Phase 6: End-to-end tests
├── .env                      # Environment variables (fill your keys)
├── config/
│   └── aws_setup.py          # Phase 1 & 2: AWS + DynamoDB setup
├── deployment_monitoring.py  # Phase 5 & 7: Nginx config + CloudWatch
└── templates/
    ├── base.html
    ├── index.html
    ├── products.html
    ├── product_detail.html
    ├── register.html
    ├── login.html
    ├── cart.html
    ├── checkout.html
    ├── order_confirmation.html
    ├── my_orders.html
    ├── subscriptions.html
    └── dashboard.html
```

---

## ⚙️ Phase 1: Environment Setup

### Step 1 — Install dependencies locally
```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Configure .env
Fill in your AWS credentials in `.env`:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
FLASK_SECRET_KEY=any_random_string
```

---

## 🗄️ Phase 2: DynamoDB Setup

Run the setup script to create tables and seed products:
```bash
python config/aws_setup.py
```
This creates 5 tables:
- `PicklesProducts` — Product catalog
- `PicklesUsers` — User profiles
- `PicklesOrders` — Orders (OrderID + UserID)
- `PicklesInventory` — Real-time stock levels
- `PicklesSubscriptions` — Subscription plans

---

## 🌶️ Phase 3: Run Flask App

```bash
python app.py
```
Visit: http://localhost:5000

### Features:
| Route | Feature |
|-------|---------|
| `/` | Homepage with bestsellers |
| `/products` | Browse + Category filter + Search |
| `/product/<id>` | Detail + Real-time stock + Recommendations |
| `/register` | User registration |
| `/login` | User login |
| `/cart` | Cart management |
| `/checkout` | Order placement + Payment simulation |
| `/my-orders` | Order history |
| `/subscriptions` | Weekly/Monthly/Seasonal plans |
| `/dashboard` | User stats + Low stock alerts |
| `/api/inventory/<id>` | Real-time inventory JSON API |

---

## 📦 Phase 4: Real-Time Inventory

When an order is placed, `app.py` automatically:
1. Saves order to `PicklesOrders` DynamoDB table
2. Deducts quantity from `PicklesInventory` for each product
3. Dashboard shows low-stock alerts (< 20 units)

---

## ☁️ Phase 5: Deploy on EC2

### On your EC2 instance (Ubuntu):
```bash
# Upload your project files, then run:
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```
This installs Nginx + Gunicorn + Systemd service.

---

## 🧪 Phase 6: Testing

```bash
# Run Flask first, then:
python tests.py
```

---

## 📊 Phase 7: CloudWatch Monitoring

```bash
python deployment_monitoring.py
```
- Pushes inventory metrics to CloudWatch
- Creates alarms for low stock and high order volume

---

## 🔐 AWS Services Used

| Service | Purpose |
|---------|---------|
| EC2 | Host Flask application |
| DynamoDB | NoSQL database for all data |
| CloudWatch | Monitoring, metrics, alarms |
| boto3 | Python SDK for AWS |
| IAM | Access control |

---

## 🌿 Built with

- **Flask** — Python web framework
- **boto3** — AWS SDK
- **DynamoDB** — Serverless NoSQL
- **Gunicorn** — WSGI server
- **Nginx** — Reverse proxy
- **CloudWatch** — Monitoring
