from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import uuid
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'popy_crunch_secret_key_2026'

# Configure database
DATABASE = 'instance/popy.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            delivery_method TEXT NOT NULL,
            order_notes TEXT,
            subtotal REAL NOT NULL,
            delivery_fee REAL NOT NULL,
            total REAL NOT NULL,
            order_date TEXT NOT NULL,
            items TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Products data
PRODUCTS = [
    {
        'id': 1,
        'name': 'Popy Crunch – Cheese Flavour',
        'flavour': 'Cheese',
        'price': 12.50,
        'description': 'Crispy mini popia coated with a rich and savoury cheese flavour.',
        'image': 'cheese-flavour.jpg'
    },
    {
        'id': 2,
        'name': 'Popy Crunch – Salted Egg Flavour',
        'flavour': 'Salted Egg',
        'price': 12.50,
        'description': 'Crispy mini popia with a savoury salted egg flavour for a satisfying snack.',
        'image': 'salted-egg-flavour.jpg'
    }
]

@app.context_processor
def utility_processor():
    def get_cart_count():
        cart = session.get('cart', {})
        return sum(item.get('quantity', 0) for item in cart.values())
    return dict(get_cart_count=get_cart_count)

@app.route('/')
def index():
    return render_template('index.html', products=PRODUCTS)

@app.route('/shop')
def shop():
    return render_template('shop.html', products=PRODUCTS)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0
    
    for product_id, item in cart.items():
        product = next((p for p in PRODUCTS if str(p['id']) == product_id), None)
        if product:
            total = product['price'] * item['quantity']
            subtotal += total
            cart_items.append({
                'id': product_id,
                'name': product['name'],
                'flavour': product['flavour'],
                'price': product['price'],
                'quantity': item['quantity'],
                'image': product['image'],
                'total': total
            })
    
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    product_id = str(request.json.get('product_id'))
    quantity = int(request.json.get('quantity', 1))
    
    # Validate product exists
    product = next((p for p in PRODUCTS if str(p['id']) == product_id), None)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    cart = session.get('cart', {})
    
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {
            'quantity': quantity
        }
    
    session['cart'] = cart
    session.modified = True
    
    cart_count = sum(item['quantity'] for item in cart.values())
    
    return jsonify({
        'success': True,
        'message': f'{product["flavour"]} Flavour added to cart!',
        'cart_count': cart_count
    })

@app.route('/update-cart', methods=['POST'])
def update_cart():
    product_id = str(request.json.get('product_id'))
    quantity = int(request.json.get('quantity', 0))
    action = request.json.get('action', 'update')
    
    cart = session.get('cart', {})
    
    if action == 'remove' or quantity <= 0:
        if product_id in cart:
            del cart[product_id]
    else:
        if product_id in cart:
            cart[product_id]['quantity'] = quantity
    
    session['cart'] = cart
    session.modified = True
    
    # Recalculate
    cart_items = []
    subtotal = 0
    
    for pid, item in cart.items():
        product = next((p for p in PRODUCTS if str(p['id']) == pid), None)
        if product:
            total = product['price'] * item['quantity']
            subtotal += total
            cart_items.append({
                'id': pid,
                'name': product['name'],
                'price': product['price'],
                'quantity': item['quantity'],
                'total': total
            })
    
    cart_count = sum(item['quantity'] for item in cart.values())
    
    return jsonify({
        'success': True,
        'cart_count': cart_count,
        'subtotal': subtotal,
        'items': cart_items
    })

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('shop'))
    
    cart_items = []
    subtotal = 0
    
    for product_id, item in cart.items():
        product = next((p for p in PRODUCTS if str(p['id']) == product_id), None)
        if product:
            total = product['price'] * item['quantity']
            subtotal += total
            cart_items.append({
                'id': product_id,
                'name': product['name'],
                'flavour': product['flavour'],
                'price': product['price'],
                'quantity': item['quantity'],
                'image': product['image'],
                'total': total
            })
    
    if request.method == 'POST':
        # Process order
        customer_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        delivery_method = request.form.get('delivery_method')
        order_notes = request.form.get('order_notes', '')
        
        # Calculate delivery fee
        delivery_fee = 5.00 if delivery_method == 'delivery' else 0.00
        total = subtotal + delivery_fee
        
        # Generate order number
        order_number = f"PC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Save to database
        conn = get_db()
        cursor = conn.cursor()
        
        items_json = str(cart_items)  # Simple serialization
        
        cursor.execute('''
            INSERT INTO orders 
            (order_number, customer_name, phone, email, address, delivery_method, 
             order_notes, subtotal, delivery_fee, total, order_date, items)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_number, customer_name, phone, email, address, delivery_method,
            order_notes, subtotal, delivery_fee, total, datetime.now().isoformat(),
            items_json
        ))
        
        conn.commit()
        conn.close()
        
        # Clear cart
        session.pop('cart', None)
        
        # Store order in session for confirmation
        session['last_order'] = {
            'order_number': order_number,
            'customer_name': customer_name,
            'items': cart_items,
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'total': total,
            'delivery_method': delivery_method
        }
        
        return redirect(url_for('confirmation'))
    
    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/confirmation')
def confirmation():
    order = session.get('last_order')
    if not order:
        return redirect(url_for('index'))
    return render_template('confirmation.html', order=order)

@app.route('/clear-cart', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    return jsonify({'success': True})

# Initialize database
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
