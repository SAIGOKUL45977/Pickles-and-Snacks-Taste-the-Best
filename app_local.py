"""
HomeMade Pickles & Snacks — LOCAL TEST VERSION
✅ All 17 UX issues fixed
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import uuid, hashlib
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'products')
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_product_image(product_id):
    """Returns (image_exists, ext, url_path) for a product."""
    for ext in ALLOWED_EXTENSIONS:
        path = os.path.join(IMAGE_FOLDER, f"{product_id}.{ext}")
        if os.path.exists(path):
            return True, f".{ext}", f"images/products/{product_id}.{ext}"
    return False, '', ''

app = Flask(__name__)
app.secret_key = 'pickles_local_test_2025'

# ─────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────

MOCK_PRODUCTS = [
    {"ProductID": "P001", "Name": "Mango Pickle",   "Category": "Pickles", "Price": "120",
     "Description": "Traditional sun-dried mango pickle with mustard oil.",
     "Tags": ["spicy", "traditional", "bestseller"], "Rating": "4.8"},
    {"ProductID": "P002", "Name": "Lemon Pickle",   "Category": "Pickles", "Price": "90",
     "Description": "Tangy lemon pickle with aromatic spices.",
     "Tags": ["tangy", "light"], "Rating": "4.5"},
    {"ProductID": "P003", "Name": "Garlic Pickle",  "Category": "Pickles", "Price": "150",
     "Description": "Bold garlic pickle, perfect with dal-rice and also very tasty.",
     "Tags": ["bold", "garlic", "spicy"], "Rating": "4.7"},
    {"ProductID": "P004", "Name": "Murukku",        "Category": "Snacks",  "Price": "60",
     "Description": "Crispy rice flour murukku, handmade with sesame seeds.",
     "Tags": ["crunchy", "traditional"], "Rating": "4.6"},
    {"ProductID": "P005", "Name": "Mixture",        "Category": "Snacks",  "Price": "80",
     "Description": "South Indian spicy mixture with fried lentils.",
     "Tags": ["spicy", "crunchy", "bestseller"], "Rating": "4.9"},
    {"ProductID": "P006", "Name": "Avakaya Pickle", "Category": "Pickles", "Price": "180",
     "Description": "Authentic Andhra-style raw mango pickle.",
     "Tags": ["andhra", "spicy", "traditional"], "Rating": "5.0"},
    {"ProductID": "P007", "Name": "Gongura Pickle", "Category": "Pickles", "Price": "130",
     "Description": "Famous Andhra sorrel leaves pickle, tangy and spicy.",
     "Tags": ["andhra", "tangy", "bestseller"], "Rating": "4.9"},
    {"ProductID": "P008", "Name": "Chakli",         "Category": "Snacks",  "Price": "70",
     "Description": "Crispy spiral snack made from rice and lentil flour.",
     "Tags": ["crunchy", "traditional"], "Rating": "4.5"},
]

MOCK_INVENTORY     = {p["ProductID"]: 100 for p in MOCK_PRODUCTS}
MOCK_USERS         = {}   # { email: user_dict }
MOCK_ORDERS        = []
MOCK_SUBSCRIPTIONS = {}   # { user_id: sub_dict }

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def get_product(pid):
    return next((p for p in MOCK_PRODUCTS if p['ProductID'] == pid), None)

def get_user_by_id(uid):
    return next((u for u in MOCK_USERS.values() if u['UserID'] == uid), None)

def product_has_orders(pid):
    return any(
        any(i['ProductID'] == pid for i in o.get('Items', []))
        for o in MOCK_ORDERS
    )

def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return dec

def admin_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*a, **kw)
    return dec

# Fix #1: Cart count available in ALL templates
@app.context_processor
def inject_globals():
    cart = session.get('cart', {})
    return {'cart_count': sum(cart.values())}

# ─────────────────────────────────────────────
# CUSTOMER ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    featured = [p for p in MOCK_PRODUCTS if 'bestseller' in p.get('Tags', [])]
    def with_image(products):
        result = []
        for p in products:
            exists, ext, path = get_product_image(p['ProductID'])
            result.append({**p, 'image_exists': exists, 'image_path': path})
        return result
    return render_template('index.html', products=with_image(MOCK_PRODUCTS[:6]),
                           featured=with_image(featured))

@app.route('/products')
def products():
    category = request.args.get('category', '')
    search   = request.args.get('search', '').lower()
    filtered = MOCK_PRODUCTS[:]
    if category:
        filtered = [p for p in filtered if p['Category'] == category]
    if search:
        filtered = [p for p in filtered if search in p['Name'].lower()]
    categories = sorted(set(p['Category'] for p in MOCK_PRODUCTS))
    products_with_images = []
    for p in filtered:
        exists, ext, path = get_product_image(p['ProductID'])
        products_with_images.append({**p, 'image_exists': exists, 'image_path': path})
    return render_template('products.html', products=products_with_images,
                           categories=categories, selected_category=category, search=search)

@app.route('/product/<product_id>')
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('products'))
    stock = MOCK_INVENTORY.get(product_id, 0)
    recommendations = [p for p in MOCK_PRODUCTS
                       if p['Category'] == product['Category']
                       and p['ProductID'] != product_id][:3]
    exists, ext, path = get_product_image(product_id)
    recos_with_images = []
    for r in recommendations:
        re, rx, rp = get_product_image(r['ProductID'])
        recos_with_images.append({**r, 'image_exists': re, 'image_path': rp})
    return render_template('product_detail.html', product=product,
                           stock=stock, recommendations=recos_with_images,
                           image_exists=exists, image_path=path)

# ── Auth ──────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        phone    = request.form['phone'].strip()
        address  = request.form['address'].strip()
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        if not all([name, email, phone, address]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if email in MOCK_USERS:
            flash('Email already registered.', 'warning')
            return redirect(url_for('login'))
        uid = str(uuid.uuid4())
        MOCK_USERS[email] = {
            'UserID': uid, 'Name': name, 'Email': email,
            'Password': hash_password(password), 'Phone': phone,
            'Address': address, 'CreatedAt': datetime.now().isoformat()
        }
        session.update({'user_id': uid, 'user_name': name, 'user_email': email})
        flash(f'Welcome, {name}! 🎉', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        user     = MOCK_USERS.get(email)
        if user and user['Password'] == hash_password(password):
            session.update({'user_id': user['UserID'], 'user_name': user['Name'], 'user_email': email})
            flash(f'Welcome back, {user["Name"]}! 👋', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# ── Cart ──────────────────────────────────────

@app.route('/cart')
@login_required
def cart():
    items, total = [], 0
    for pid, qty in session.get('cart', {}).items():
        p = get_product(pid)
        if p:
            sub = float(p['Price']) * qty
            total += sub
            items.append({**p, 'Quantity': qty, 'Subtotal': sub})
    return render_template('cart.html', cart_products=items, total=total)

@app.route('/cart/add/<product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = get_product(product_id)
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('products'))
    qty     = int(request.form.get('quantity', 1))
    cart    = session.get('cart', {})
    current = cart.get(product_id, 0)
    stock   = MOCK_INVENTORY.get(product_id, 0)
    if stock == 0:
        flash(f'Sorry! {product["Name"]} is out of stock.', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    if current + qty > stock:
        available = stock - current
        flash(f'Only {available} more unit(s) of {product["Name"]} available.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    cart[product_id] = current + qty
    session['cart']  = cart
    flash(f'✅ {product["Name"]} added to cart!', 'success')
    next_page = request.form.get('next') or request.referrer
    if next_page and next_page.startswith(request.host_url):
        return redirect(next_page)
    return redirect(url_for('products'))

# Fix #5: Update cart quantity
@app.route('/cart/update/<product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    cart    = session.get('cart', {})
    action  = request.form.get('action', '')
    qty     = int(request.form.get('quantity', 1))
    stock   = MOCK_INVENTORY.get(product_id, 0)
    product = get_product(product_id)

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
    session['cart'] = cart
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

# ── Checkout & Orders ─────────────────────────

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = session.get('cart', {})
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('products'))

    items, total = [], 0
    for pid, qty in cart_items.items():
        p = get_product(pid)
        if p:
            sub = float(p['Price']) * qty
            total += sub
            items.append({**p, 'Quantity': qty, 'Subtotal': sub})

    if request.method == 'POST':
        oid = 'ORD-' + str(uuid.uuid4())[:8].upper()
        MOCK_ORDERS.append({
            'OrderID':         oid,
            'UserID':          session['user_id'],
            'Items':           [{'ProductID': pid, 'Quantity': qty,
                                 'Name': get_product(pid)['Name']}
                                for pid, qty in cart_items.items()],
            'Total':           round(total, 2),
            'Status':          'Confirmed',
            'PaymentMethod':   request.form.get('payment', 'COD'),
            'OrderedAt':       datetime.now().isoformat(),
            'DeliveryAddress': request.form.get('address', ''),
            'Phone':           request.form.get('phone', '')
        })
        for pid, qty in cart_items.items():
            MOCK_INVENTORY[pid] = max(0, MOCK_INVENTORY.get(pid, 0) - qty)
        session['cart'] = {}
        flash(f'🎉 Order {oid} placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=oid))

    # Fix #3: Pre-fill address and phone from user profile
    user = get_user_by_id(session['user_id'])
    user_address = user.get('Address', '') if user else ''
    user_phone   = user.get('Phone', '')   if user else ''
    return render_template('checkout.html', cart_products=items, total=total,
                           user_address=user_address, user_phone=user_phone)

@app.route('/order/confirmation/<order_id>')
@login_required
def order_confirmation(order_id):
    order = next((o for o in MOCK_ORDERS if o['OrderID'] == order_id), None)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('my_orders'))
    return render_template('order_confirmation.html', order=order)

@app.route('/my-orders')
@login_required
def my_orders():
    orders = sorted(
        [o for o in MOCK_ORDERS if o['UserID'] == session['user_id']],
        key=lambda x: x['OrderedAt'], reverse=True
    )
    return render_template('my_orders.html', orders=orders)

# ── Subscriptions ─────────────────────────────

@app.route('/subscriptions', methods=['GET', 'POST'])
def subscriptions():
    plans = [
        {'id': 'weekly',   'name': 'Weekly Box',       'price': 299,
         'items': '3 Pickle Jars + 2 Snack Packs',     'frequency': 'Every Week'},
        {'id': 'monthly',  'name': 'Monthly Hamper',   'price': 999,
         'items': '8 Pickle Jars + 5 Snack Packs',     'frequency': 'Every Month'},
        {'id': 'seasonal', 'name': 'Seasonal Special', 'price': 1499,
         'items': '12 Pickle Jars + 8 Snack Packs + Bonus', 'frequency': 'Every Season'},
    ]
    current_sub = MOCK_SUBSCRIPTIONS.get(session.get('user_id'))
    if request.method == 'POST':
        if not session.get('user_id'):
            flash('Please login to subscribe.', 'warning')
            return redirect(url_for('login'))
        if current_sub:
            flash('You already have an active subscription! Cancel it first to change.', 'warning')
            return redirect(url_for('subscriptions'))
        plan_id = request.form.get('plan')
        MOCK_SUBSCRIPTIONS[session['user_id']] = {
            'Plan': plan_id, 'StartDate': datetime.now().isoformat(),
            'Status': 'Active', 'Address': request.form.get('address', '')
        }
        flash(f'🎁 {plan_id.title()} subscription activated!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('subscriptions.html', plans=plans, current_sub=current_sub)

@app.route('/subscriptions/cancel')
@login_required
def cancel_subscription():
    MOCK_SUBSCRIPTIONS.pop(session['user_id'], None)
    flash('Subscription cancelled.', 'info')
    return redirect(url_for('subscriptions'))

# ── Customer Dashboard ────────────────────────
# Fix #7: Removed low_stock (admin concern)
# Fix #8: Real membership status

@app.route('/dashboard')
@login_required
def dashboard():
    user_orders = [o for o in MOCK_ORDERS if o['UserID'] == session['user_id']]
    total_spent = sum(o['Total'] for o in user_orders)
    current_sub = MOCK_SUBSCRIPTIONS.get(session['user_id'])
    return render_template('dashboard.html',
                           orders=user_orders,
                           total_spent=total_spent,
                           order_count=len(user_orders),
                           current_sub=current_sub)

# ── Inventory API ─────────────────────────────

@app.route('/api/inventory/<product_id>')
def get_inventory(product_id):
    stock = MOCK_INVENTORY.get(product_id, 0)
    return jsonify({'product_id': product_id, 'stock': stock,
                    'status': 'In Stock' if stock > 0 else 'Out of Stock'})

# ── Error pages ───────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ═══════════════════════════════════════════════
# ADMIN / OWNER PANEL
# ═══════════════════════════════════════════════

ADMIN_EMAIL    = 'owner@pickles.com'
ADMIN_PASSWORD = 'owner123'

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        if (request.form['email'].strip().lower() == ADMIN_EMAIL
                and request.form['password'] == ADMIN_PASSWORD):
            session['is_admin']   = True
            session['admin_name'] = 'Owner'
            flash('Welcome back, Owner! 👑', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_name', None)
    return redirect(url_for('admin_login'))

# Fix #11: low_stock includes product NAME as 3rd element in tuple
# Fix #15: sidebar active state fixed via request.endpoint
@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    low_stock = [
        (pid, stock, get_product(pid)['Name'] if get_product(pid) else pid)
        for pid, stock in MOCK_INVENTORY.items() if stock < 20
    ]
    recent_orders = sorted(MOCK_ORDERS, key=lambda x: x['OrderedAt'], reverse=True)[:5]
    uid_to_name   = {u['UserID']: u['Name'] for u in MOCK_USERS.values()}
    for o in recent_orders:
        o['CustomerName'] = uid_to_name.get(o['UserID'], 'Unknown')
    return render_template('admin/dashboard.html',
                           total_products=len(MOCK_PRODUCTS),
                           total_orders=len(MOCK_ORDERS),
                           total_users=len(MOCK_USERS),
                           total_revenue=sum(o['Total'] for o in MOCK_ORDERS),
                           low_stock=low_stock,
                           recent_orders=recent_orders)

# Fix #12: Search/filter done client-side in template
# Fix #13: has_orders flag passed to template for delete warning
@app.route('/admin/products')
@admin_required
def admin_products():
    products_with_stock = [
        {**p,
         'Stock':      MOCK_INVENTORY.get(p['ProductID'], 0),
         'has_orders': 'true' if product_has_orders(p['ProductID']) else 'false'}
        for p in MOCK_PRODUCTS
    ]
    return render_template('admin/products.html', products=products_with_stock)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name        = request.form['name'].strip()
        category    = request.form['category']
        price       = request.form['price'].strip()
        description = request.form['description'].strip()
        tags        = [t.strip().lower() for t in request.form['tags'].split(',') if t.strip()]
        rating      = request.form.get('rating', '4.0').strip()
        stock       = int(request.form.get('stock', 50))
        existing_ids = [int(p['ProductID'][1:]) for p in MOCK_PRODUCTS if p['ProductID'][1:].isdigit()]
        pid = f"P{(max(existing_ids)+1 if existing_ids else 1):03d}"
        MOCK_PRODUCTS.append({'ProductID': pid, 'Name': name, 'Category': category,
                              'Price': price, 'Description': description,
                              'Tags': tags, 'Rating': rating})
        MOCK_INVENTORY[pid] = stock
        flash(f'✅ "{name}" added! (ID: {pid})', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/add_product.html')

# Fix #15: Pass 'active_section' so sidebar highlights correctly
@app.route('/admin/products/edit/<product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = get_product(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin_products'))
    if request.method == 'POST':
        product['Name']        = request.form['name'].strip()
        product['Category']    = request.form['category']
        product['Price']       = request.form['price'].strip()
        product['Description'] = request.form['description'].strip()
        product['Tags']        = [t.strip().lower() for t in request.form['tags'].split(',') if t.strip()]
        product['Rating']      = request.form.get('rating', product['Rating']).strip()
        MOCK_INVENTORY[product_id] = int(request.form.get('stock', MOCK_INVENTORY.get(product_id, 0)))
        flash(f'✅ "{product["Name"]}" updated!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/edit_product.html', product=product,
                           stock=MOCK_INVENTORY.get(product_id, 0),
                           active_section='products')

@app.route('/admin/products/delete/<product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = get_product(product_id)
    if product:
        MOCK_PRODUCTS.remove(product)
        MOCK_INVENTORY.pop(product_id, None)
        flash(f'🗑️ "{product["Name"]}" deleted.', 'info')
    return redirect(url_for('admin_products'))

# Fix #17: Pass updated_product name for success message
@app.route('/admin/inventory', methods=['GET', 'POST'])
@admin_required
def admin_inventory():
    updated_product = None
    if request.method == 'POST':
        pid       = request.form['product_id']
        new_stock = int(request.form['stock'])
        if pid in MOCK_INVENTORY:
            MOCK_INVENTORY[pid] = new_stock
            p = get_product(pid)
            updated_product = p['Name'] if p else pid

    inventory_data = [
        {**p, 'Stock': MOCK_INVENTORY.get(p['ProductID'], 0)}
        for p in MOCK_PRODUCTS
    ]
    return render_template('admin/inventory.html',
                           inventory=inventory_data,
                           updated_product=updated_product)

# Fix #14: Filter by status + Fix #16: Delivery address expandable
@app.route('/admin/orders')
@admin_required
def admin_orders():
    uid_to_name = {u['UserID']: u['Name'] for u in MOCK_USERS.values()}
    all_orders  = sorted(MOCK_ORDERS, key=lambda x: x['OrderedAt'], reverse=True)
    for o in all_orders:
        o['CustomerName'] = uid_to_name.get(o['UserID'], 'Unknown')
    return render_template('admin/orders.html', orders=all_orders)

@app.route('/admin/orders/status/<order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    new_status = request.form['status']
    for o in MOCK_ORDERS:
        if o['OrderID'] == order_id:
            o['Status'] = new_status
            flash(f'Order {order_id} → "{new_status}".', 'success')
            break
    return redirect(url_for('admin_orders'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = list(MOCK_USERS.values())
    for u in users:
        u['OrderCount'] = len([o for o in MOCK_ORDERS if o['UserID'] == u['UserID']])
        u['HasSub']     = u['UserID'] in MOCK_SUBSCRIPTIONS
    return render_template('admin/users.html', users=users)


# ── Image Management ──────────────────────────

@app.route('/admin/images')
@admin_required
def admin_images():
    products_with_images = []
    for p in MOCK_PRODUCTS:
        exists, ext, path = get_product_image(p['ProductID'])
        products_with_images.append({
            **p,
            'image_exists': exists,
            'image_ext':    ext,
            'image_path':   path
        })
    return render_template('admin/images.html', products=products_with_images)

@app.route('/admin/images/upload/<product_id>', methods=['POST'])
@admin_required
def admin_upload_image(product_id):
    product = get_product(product_id)
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

    # Remove any existing image for this product first
    for ext in ALLOWED_EXTENSIONS:
        old_path = os.path.join(IMAGE_FOLDER, f"{product_id}.{ext}")
        if os.path.exists(old_path):
            os.remove(old_path)

    # Save with product ID as filename
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{product_id}.{ext}"
    file.save(os.path.join(IMAGE_FOLDER, filename))
    flash(f'✅ Image uploaded for "{product["Name"]}"!', 'success')
    return redirect(url_for('admin_images'))

@app.route('/admin/images/delete/<product_id>', methods=['POST'])
@admin_required
def admin_delete_image(product_id):
    product = get_product(product_id)
    for ext in ALLOWED_EXTENSIONS:
        path = os.path.join(IMAGE_FOLDER, f"{product_id}.{ext}")
        if os.path.exists(path):
            os.remove(path)
            flash(f'🗑️ Image removed for "{product["Name"] if product else product_id}".', 'info')
            return redirect(url_for('admin_images'))
    flash('No image found to delete.', 'warning')
    return redirect(url_for('admin_images'))

# ─────────────────────────────────────────────
if __name__ == '__main__':
    print("\n🥒 HomeMade Pickles & Snacks — LOCAL TEST MODE")
    print("=" * 55)
    print("✅ No AWS required — using mock in-memory data")
    print("⚠️  Data resets when you restart the server")
    print("🌐 Store:        http://localhost:5000")
    print("👑 Admin Panel:  http://localhost:5000/admin/login")
    print("   Email:    owner@pickles.com")
    print("   Password: owner123")
    print("=" * 55 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
