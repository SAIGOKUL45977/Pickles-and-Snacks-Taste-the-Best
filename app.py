"""
Phase 3: Flask Application - HomeMade Pickles & Snacks
Full e-commerce workflow with DynamoDB integration
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import boto3
import os
import uuid
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from decimal import Decimal
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'pickles_secret_2025')

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'products')
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def get_product_image(product_id):
    for ext in ALLOWED_EXTENSIONS:
        path = os.path.join(IMAGE_FOLDER, f"{product_id}.{ext}")
        if os.path.exists(path):
            return True, f"images/products/{product_id}.{ext}"
    return False, ''

def with_product_images(products):
    result = []
    for product in products:
        exists, path = get_product_image(product['ProductID'])
        result.append({**product, 'image_exists': exists, 'image_path': path})
    return result

# ─────────────────────────────────────────────
# DynamoDB Helpers
# ─────────────────────────────────────────────

def get_table(name_env, default):
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'ap-south-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    return dynamodb.Table(os.getenv(name_env, default))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_globals():
    cart = session.get('cart', {})
    return {'cart_count': sum(cart.values())}

# ─────────────────────────────────────────────
# Phase 3a: Product Browsing
# ─────────────────────────────────────────────

@app.route('/')
def index():
    table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    response = table.scan()
    products = response.get('Items', [])
    featured = [p for p in products if 'bestseller' in p.get('Tags', [])]

    return render_template(
        'index.html',
        products=with_product_images(products[:6]),
        featured=with_product_images(featured)
    )

@app.route('/products')
def products():
    table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    category = request.args.get('category', '')
    search = request.args.get('search', '')

    response = table.scan()
    all_products = response.get('Items', [])

    if category:
        all_products = [p for p in all_products if p.get('Category') == category]
    if search:
        all_products = [p for p in all_products if search.lower() in p['Name'].lower()]

    categories = sorted(set(p['Category'] for p in table.scan()['Items']))
    return render_template(
    'products.html',
    products=with_product_images(all_products),
    categories=categories,
    selected_category=category,
    search=search
)

@app.route('/product/<product_id>')
def product_detail(product_id):
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')

    product = p_table.get_item(Key={'ProductID': product_id}).get('Item')
    inventory = i_table.get_item(Key={'ProductID': product_id}).get('Item', {})

    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('products'))

    # Personalized recommendations (same category)
    all_products = p_table.scan()['Items']
    recommendations = [p for p in all_products
                       if p['Category'] == product['Category'] and p['ProductID'] != product_id][:3]

    exists, path = get_product_image(product_id)

    return render_template(
    'product_detail.html',
    product=product,
    stock=inventory.get('Stock', 0),
    recommendations=with_product_images(recommendations),
    image_exists=exists,
    image_path=path
)

# ─────────────────────────────────────────────
# Phase 3b: User Auth
# ─────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        phone = request.form['phone'].strip()
        address = request.form['address'].strip()

        # Validation
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        if not all([name, email, phone, address]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        table = get_table('USERS_TABLE', 'PicklesUsers')
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('Email').eq(email)
        )
        if response.get('Items'):
            flash('Email already registered.', 'warning')
            return redirect(url_for('login'))

        user_id = str(uuid.uuid4())

        table.put_item(Item={
            'UserID': user_id,
            'Name': name,
            'Email': email,
            'Password': hash_password(password),
            'Phone': phone,
            'Address': address,
            'CreatedAt': datetime.now().isoformat(),
            'Preferences': []
        })

        session['user_id'] = user_id
        session['user_name'] = name
        flash(f'Welcome, {name}! 🎉', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        table = get_table('USERS_TABLE', 'PicklesUsers')
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('Email').eq(email)
        )
        users = response.get('Items', [])

        if users and users[0]['Password'] == hash_password(password):
            user = users[0]
            session['user_id'] = user['UserID']
            session['user_name'] = user['Name']
            flash(f'Welcome back, {user["Name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ─────────────────────────────────────────────
# Phase 3c: Cart & Orders
# ─────────────────────────────────────────────

@app.route('/cart')
@login_required
def cart():
    cart_items = session.get('cart', {})
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    products = []
    total = 0

    for pid, qty in cart_items.items():
        product = p_table.get_item(Key={'ProductID': pid}).get('Item')
        if product:
            subtotal = float(product['Price']) * qty
            total += subtotal
            products.append({**product, 'Quantity': qty, 'Subtotal': subtotal})

    return render_template('cart.html', cart_products=products, total=total)

@app.route('/cart/add/<product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')
    
    product = p_table.get_item(Key={'ProductID': product_id}).get('Item')
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('products'))
    
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    current = cart.get(product_id, 0)
    inventory = i_table.get_item(Key={'ProductID': product_id}).get('Item', {})
    stock = int(inventory.get('Stock', 0))
    
    if stock == 0:
        flash(f'Sorry! {product["Name"]} is out of stock.', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    if current + qty > stock:
        available = stock - current
        flash(f'Only {available} more unit(s) of {product["Name"]} available.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    cart[product_id] = current + qty
    session['cart'] = cart
    flash(f'✅ {product["Name"]} added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/update/<product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    
    cart = session.get('cart', {})
    action = request.form.get('action', '')
    qty = int(request.form.get('quantity', 1))
    inventory = i_table.get_item(Key={'ProductID': product_id}).get('Item', {})
    stock = int(inventory.get('Stock', 0))
    product = p_table.get_item(Key={'ProductID': product_id}).get('Item')

    if action == 'increase':
        qty = cart.get(product_id, 0) + 1
    elif action == 'decrease':
        qty = cart.get(product_id, 1) - 1

    if qty <= 0:
        cart.pop(product_id, None)
        flash(f'Removed from cart.', 'info')
    elif qty > stock:
        flash(f'Only {stock} units available.', 'warning')
        qty = stock
        cart[product_id] = qty
    else:
        cart[product_id] = qty
        if product:
            flash(f'Updated {product["Name"]} to {qty} unit(s).', 'success')

    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart/remove/<product_id>')
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(product_id, None)
    flash('Item removed from cart.', 'info')
    session['cart'] = cart
    return redirect(url_for('cart'))

# ─────────────────────────────────────────────
# Phase 4: Order Placement + Inventory Update
# ─────────────────────────────────────────────

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = session.get('cart', {})
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('products'))

    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')
    u_table = get_table('USERS_TABLE', 'PicklesUsers')

    products = []
    total = 0
    for pid, qty in cart_items.items():
        product = p_table.get_item(Key={'ProductID': pid}).get('Item')
        if product:
            subtotal = float(product['Price']) * qty
            total += subtotal
            products.append({**product, 'Quantity': qty, 'Subtotal': subtotal})

    if request.method == 'POST':
        order_id = 'ORD-' + str(uuid.uuid4())[:8].upper()
        payment_method = request.form.get('payment', 'COD')

        # Save order
        o_table.put_item(Item={
            'OrderID': order_id,
            'UserID': session['user_id'],
            'Items': [{'ProductID': pid, 'Quantity': Decimal(qty)}
                      for pid, qty in cart_items.items()],
            'Total': Decimal(str(round(total, 2))),
            'Status': 'Confirmed',
            'PaymentMethod': payment_method,
            'OrderedAt': datetime.now().isoformat(),
            'DeliveryAddress': request.form.get('address', '')
        })

        # Real-time inventory update
        for pid, qty in cart_items.items():
            i_table.update_item(
                Key={'ProductID': pid},
                UpdateExpression='SET Stock = Stock - :qty, LastUpdated = :ts',
                ExpressionAttributeValues={
                    ':qty': Decimal(qty),
                    ':ts': datetime.now().isoformat()
                }
            )

        session['cart'] = {}
        flash(f'🎉 Order {order_id} placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order_id))

    # Pre-fill from user profile
    user = u_table.get_item(Key={'UserID': session['user_id']}).get('Item', {})
    user_address = user.get('Address', '')
    user_phone = user.get('Phone', '')
    
    return render_template('checkout.html', cart_products=products, total=total,
                           user_address=user_address, user_phone=user_phone)

@app.route('/order/confirmation/<order_id>')
@login_required
def order_confirmation(order_id):
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')
    order = o_table.get_item(Key={
        'OrderID': order_id,
        'UserID': session['user_id']
    }).get('Item')
    return render_template('order_confirmation.html', order=order)

@app.route('/my-orders')
@login_required
def my_orders():
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')
    response = o_table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('UserID').eq(session['user_id'])
    )
    orders = sorted(response.get('Items', []), key=lambda x: x['OrderedAt'], reverse=True)
    return render_template('my_orders.html', orders=orders)

# ─────────────────────────────────────────────
# Phase 3e: Subscriptions
# ─────────────────────────────────────────────

@app.route('/subscriptions', methods=['GET', 'POST'])
@login_required
def subscriptions():
    plans = [
        {'id': 'weekly', 'name': 'Weekly Box', 'price': 299,
         'items': '3 Pickle Jars + 2 Snack Packs', 'frequency': 'Every Week'},
        {'id': 'monthly', 'name': 'Monthly Hamper', 'price': 999,
         'items': '8 Pickle Jars + 5 Snack Packs', 'frequency': 'Every Month'},
        {'id': 'seasonal', 'name': 'Seasonal Special', 'price': 1499,
         'items': '12 Pickle Jars + 8 Snack Packs + Bonus', 'frequency': 'Every Season'},
    ]
    
    s_table = get_table('SUBSCRIPTIONS_TABLE', 'PicklesSubscriptions')
    current_sub = s_table.get_item(Key={'UserID': session['user_id']}).get('Item')
    
    if request.method == 'POST':
        if current_sub and current_sub.get('Status') == 'Active':
            flash('You already have an active subscription! Cancel it first to change.', 'warning')
            return redirect(url_for('subscriptions'))
        
        plan_id = request.form.get('plan')
        s_table.put_item(Item={
            'UserID': session['user_id'],
            'Plan': plan_id,
            'StartDate': datetime.now().isoformat(),
            'Status': 'Active',
            'Address': request.form.get('address', '')
        })
        flash(f'🎁 {plan_id.title()} subscription activated!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('subscriptions.html', plans=plans, current_sub=current_sub)

@app.route('/subscriptions/cancel')
@login_required
def cancel_subscription():
    s_table = get_table('SUBSCRIPTIONS_TABLE', 'PicklesSubscriptions')
    s_table.update_item(
        Key={'UserID': session['user_id']},
        UpdateExpression='SET #status = :status',
        ExpressionAttributeNames={'#status': 'Status'},
        ExpressionAttributeValues={':status': 'Cancelled'}
    )
    flash('Subscription cancelled.', 'info')
    return redirect(url_for('dashboard'))

# ─────────────────────────────────────────────
# API: Real-Time Inventory (AJAX)
# ─────────────────────────────────────────────

@app.route('/api/inventory/<product_id>')
def get_inventory(product_id):
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')
    item = i_table.get_item(Key={'ProductID': product_id}).get('Item', {})
    stock = int(item.get('Stock', 0))
    return jsonify({'product_id': product_id, 'stock': stock,
                    'status': 'In Stock' if stock > 0 else 'Out of Stock'})

# ─────────────────────────────────────────────
# Dashboard (Admin view)
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')
    s_table = get_table('SUBSCRIPTIONS_TABLE', 'PicklesSubscriptions')

    user_orders = o_table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('UserID').eq(session['user_id'])
    )['Items']
    
    current_sub = s_table.get_item(Key={'UserID': session['user_id']}).get('Item')
    total_spent = sum(float(o.get('Total', 0)) for o in user_orders)

    return render_template('dashboard.html',
                           orders=user_orders,
                           total_spent=total_spent,
                           order_count=len(user_orders),
                           current_sub=current_sub)

# ─────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ═══════════════════════════════════════════════
# ADMIN / OWNER PANEL
# ═══════════════════════════════════════════════

ADMIN_EMAIL = 'owner@pickles.com'
ADMIN_PASSWORD = 'owner123'

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        if (request.form['email'].strip().lower() == ADMIN_EMAIL
                and request.form['password'] == ADMIN_PASSWORD):
            session['is_admin'] = True
            session['admin_name'] = 'Owner'
            flash('Welcome back, Owner! 👑', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_name', None)
    flash('Logged out from admin panel.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')
    u_table = get_table('USERS_TABLE', 'PicklesUsers')
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')

    all_products = p_table.scan()['Items']
    all_orders = sorted(o_table.scan()['Items'], key=lambda x: x.get('OrderedAt', ''), reverse=True)[:5]
    all_users = u_table.scan()['Items']
    inventory = i_table.scan()['Items']
    low_stock = [(i['ProductID'], int(i.get('Stock', 0))) for i in inventory if int(i.get('Stock', 0)) < 20]
    
    # Add customer names to recent orders
    uid_to_name = {u['UserID']: u['Name'] for u in all_users}
    for o in all_orders:
        o['CustomerName'] = uid_to_name.get(o['UserID'], 'Unknown')

    total_revenue = sum(float(o.get('Total', 0)) for o in o_table.scan()['Items'])

    return render_template('admin/dashboard.html',
                           total_products=len(all_products),
                           total_orders=len(o_table.scan()['Items']),
                           total_users=len(all_users),
                           total_revenue=total_revenue,
                           low_stock=low_stock,
                           recent_orders=all_orders)

@app.route('/admin/products')
@admin_required
def admin_products():
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')

    all_products = p_table.scan()['Items']
    inventory = {item['ProductID']: int(item.get('Stock', 0)) for item in i_table.scan()['Items']}
    all_orders = o_table.scan()['Items']

    products_with_stock = []
    for p in all_products:
        has_orders = any(
            any(item['ProductID'] == p['ProductID'] for item in o.get('Items', []))
            for o in all_orders
        )
        products_with_stock.append({
            **p,
            'Stock': inventory.get(p['ProductID'], 0),
            'has_orders': 'true' if has_orders else 'false'
        })

    return render_template('admin/products.html', products=products_with_stock)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form['name'].strip()
        category = request.form['category']
        price = request.form['price'].strip()
        description = request.form['description'].strip()
        tags = [t.strip().lower() for t in request.form['tags'].split(',') if t.strip()]
        rating = request.form.get('rating', '4.0').strip()
        stock = int(request.form.get('stock', 50))

        p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
        all_products = p_table.scan()['Items']
        existing_ids = [int(p['ProductID'][1:]) for p in all_products if p['ProductID'][1:].isdigit()]
        pid = f"P{(max(existing_ids)+1 if existing_ids else 1):03d}"

        p_table.put_item(Item={
            'ProductID': pid,
            'Name': name,
            'Category': category,
            'Price': price,
            'Description': description,
            'Tags': tags,
            'Rating': rating
        })

        i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')
        i_table.put_item(Item={
            'ProductID': pid,
            'Stock': Decimal(stock),
            'LastUpdated': datetime.now().isoformat()
        })

        flash(f'✅ "{name}" added! (ID: {pid})', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/add_product.html')

@app.route('/admin/products/edit/<product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')

    product = p_table.get_item(Key={'ProductID': product_id}).get('Item')
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin_products'))

    inventory = i_table.get_item(Key={'ProductID': product_id}).get('Item', {})
    stock = int(inventory.get('Stock', 0))

    if request.method == 'POST':
        product['Name'] = request.form['name'].strip()
        product['Category'] = request.form['category']
        product['Price'] = request.form['price'].strip()
        product['Description'] = request.form['description'].strip()
        product['Tags'] = [t.strip().lower() for t in request.form['tags'].split(',') if t.strip()]
        product['Rating'] = request.form.get('rating', product.get('Rating', '4.0')).strip()

        p_table.put_item(Item=product)
        i_table.put_item(Item={
            'ProductID': product_id,
            'Stock': Decimal(int(request.form.get('stock', stock))),
            'LastUpdated': datetime.now().isoformat()
        })

        flash(f'✅ "{product["Name"]}" updated!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/edit_product.html', product=product, stock=stock)

@app.route('/admin/products/delete/<product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')

    product = p_table.get_item(Key={'ProductID': product_id}).get('Item')
    if product:
        p_table.delete_item(Key={'ProductID': product_id})
        i_table.delete_item(Key={'ProductID': product_id})
        flash(f'🗑️ "{product["Name"]}" deleted.', 'info')
    return redirect(url_for('admin_products'))

@app.route('/admin/inventory', methods=['GET', 'POST'])
@admin_required
def admin_inventory():
    i_table = get_table('INVENTORY_TABLE', 'PicklesInventory')
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')

    updated_product = None
    if request.method == 'POST':
        pid = request.form['product_id']
        new_stock = int(request.form['stock'])
        i_table.put_item(Item={
            'ProductID': pid,
            'Stock': Decimal(new_stock),
            'LastUpdated': datetime.now().isoformat()
        })
        product = p_table.get_item(Key={'ProductID': pid}).get('Item')
        updated_product = product['Name'] if product else pid

    all_products = p_table.scan()['Items']
    inventory = {item['ProductID']: int(item.get('Stock', 0)) for item in i_table.scan()['Items']}

    inventory_data = [
        {**p, 'Stock': inventory.get(p['ProductID'], 0)}
        for p in all_products
    ]

    return render_template('admin/inventory.html',
                           inventory=inventory_data,
                           updated_product=updated_product)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')
    u_table = get_table('USERS_TABLE', 'PicklesUsers')

    uid_to_name = {u['UserID']: u['Name'] for u in u_table.scan()['Items']}
    all_orders = sorted(o_table.scan()['Items'], key=lambda x: x.get('OrderedAt', ''), reverse=True)

    for o in all_orders:
        o['CustomerName'] = uid_to_name.get(o['UserID'], 'Unknown')

    return render_template('admin/orders.html', orders=all_orders)

@app.route('/admin/orders/status/<order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')
    new_status = request.form['status']

    # Need to find the order first to get UserID (composite key)
    orders = o_table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('OrderID').eq(order_id)
    )['Items']

    if orders:
        order = orders[0]
        o_table.update_item(
            Key={'OrderID': order_id, 'UserID': order['UserID']},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={':status': new_status}
        )
        flash(f'Order {order_id} → "{new_status}".', 'success')

    return redirect(url_for('admin_orders'))

@app.route('/admin/users')
@admin_required
def admin_users():
    u_table = get_table('USERS_TABLE', 'PicklesUsers')
    o_table = get_table('ORDERS_TABLE', 'PicklesOrders')
    s_table = get_table('SUBSCRIPTIONS_TABLE', 'PicklesSubscriptions')

    all_users = u_table.scan()['Items']
    all_orders = o_table.scan()['Items']
    all_subs = s_table.scan()['Items']

    for u in all_users:
        u['OrderCount'] = len([o for o in all_orders if o['UserID'] == u['UserID']])
        u['HasSub'] = any(s['UserID'] == u['UserID'] and s.get('Status') == 'Active' for s in all_subs)

    return render_template('admin/users.html', users=all_users)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/images')
@admin_required
def admin_images():
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    products = p_table.scan()['Items']

    products_with_images = []
    for p in products:
        exists, path = get_product_image(p['ProductID'])
        products_with_images.append({
            **p,
            'image_exists': exists,
            'image_path': path
        })

    return render_template('admin/images.html', products=products_with_images)

@app.route('/admin/images/upload/<product_id>', methods=['POST'])
@admin_required
def admin_upload_image(product_id):
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    product = p_table.get_item(Key={'ProductID': product_id}).get('Item')

    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin_images'))

    if 'image' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('admin_images'))

    file = request.files['image']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('admin_images'))

    if not allowed_file(file.filename):
        flash('Invalid file type. Use JPG, PNG, or WebP.', 'danger')
        return redirect(url_for('admin_images'))

    # Remove existing image
    for ext in ALLOWED_EXTENSIONS:
        old_path = os.path.join(IMAGE_FOLDER, f"{product_id}.{ext}")
        if os.path.exists(old_path):
            os.remove(old_path)

    # Save new image
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{product_id}.{ext}"
    file.save(os.path.join(IMAGE_FOLDER, filename))
    flash(f'✅ Image uploaded for "{product["Name"]}"!', 'success')
    return redirect(url_for('admin_images'))

@app.route('/admin/images/delete/<product_id>', methods=['POST'])
@admin_required
def admin_delete_image(product_id):
    p_table = get_table('PRODUCTS_TABLE', 'PicklesProducts')
    product = p_table.get_item(Key={'ProductID': product_id}).get('Item')

    for ext in ALLOWED_EXTENSIONS:
        path = os.path.join(IMAGE_FOLDER, f"{product_id}.{ext}")
        if os.path.exists(path):
            os.remove(path)
            flash(f'🗑️ Image removed for "{product["Name"] if product else product_id}".', 'info')
            return redirect(url_for('admin_images'))

    flash('No image found to delete.', 'warning')
    return redirect(url_for('admin_images'))

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'True') == 'True', host='0.0.0.0', port=5000)
