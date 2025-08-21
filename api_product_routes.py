from flask import Blueprint, jsonify, request, render_template
from flask_login import current_user
from models import Product, Category, Order, OrderItem, db
from utils import get_visible_products, get_user_price, convert_currency
from datetime import datetime

api_products = Blueprint('api_products', __name__)

@api_products.route('/api/v1/products', methods=['GET'])
def get_products():
    """Get all visible products with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category_id = request.args.get('category_id', type=int)
    
    query = get_visible_products(current_user if current_user.is_authenticated else None)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'products': [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': get_user_price(p, current_user if current_user.is_authenticated else None),
            'image_url': p.image_url,
            'category_id': p.category_id,
            'stock': p.stock_quantity,
            'currency': 'SAR'  # نستخدم SAR كعملة افتراضية
        } for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': products.page
    })

@api_products.route('/api/v1/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product details"""
    product = Product.query.get_or_404(product_id)
    
    # التحقق من صلاحية الوصول للمنتج
    if product.visibility == 'restricted' and (not current_user.is_authenticated or not current_user.is_admin):
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': get_user_price(product, current_user if current_user.is_authenticated else None),
        'image_url': product.image_url,
        'category_id': product.category_id,
        'stock': product.stock_quantity,
        'currency': 'SAR',  # نستخدم SAR كعملة افتراضية
        'details': product.description  # استخدام description بدلاً من details الذي قد لا يكون موجوداً
    })

@api_products.route('/api/v1/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    categories = Category.query.all()
    return jsonify({
        'categories': [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'image_url': c.image_url
        } for c in categories]
    })

@api_products.route('/api/v1/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
        
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
        
    # Create new order
    order = Order(
        user_id=current_user.id,
        status='pending',
        created_at=datetime.utcnow()
    )
    db.session.add(order)
    
    total_amount = 0
    order_items = []
    
    # Add order items
    for item in data['items']:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({'error': f'Product {item["product_id"]} not found'}), 404
            
        quantity = item.get('quantity', 1)
        price = get_user_price(product, current_user)
        
        order_item = OrderItem(
            order=order,
            product=product,
            quantity=quantity,
            price=price
        )
        order_items.append(order_item)
        total_amount += price * quantity
    
    order.total_amount = total_amount
    db.session.add_all(order_items)
    db.session.commit()
    
    return jsonify({
        'order_id': order.id,
        'total_amount': order.total_amount,
        'status': order.status,
        'created_at': order.created_at.isoformat()
    }), 201
