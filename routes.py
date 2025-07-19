from flask import Blueprint, current_app, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import requests
import re
import unicodedata

from models import *
from utils import get_user_price, convert_currency, send_email, send_order_email, get_visible_products

def create_slug(text):
    """إنشاء slug من النص العربي أو الإنجليزي"""
    if not text:
        return ""
    
    # تحويل إلى نص صغير
    text = text.lower()
    
    # إزالة الأحرف الخاصة والرموز
    text = re.sub(r'[^\w\s\u0600-\u06FF-]', '', text)
    
    # استبدال المساحات بشرطات
    text = re.sub(r'[-\s]+', '-', text)
    
    # إزالة الشرطات من البداية والنهاية
    text = text.strip('-')
    
    return text

# إنشاء Blueprint للمسارات
main = Blueprint('main', __name__)

@main.route('/')
def index():
    # المنتجات الأساسية - فقط المنتجات المرئية للمستخدم
    products = get_visible_products(current_user if current_user.is_authenticated else None).limit(20).all()
    
    # المنتجات المميزة (للسلايدر الرئيسي)
    featured_products = get_visible_products(current_user if current_user.is_authenticated else None).limit(4).all()
    
    # منتجات الهدايا
    gift_products = get_visible_products(current_user if current_user.is_authenticated else None, category='gift').limit(16).all()
    
    # منتجات العروض
    offer_products = get_visible_products(current_user if current_user.is_authenticated else None).limit(7).all()
    
    # منتجات أخرى
    other_products = get_visible_products(current_user if current_user.is_authenticated else None).limit(8).all()
    
    # العروض المحدودة
    limited_offers = get_visible_products(current_user if current_user.is_authenticated else None).limit(4).all()
    
    user_currency = session.get('currency', 'SAR')
    
    # تحويل أسعار المنتجات
    all_products = products + featured_products + gift_products + offer_products + other_products + limited_offers
    for product in all_products:
        if current_user.is_authenticated:
            # استخدام الدالة المحدثة التي تدعم الأسعار المخصصة
            price = get_user_price(product, current_user.customer_type, current_user)
        else:
            price = product.regular_price
        product.display_price = convert_currency(price, 'SAR', user_currency)
    
    # العروض الرئيسية
    main_offers = MainOffer.query.filter_by(is_active=True).order_by(MainOffer.display_order).all()
    
    # بطاقات الهدايا
    gift_card_sections = GiftCardSection.query.filter_by(is_active=True).order_by(GiftCardSection.display_order).all()
    
    # ماركات أخرى
    other_brands = OtherBrand.query.filter_by(is_active=True).order_by(OtherBrand.display_order).all()
    
    # الأقسام الرئيسية للهيدر
    main_categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).limit(8).all()
    
    # جميع الأقسام الفرعية من كافة الأقسام الرئيسية
    subcategories = Subcategory.query.filter_by(is_active=True).order_by(Subcategory.display_order, Subcategory.name).all()
    
    return render_template('index.html', 
                         products=products,
                         featured_products=featured_products,
                         gift_products=gift_products,
                         offer_products=offer_products,
                         other_products=other_products,
                         limited_offers=limited_offers,
                         main_offers=main_offers,
                         gift_card_sections=gift_card_sections,
                         other_brands=other_brands,
                         main_categories=main_categories,
                         subcategories=subcategories)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'تم تسجيل الدخول بنجاح',
                    'redirect': url_for('main.index')
                })
            else:
                flash('تم تسجيل الدخول بنجاح', 'success')
                return redirect(url_for('main.index'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'})
            else:
                flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    # معالجة POST request
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
    
    # التحقق من صحة البيانات
    if not email or not password:
        error_msg = 'البريد الإلكتروني وكلمة المرور مطلوبان'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        else:
            flash(error_msg, 'error')
            return render_template('register.html')
    
    if len(password) < 6:
        error_msg = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        else:
            flash(error_msg, 'error')
            return render_template('register.html')
    
    if User.query.filter_by(email=email).first():
        error_msg = 'البريد الإلكتروني مسجل مسبقاً'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        else:
            flash(error_msg, 'error')
            return render_template('register.html')
    
    try:
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        success_msg = 'تم إنشاء الحساب بنجاح'
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg})
        else:
            flash(success_msg, 'success')
            return redirect(url_for('main.index'))
    
    except Exception as e:
        db.session.rollback()
        error_msg = f'حدث خطأ أثناء إنشاء الحساب: {str(e)}'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        else:
            flash(error_msg, 'error')
            return render_template('register.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@main.route('/kyc-upgrade', methods=['GET', 'POST'])
@login_required
def kyc_upgrade():
    if request.method == 'POST':
        try:
            # التحقق من نوع الطلب (JSON أم form data عادي)
            if request.content_type and 'multipart/form-data' in request.content_type:
                # معالجة طلب AJAX مع ملفات
                current_user.full_name = request.form.get('full_name')
                current_user.phone = request.form.get('phone')
                birth_date_str = request.form.get('birth_date')
                if birth_date_str:
                    current_user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                current_user.nationality = request.form.get('nationality')
                current_user.kyc_status = 'pending'
                current_user.document_type = request.form.get('document_type')
                
                # حفظ مستندات الهوية
                upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'kyc-documents')
                os.makedirs(upload_folder, exist_ok=True)
                
                document_type = request.form.get('document_type')
                if document_type == 'national_id':
                    # حفظ صور الهوية الوطنية
                    for field_name, file_attr in [('id_front', 'id_front_image'), ('id_back', 'id_back_image')]:
                        if field_name in request.files:
                            file = request.files[field_name]
                            if file and file.filename:
                                filename = f"{current_user.id}_{field_name}_{secure_filename(file.filename)}"
                                file_path = os.path.join(upload_folder, filename)
                                file.save(file_path)
                                setattr(current_user, file_attr, filename)
                elif document_type == 'passport':
                    # حفظ صورة جواز السفر
                    if 'passport' in request.files:
                        file = request.files['passport']
                        if file and file.filename:
                            filename = f"{current_user.id}_passport_{secure_filename(file.filename)}"
                            file_path = os.path.join(upload_folder, filename)
                            file.save(file_path)
                            current_user.passport_image = filename
                elif document_type == 'driver_license':
                    # حفظ صورة رخصة القيادة
                    if 'driver_license' in request.files:
                        file = request.files['driver_license']
                        if file and file.filename:
                            filename = f"{current_user.id}_driver_license_{secure_filename(file.filename)}"
                            file_path = os.path.join(upload_folder, filename)
                            file.save(file_path)
                            current_user.driver_license_image = filename
                
                # حفظ صور التحقق من الوجه
                face_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'face-verification')
                os.makedirs(face_folder, exist_ok=True)
                
                for field_name, file_attr in [
                    ('face_photo_front', 'face_photo_front'),
                    ('face_photo_right', 'face_photo_right'), 
                    ('face_photo_left', 'face_photo_left')
                ]:
                    if field_name in request.files:
                        file = request.files[field_name]
                        if file and file.filename:
                            filename = f"{current_user.id}_{field_name}_{secure_filename(file.filename)}"
                            file_path = os.path.join(face_folder, filename)
                            file.save(file_path)
                            setattr(current_user, file_attr, filename)
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'تم حفظ البيانات بنجاح'})
            else:
                # معالجة النموذج العادي (fallback)
                current_user.full_name = request.form.get('full_name')
                current_user.phone = request.form.get('phone')
                birth_date_str = request.form.get('birth_date')
                if birth_date_str:
                    current_user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                current_user.nationality = request.form.get('nationality')
                current_user.kyc_status = 'pending'
                
                db.session.commit()
                flash('تم إرسال طلب التحقق بنجاح', 'success')
                return redirect(url_for('main.profile'))
                
        except Exception as e:
            if request.content_type and 'multipart/form-data' in request.content_type:
                return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
            else:
                flash(f'حدث خطأ: {str(e)}', 'error')
    
    return render_template('kyc_upgrade.html')

@main.route('/product/<int:product_id>')
@main.route('/product/<int:product_id>/<slug>')
def product_detail(product_id, slug=None):
    # التحقق من وجود المنتج والتأكد من أن المستخدم يمكنه رؤيته
    from models import ProductUserAccess
    
    product = Product.query.get_or_404(product_id)
    
    # التحقق من صحة الـ slug إذا تم توفيره
    correct_slug = create_slug(product.name)
    if slug and slug != correct_slug:
        return redirect(url_for('main.product_detail', product_id=product_id, slug=correct_slug))
    
    # التحقق من قيود الرؤية
    if product.restricted_visibility:
        if not current_user.is_authenticated:
            # المستخدم غير مسجل لا يستطيع رؤية المنتجات المقيدة
            flash('هذا المنتج غير متاح', 'error')
            return redirect(url_for('main.index'))
        
        if not current_user.is_admin:
            # التحقق من أن المستخدم مسموح له برؤية هذا المنتج
            access = ProductUserAccess.query.filter_by(
                product_id=product_id,
                user_id=current_user.id
            ).first()
            
            if not access:
                flash('هذا المنتج غير متاح لك', 'error')
                return redirect(url_for('main.index'))
    
    user_currency = session.get('currency', 'SAR')
    
    if current_user.is_authenticated:
        # استخدام الدالة المحدثة التي تدعم الأسعار المخصصة
        price = get_user_price(product, current_user.customer_type, current_user)
    else:
        price = product.regular_price
    
    product.display_price = convert_currency(price, 'SAR', user_currency)
    
    return render_template('product_detail.html', product=product)

@main.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    # إضافة إلى السلة (يمكن استخدام session أو جدول منفصل)
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    
    # حساب إجمالي عدد العناصر في السلة
    cart_count = sum(cart.values())
    
    return jsonify({
        'success': True, 
        'message': 'تمت إضافة المنتج إلى السلة',
        'cart_count': cart_count
    })

@main.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            # استخدام الدالة المحدثة التي تدعم الأسعار المخصصة
            price = get_user_price(product, current_user.customer_type, current_user)
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'total': price * quantity
            })
            total += price * quantity
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@main.route('/update-cart-quantity', methods=['POST'])
@login_required
def update_cart_quantity():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    cart = session.get('cart', {})
    if str(product_id) in cart:
        if quantity > 0:
            cart[str(product_id)] = quantity
        else:
            del cart[str(product_id)]
        session['cart'] = cart
        
        cart_count = sum(cart.values())
        return jsonify({
            'success': True,
            'message': 'تم تحديث الكمية',
            'cart_count': cart_count
        })
    
    return jsonify({'success': False, 'message': 'المنتج غير موجود في السلة'})

@main.route('/remove-from-cart', methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        
        cart_count = sum(cart.values())
        return jsonify({
            'success': True,
            'message': 'تم حذف المنتج من السلة',
            'cart_count': cart_count
        })
    
    return jsonify({'success': False, 'message': 'المنتج غير موجود في السلة'})

@main.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return jsonify({'success': False, 'message': 'السلة فارغة'})
    
    # إنشاء طلب جديد
    order = Order(
        user_id=current_user.id,
        order_number=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}",
        total_amount=0,
        currency=session.get('currency', 'SAR')
    )
    db.session.add(order)
    db.session.flush()
    
    total_amount = 0
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            price = get_user_price(product, current_user.customer_type)
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                price=price
            )
            db.session.add(order_item)
            total_amount += price * quantity
    
    order.total_amount = total_amount
    db.session.commit()
    
    # مسح السلة
    session.pop('cart', None)
    
    return jsonify({'success': True, 'order_id': order.id, 'redirect': url_for('main.payment', order_id=order.id)})

@main.route('/payment/<int:order_id>')
@login_required
def payment(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return redirect(url_for('main.index'))
    
    payment_gateways = PaymentGateway.query.filter_by(is_active=True).all()
    
    return render_template('payment.html', order=order, payment_gateways=payment_gateways)

@main.route('/process-payment', methods=['POST'])
@login_required
def process_payment():
    data = request.get_json()
    order_id = data.get('order_id')
    payment_method = data.get('payment_method')
    
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    # محاكاة عملية الدفع
    order.payment_status = 'completed'
    order.payment_method = payment_method
    order.order_status = 'completed'
    
    # تخصيص أكواد للمنتجات
    for item in order.items:
        for i in range(item.quantity):
            available_code = ProductCode.query.filter_by(
                product_id=item.product_id,
                is_used=False
            ).first()
            
            if available_code:
                available_code.is_used = True
                available_code.used_at = datetime.utcnow()
                available_code.order_id = order.id
    
    db.session.commit()
    
    # إرسال بريد إلكتروني بالأكواد
    send_order_email(order)
    
    return jsonify({'success': True, 'message': 'تم إتمام الدفع بنجاح'})

@main.route('/set-currency/<currency>')
def set_currency(currency):
    session['currency'] = currency
    return redirect(request.referrer or url_for('main.index'))

@main.route('/category/<int:category_id>')
@main.route('/category/<int:category_id>/<slug>')
def category_products(category_id, slug=None):
    """عرض منتجات قسم معين"""
    from models import Category
    
    category = Category.query.get_or_404(category_id)
    
    # التحقق من صحة الـ slug إذا تم توفيره
    correct_slug = create_slug(category.name)
    if slug and slug != correct_slug:
        return redirect(url_for('main.category_products', category_id=category_id, slug=correct_slug))
    
    # جلب المنتجات المرئية للمستخدم في هذا القسم
    products = get_visible_products(
        current_user if current_user.is_authenticated else None,
        category=category.name_en or category.name
    ).all()
    
    # تحويل الأسعار
    user_currency = session.get('currency', 'SAR')
    for product in products:
        if current_user.is_authenticated:
            price = get_user_price(product, current_user.customer_type, current_user)
        else:
            price = product.regular_price
        product.display_price = convert_currency(price, 'SAR', user_currency)
    
    return render_template('category_products.html', 
                         category=category, 
                         products=products)

@main.route('/subcategory/<int:subcategory_id>')
@main.route('/subcategory/<int:subcategory_id>/<slug>')
def subcategory_products(subcategory_id, slug=None):
    """عرض منتجات قسم فرعي معين"""
    subcategory = Subcategory.query.get_or_404(subcategory_id)
    
    # التحقق من صحة الـ slug إذا تم توفيره
    correct_slug = create_slug(subcategory.name)
    if slug and slug != correct_slug:
        return redirect(url_for('main.subcategory_products', subcategory_id=subcategory_id, slug=correct_slug))
    
    # الحصول على المنتجات المرتبطة بهذا القسم الفرعي
    # نفترض أن المنتجات لها علاقة مع الأقسام الفرعية
    # إذا لم تكن موجودة، يمكننا استخدام category للقسم الرئيسي
    products_query = get_visible_products(current_user if current_user.is_authenticated else None)
    
    # فلترة المنتجات حسب القسم الرئيسي للقسم الفرعي
    products = products_query.filter(Product.category == subcategory.parent_category.name).all()
    
    user_currency = session.get('currency', 'SAR')
    
    # تحويل الأسعار
    for product in products:
        if current_user.is_authenticated:
            price = get_user_price(product, current_user.customer_type, current_user)
        else:
            price = product.regular_price
        product.display_price = convert_currency(price, 'SAR', user_currency)
    
    return render_template('subcategory_products.html', 
                         subcategory=subcategory,
                         products=products)

@main.route('/categories')
def all_categories():
    """عرض جميع الأقسام"""
    from models import Category
    
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order, Category.name).all()
    return render_template('categories.html', categories=categories)
