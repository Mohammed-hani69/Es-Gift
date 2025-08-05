from flask import Blueprint, current_app, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import requests
import re
import unicodedata
import json
import logging

from models import *
from utils import get_user_price, convert_currency, send_email, send_order_email, get_visible_products, send_order_confirmation_without_codes, generate_order_number
from email_pro_verification_service import send_user_verification_code, verify_user_code, resend_user_verification_code, is_verification_pending
from send_by_hostinger import send_order_confirmation

# إعداد التسجيل
logger = logging.getLogger(__name__)

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
    
    # المنتجات المضافة حديثاً من API مع جلب مباشر وتحديث تلقائي
    api_products = []
    try:
        # أولاً: جلب المنتجات المحفوظة محلياً
        recent_api_products = APIProduct.query.filter_by(is_active=True).order_by(APIProduct.created_at.desc()).limit(12).all()
        
        # ثانياً: محاولة جلب منتجات حديثة مباشرة من OneCard API إذا أمكن
        fresh_products = []
        try:
            from api_services import APIManager
            api_settings = APISettings.query.filter_by(api_type='onecard', is_active=True).first()
            
            if api_settings:
                service = APIManager.get_api_service(api_settings)
                # جلب أحدث المنتجات من API
                response = service.get_products_list()
                
                if 'error' not in response:
                    products_data = []
                    if isinstance(response, dict):
                        if 'products' in response:
                            products_data = response['products']
                        elif 'result' in response:
                            products_data = response['result']
                        elif 'data' in response:
                            products_data = response['data']
                    elif isinstance(response, list):
                        products_data = response
                    
                    # جلب أول 6 منتجات من API مباشرة
                    for i, product_data in enumerate(products_data[:6]):
                        try:
                            # OneCard API يستخدم productID وليس id
                            product_id = str(product_data.get('productID') or product_data.get('id') or product_data.get('productId') or product_data.get('ProductId', ''))
                            if product_id:
                                # استخراج الاسم العربي أو الإنجليزي
                                product_name = product_data.get('nameAr') or product_data.get('nameEn') or product_data.get('name') or product_data.get('productName') or 'منتج من OneCard'
                                # استخراج الفئة العربية أو الإنجليزية  
                                category_name = product_data.get('categoryNameAr') or product_data.get('categoryNameEn') or product_data.get('category') or 'منتجات OneCard'
                                # استخراج السعر المناسب
                                price = float(product_data.get('recommendedRetailPriceAfterVat') or product_data.get('price') or product_data.get('sellingPrice') or 0)
                                
                                # استخراج رابط الصورة من API
                                image_url = product_data.get('logo') or product_data.get('image') or product_data.get('imageUrl') or product_data.get('logoUrl') or 'default-product.jpg'
                                # إذا كان الرابط نسبي، اجعله مطلق
                                if image_url and not image_url.startswith('http') and image_url != 'default-product.jpg':
                                    # معظم الصور في OneCard تأتي كـ relative paths
                                    image_url = f"https://cdn.onecard.net/images/{image_url}" if '/' not in image_url else image_url
                                
                                fresh_products.append({
                                    'id': f"fresh_{i}_{product_id}",
                                    'name': product_name,
                                    'description': f'منتج جديد من OneCard API - {category_name}',
                                    'regular_price': price,
                                    'image_url': image_url,
                                    'category': category_name,
                                    'is_api_product': True,
                                    'external_product_id': product_id,
                                    'provider': 'OneCard',
                                    'stock_status': product_data.get('available', True),
                                    'currency': 'SAR',  # تحويل من USD إلى SAR
                                    'is_fresh': True  # إشارة إلى أنه منتج محدث من API
                                })
                        except Exception as e:
                            current_app.logger.warning(f"Error processing fresh product: {e}")
                            continue
                
                current_app.logger.info(f"Extracted {len(fresh_products)} products from API response")
        except Exception as e:
            current_app.logger.warning(f"Could not fetch fresh products from API: {e}")
        
        # دمج المنتجات المحدثة مع المحفوظة محلياً
        for fresh_product in fresh_products:
            product_obj = type('Product', (), fresh_product)()
            api_products.append(product_obj)
        
        current_app.logger.info(f"Found {len(fresh_products)} fresh products from API")
        
        # إضافة المنتجات المحفوظة محلياً (تجنب التكرار)
        for api_product in recent_api_products[:6]:  # أول 6 منتجات محفوظة
            product_obj = type('Product', (), {
                'id': api_product.id,
                'name': api_product.name,
                'description': api_product.description or 'منتج من API',
                'regular_price': float(api_product.price) if api_product.price else 0.0,
                'image_url': 'default-product.jpg',
                'category': api_product.category or 'منتجات جديدة',
                'is_api_product': True,
                'external_product_id': api_product.external_product_id,
                'provider': api_product.provider or 'API',
                'stock_status': api_product.stock_status,
                'currency': api_product.currency or 'SAR',
                'is_fresh': False
            })()
            api_products.append(product_obj)
            
    except Exception as e:
        current_app.logger.error(f"Error fetching API products: {e}")
        api_products = []
    
    current_app.logger.info(f"Total API products to display: {len(api_products)}")
    
    current_app.logger.info(f"Total API products to display: {len(api_products)}")
    
    user_currency = session.get('currency', 'SAR')
    
    # تحويل أسعار المنتجات
    all_products = products + featured_products + gift_products + offer_products + other_products + limited_offers
    for product in all_products:
        if current_user.is_authenticated:
            # استخدام الدالة المحدثة التي تدعم الأسعار المخصصة
            price = get_user_price(product, current_user.customer_type, current_user)
        else:
            price = product.regular_price
        
        # التحقق من صحة السعر
        if price is None or price == 0:
            price = product.regular_price if product.regular_price else 0
        
        # حفظ السعر الأصلي بالريال السعودي
        product.original_price_sar = price
        product.display_price = convert_currency(price, 'SAR', user_currency)
        
        # تطبيق نفس التحويل على الأسعار الأخرى إذا لزم الأمر
        if hasattr(product, 'regular_price') and product.regular_price:
            product.regular_price_converted = convert_currency(product.regular_price, 'SAR', user_currency)
    
    # تحويل أسعار المنتجات من API
    for product in api_products:
        price = product.regular_price if product.regular_price else 0
        product.original_price_sar = price
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
    
    # جلب العملات النشطة لعرضها في المنطقة العلوية
    active_currencies = Currency.query.filter_by(is_active=True).order_by(Currency.code).all()
    
    # المقالات المنشورة للعرض في الصفحة الرئيسية
    published_articles = Article.query.filter_by(is_published=True).order_by(Article.created_at.desc()).limit(4).all()
    
    return render_template('index.html', 
                         products=products,
                         featured_products=featured_products,
                         gift_products=gift_products,
                         offer_products=offer_products,
                         other_products=other_products,
                         limited_offers=limited_offers,
                         api_products=api_products,
                         main_offers=main_offers,
                         gift_card_sections=gift_card_sections,
                         other_brands=other_brands,
                         main_categories=main_categories,
                         subcategories=subcategories,
                         currencies=active_currencies,
                         published_articles=published_articles,
                         current_currency=user_currency)

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
            # التحقق من تفعيل البريد الإلكتروني
            if not user.is_verified:
                if request.is_json:
                    return jsonify({
                        'success': False, 
                        'message': 'يجب تأكيد البريد الإلكتروني أولاً',
                        'verification_required': True,
                        'email': user.email
                    })
                else:
                    flash('يجب تأكيد البريد الإلكتروني قبل تسجيل الدخول', 'warning')
                    return render_template('verification_sent.html', email=user.email)
            
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

@main.route('/refresh-prices', methods=['POST'])
@login_required
def refresh_prices():
    """تحديث الأسعار للمستخدم الحالي بناءً على نوع العميل"""
    try:
        from utils import refresh_user_data, get_customer_type_display_name
        
        # تحديث بيانات المستخدم والأسعار
        success = refresh_user_data(current_user)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'تم تحديث الأسعار وفقاً لنوع العميل: {get_customer_type_display_name(current_user.customer_type)}',
                'customer_type': current_user.customer_type,
                'force_reload': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'حدث خطأ أثناء تحديث الأسعار'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        })

@main.route('/clear-price-notification', methods=['POST'])
@login_required 
def clear_price_notification():
    """إزالة إشعار تحديث الأسعار من الجلسة"""
    session.pop('show_price_update_notification', None)
    session.pop('price_update_message', None)
    return jsonify({'success': True})

@main.route('/api/get-product-price/<int:product_id>')
@login_required
def get_product_price(product_id):
    """الحصول على سعر المنتج المحدث حسب نوع العميل"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # الحصول على السعر المناسب للمستخدم
        price = get_user_price(product, current_user.customer_type, current_user)
        
        # التحقق من صحة السعر
        if price is None or price == 0:
            price = product.regular_price if product.regular_price else 0
        
        # تحويل السعر للعملة المطلوبة
        user_currency = session.get('currency', 'SAR')
        converted_price = convert_currency(price, 'SAR', user_currency)
        
        from utils import get_customer_type_display_name
        
        return jsonify({
            'success': True,
            'price': converted_price,
            'original_price': price,
            'currency': user_currency,
            'customer_type': current_user.customer_type,
            'customer_type_name': get_customer_type_display_name(current_user.customer_type)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        })

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    # معالجة POST request
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '').strip()  # الاسم الكامل (اختياري)
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name', '').strip()  # الاسم الكامل (اختياري)
    
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
            full_name=name if name else None,  # حفظ الاسم الكامل إذا تم إدخاله
            password_hash=generate_password_hash(password),
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.flush()  # للحصول على user.id قبل commit
        
        # إنشاء حدود المستخدم بالقيم الافتراضية للمستخدم العادي
        from wallet_utils import create_user_limits
        user_limits = create_user_limits(user)
        
        # إنشاء محفظة المستخدم
        from wallet_utils import get_or_create_wallet
        wallet = get_or_create_wallet(user)
        
        db.session.commit()
        
        # إرسال كود التحقق باستخدام Email Sender Pro
        user_display_name = name if name else email.split('@')[0]
        verification_sent, message, verification_code = send_user_verification_code(email, user_display_name)
        
        if verification_sent:
            # حفظ بيانات المستخدم في الجلسة مؤقتاً
            session['pending_user_id'] = user.id
            session['pending_user_email'] = email
            session['pending_user_name'] = user_display_name
            session['pending_verification_email'] = email  # إضافة للتوافق مع صفحة التحقق
            
            success_msg = 'تم إنشاء الحساب بنجاح! تم إرسال كود التحقق إلى بريدك الإلكتروني'
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': success_msg,
                    'verification_required': True,
                    'email': email,
                    'redirect_url': url_for('auth.verify_email_code_page')
                })
            else:
                flash(success_msg, 'success')
                return redirect(url_for('auth.verify_email_code_page'))
        else:
            # في حالة فشل إرسال كود التحقق، نسجل الدخول مباشرة
            login_user(user)
            success_msg = f'تم إنشاء الحساب بنجاح! (تعذر إرسال كود التحقق: {message})'
            if request.is_json:
                return jsonify({'success': True, 'message': success_msg})
            else:
                flash(success_msg, 'warning')
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

@main.route('/verify-email-code')
def verify_email_code_page():
    """صفحة إدخال كود التحقق"""
    user_email = session.get('pending_verification_email') or session.get('pending_user_email')
    if not user_email:
        flash('جلسة التحقق منتهية الصلاحية', 'warning')
        return redirect(url_for('main.register'))
    
    return render_template('auth/verify_email_code.html', user_email=user_email)

@main.route('/verify-email-code', methods=['POST'])
def verify_email_code():
    """التحقق من كود التحقق المرسل"""
    try:
        from email_pro_verification_service import verify_user_code
        
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني وكود التحقق مطلوبان'
            })
        
        # التحقق من الكود
        success, message = verify_user_code(email, code)
        
        if success:
            # البحث عن المستخدم وتفعيل الحساب
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_verified = True
                db.session.commit()
                
                # تسجيل دخول المستخدم
                login_user(user)
                
                # مسح بيانات الجلسة
                session.pop('pending_verification_email', None)
                session.pop('pending_user_id', None)
                session.pop('pending_user_email', None)
                session.pop('pending_user_name', None)
                session.pop('verification_email', None)
                session.pop('verification_pending', None)
                
                return jsonify({
                    'success': True,
                    'message': 'تم التحقق من البريد الإلكتروني بنجاح'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'المستخدم غير موجود'
                })
        else:
            return jsonify({
                'success': False,
                'message': message
            })
            
    except Exception as e:
        logger.error(f"خطأ في التحقق من الكود: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء التحقق من الكود'
        })

@main.route('/resend-verification-code', methods=['POST'])
def resend_verification_code():
    """إعادة إرسال كود التحقق"""
    try:
        from email_pro_verification_service import resend_user_verification_code
        
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني مطلوب'
            })
        
        # البحث عن المستخدم
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            })
        
        # إرسال كود جديد
        success, message = resend_user_verification_code(email)
        
        return jsonify({
            'success': success,
            'message': message
        })
            
    except Exception as e:
        logger.error(f"خطأ في إعادة إرسال الكود: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إعادة إرسال الكود'
        })

@main.route('/send-welcome-email', methods=['POST'])
def send_welcome_email_route():
    """إرسال رسالة ترحيبية للمستخدم الجديد"""
    try:
        from send_by_hostinger import send_welcome_email
        
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني مطلوب'
            })
        
        # البحث عن المستخدم
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            })
        
        # إرسال رسالة ترحيبية
        customer_name = user.full_name or user.email.split('@')[0]
        success, message = send_welcome_email(email, customer_name)
        
        return jsonify({
            'success': success,
            'message': message
        })
            
    except Exception as e:
        logger.error(f"خطأ في إرسال رسالة الترحيب: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إرسال رسالة الترحيب'
        })

@main.route('/verify-email/<token>')
def verify_email(token):
    """التحقق من البريد الإلكتروني باستخدام الرمز"""
    try:
        from email_verification_service import EmailVerificationService  # Ensure the correct import path
        success, result = EmailVerificationService.verify_token(token)
        
        if success:
            user = result
            # تفعيل الحساب
            user.is_verified = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            db.session.commit()
            
            # تسجيل دخول المستخدم
            login_user(user)
            
            flash('تم التحقق من بريدك الإلكتروني بنجاح! مرحباً بك في ES-GIFT', 'success')
            return redirect(url_for('main.index'))
        else:
            error_message = result
            flash(error_message, 'error')
            return render_template('verification_error.html', error=error_message)
            
    except Exception as e:
        flash('حدث خطأ أثناء التحقق من البريد الإلكتروني', 'error')
        return render_template('verification_error.html', error='حدث خطأ غير متوقع')

@main.route('/resend-verification', methods=['POST'])
def resend_verification():
    """إعادة إرسال بريد التحقق"""
    try:
        from email_verification_service import EmailVerificationService  # Ensure the correct import path
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'البريد الإلكتروني مطلوب'})
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'البريد الإلكتروني غير مسجل'})
        
        if user.is_verified:
            return jsonify({'success': False, 'message': 'تم التحقق من هذا الحساب مسبقاً'})
        
        success, message = EmailVerificationService.resend_verification_email(user)
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء إعادة الإرسال'})

@main.route('/verification-status/<email>')
def verification_status(email):
    """التحقق من حالة التحقق من البريد"""
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'verified': False, 'exists': False})
        
        return jsonify({
            'verified': user.is_verified,
            'exists': True,
            'email': user.email
        })
        
    except Exception as e:
        return jsonify({'verified': False, 'exists': False, 'error': str(e)})

@main.route('/profile')
@login_required
def profile():
    # الحصول على آخر الطلبات
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    
    # الحصول على آخر الفواتير
    recent_invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).limit(3).all()
    
    return render_template('profile.html', 
                         user=current_user, 
                         recent_orders=recent_orders,
                         recent_invoices=recent_invoices)

@main.route('/my-orders')
@login_required
def my_orders():
    """عرض جميع طلبات المستخدم"""
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id)\
                       .order_by(Order.created_at.desc())\
                       .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('my_orders.html', orders=orders)

@main.route('/invoices')
@login_required
def user_invoices():
    """عرض جميع فواتير المستخدم"""
    page = request.args.get('page', 1, type=int)
    invoices = Invoice.query.filter_by(user_id=current_user.id)\
                           .order_by(Invoice.created_at.desc())\
                           .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('user_invoices.html', invoices=invoices)

@main.route('/invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    """عرض تفاصيل فاتورة محددة"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # التأكد من أن الفاتورة تخص المستخدم الحالي
    if invoice.user_id != current_user.id:
        flash('غير مسموح لك بعرض هذه الفاتورة', 'error')
        return redirect(url_for('main.user_invoices'))
    
    return render_template('invoice_detail.html', invoice=invoice)

@main.route('/order/<int:order_id>/download-excel')
@login_required
def download_order_excel(order_id):
    """تحميل ملف Excel الخاص بالطلب"""
    order = Order.query.get_or_404(order_id)
    
    # التأكد من أن الطلب يخص المستخدم الحالي
    if order.user_id != current_user.id:
        flash('غير مسموح لك بتحميل هذا الملف', 'error')
        return redirect(url_for('main.my_orders'))
    
    # التأكد من وجود ملف Excel
    if not order.excel_file_path:
        flash('لا يوجد ملف Excel متاح لهذا الطلب', 'error')
        return redirect(url_for('main.my_orders'))
    
    # التأكد من وجود الملف على القرص
    file_path = os.path.join(current_app.static_folder, order.excel_file_path)
    if not os.path.exists(file_path):
        flash('الملف غير موجود', 'error')
        return redirect(url_for('main.my_orders'))
    
    # إرسال الملف للتحميل
    return send_file(file_path, 
                    as_attachment=True, 
                    download_name=f'order_{order.id}_codes.xlsx',
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    if invoice.pdf_file_path and os.path.exists(invoice.pdf_file_path):
        return send_file(invoice.pdf_file_path, 
                        as_attachment=True, 
                        download_name=f"invoice_{invoice.invoice_number}.pdf")
    else:
        flash('ملف الفاتورة غير متوفر', 'error')
        return redirect(url_for('main.view_invoice', invoice_id=invoice_id))

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
    
    # التحقق من صحة السعر
    if price is None or price == 0:
        price = product.regular_price if product.regular_price else 0
    
    product.original_price_sar = price
    product.display_price = convert_currency(price, 'SAR', user_currency)
    
    return render_template('product_detail.html', product=product)

@main.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    """إضافة منتج إلى السلة"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        is_api_product = data.get('is_api_product', False)
        
        if not product_id:
            return jsonify({'success': False, 'message': 'معرف المنتج مطلوب'})
        
        # إضافة إلى السلة باستخدام session
        cart = session.get('cart', {})
        api_cart = session.get('api_cart', {})  # سلة منفصلة للمنتجات من API
        
        if is_api_product:
            # التعامل مع المنتجات من API
            api_product = APIProduct.query.get(product_id)
            if not api_product:
                return jsonify({'success': False, 'message': 'المنتج غير موجود'})
            
            # التحقق من حالة المخزون
            if not api_product.stock_status:
                return jsonify({'success': False, 'message': 'المنتج غير متوفر'})
            
            # التحقق من حالة API
            if not api_product.api_setting.is_active:
                return jsonify({'success': False, 'message': 'خدمة المنتج غير متاحة حالياً'})
            
            # إضافة إلى السلة الخاصة بمنتجات API
            api_cart[str(product_id)] = api_cart.get(str(product_id), 0) + quantity
            session['api_cart'] = api_cart
            
        else:
            # التعامل مع المنتجات العادية
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'success': False, 'message': 'المنتج غير موجود'})
            
            # التحقق من قيود الرؤية
            if product.visibility == 'restricted':
                if not current_user.is_admin:
                    access = ProductUserAccess.query.filter_by(
                        product_id=product_id,
                        user_id=current_user.id
                    ).first()
                    if not access:
                        return jsonify({'success': False, 'message': 'هذا المنتج غير متاح لك'})
            
            # إضافة إلى السلة العادية
            cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
            session['cart'] = cart
        
        # حساب إجمالي عدد العناصر في السلة
        cart_count = sum(cart.values()) + sum(api_cart.values())
        
        return jsonify({
            'success': True, 
            'message': 'تمت إضافة المنتج إلى السلة',
            'cart_count': cart_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Add to cart error: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ، يرجى المحاولة مرة أخرى'})


@main.route('/purchase-api-product', methods=['POST'])
@login_required
def purchase_api_product():
    """شراء منتج من OneCard API مباشرة مع دعم شامل للأكواد والفواتير"""
    try:
        data = request.get_json()
        api_product_id = data.get('api_product_id') or data.get('product_id')
        external_product_id = data.get('external_product_id')
        quantity = int(data.get('quantity', 1))
        
        # التحقق من المعرفات
        if not api_product_id and not external_product_id:
            return jsonify({'success': False, 'message': 'معرف المنتج مطلوب'})
        
        # جلب المنتج من قاعدة البيانات أو API
        api_product = None
        if api_product_id:
            api_product = APIProduct.query.get(api_product_id)
            if api_product:
                external_product_id = api_product.external_product_id
        
        if not external_product_id:
            return jsonify({'success': False, 'message': 'معرف المنتج الخارجي غير موجود'})
        
        # التحقق من إعدادات OneCard API
        api_settings = APISettings.query.filter_by(api_type='onecard', is_active=True).first()
        if not api_settings:
            return jsonify({'success': False, 'message': 'خدمة OneCard غير متاحة حالياً'})
        
        # إنشاء طلب جديد
        from utils import generate_order_number
        order_number = generate_order_number()
        
        # حساب السعر الإجمالي
        unit_price = float(api_product.price) if api_product else 0
        total_amount = unit_price * quantity
        
        order = Order(
            user_id=current_user.id,
            order_number=order_number,
            total_amount=total_amount,
            currency='SAR',
            order_status='processing',
            payment_status='paid',  # افتراض الدفع المسبق
            payment_method='wallet',
            order_type='api_product'
        )
        
        db.session.add(order)
        db.session.flush()  # للحصول على order.id
        
        # معالجة شراء كل قطعة
        successful_transactions = []
        failed_transactions = []
        all_product_codes = []
        
        for i in range(quantity):
            try:
                # توليد رقم مرجعي فريد لكل معاملة
                from api_services import OnecardAPIService
                service = OnecardAPIService(api_settings)
                ref_number = service.generate_unique_ref_number()
                
                # إنشاء معاملة API
                transaction = APITransaction(
                    api_settings_id=api_settings.id,
                    order_id=order.id,
                    external_product_id=external_product_id,
                    reseller_ref_number=ref_number,
                    transaction_status='pending',
                    amount=unit_price,
                    currency='SAR'
                )
                db.session.add(transaction)
                db.session.flush()
                
                # شراء المنتج من OneCard API
                current_app.logger.info(f"Purchasing product {external_product_id} with ref {ref_number}")
                response = service.purchase_product(external_product_id, ref_number)
                
                # حفظ استجابة API
                transaction.purchase_response = json.dumps(response, ensure_ascii=False)
                
                if 'error' not in response:
                    # نجح الشراء - استخراج الأكواد
                    transaction.transaction_status = 'success'
                    product_codes = extract_product_codes_from_onecard_response(response)
                    
                    if product_codes:
                        transaction.product_codes = json.dumps(product_codes, ensure_ascii=False)
                        all_product_codes.extend(product_codes)
                        successful_transactions.append(transaction)
                        current_app.logger.info(f"Successfully purchased product, got {len(product_codes)} codes")
                    else:
                        # نجح الشراء لكن بدون أكواد واضحة
                        transaction.product_codes = json.dumps(response, ensure_ascii=False)
                        successful_transactions.append(transaction)
                        current_app.logger.warning(f"Purchase successful but no clear codes found in response")
                else:
                    # فشل الشراء
                    transaction.transaction_status = 'failed'
                    failed_transactions.append({
                        'transaction': transaction,
                        'error': response.get('error', 'خطأ غير معروف')
                    })
                    current_app.logger.error(f"Purchase failed: {response.get('error')}")
                
            except Exception as e:
                current_app.logger.error(f"Error in purchase iteration {i+1}: {e}")
                transaction.transaction_status = 'failed'
                failed_transactions.append({
                    'transaction': transaction,
                    'error': str(e)
                })
        
        # تحديث حالة الطلب حسب النتائج
        if len(successful_transactions) == quantity:
            order.order_status = 'completed'
            order.payment_status = 'paid'
        elif len(successful_transactions) > 0:
            order.order_status = 'partially_completed'
        else:
            order.order_status = 'failed'
        
        db.session.commit()
        
        # إرسال البريد الإلكتروني والفاتورة للمشتريات الناجحة
        email_sent = False
        invoice_created = False
        
        if successful_transactions and all_product_codes:
            try:
                # إرسال أكواد المنتج بالبريد الإلكتروني
                email_sent = send_api_product_codes_email_enhanced(
                    order, successful_transactions, all_product_codes
                )
                
                # إنشاء فاتورة
                invoice_created = create_api_product_invoice(order, successful_transactions)
                
            except Exception as e:
                current_app.logger.error(f"Error in post-purchase processing: {e}")
        
        # إعداد الاستجابة
        if len(successful_transactions) == quantity:
            message = f'تم شراء المنتج بنجاح! تم إرسال {len(all_product_codes)} كود إلى بريدك الإلكتروني'
            success = True
        elif len(successful_transactions) > 0:
            message = f'تم شراء {len(successful_transactions)} من أصل {quantity} بنجاح'
            success = True
        else:
            message = 'فشل في شراء المنتج'
            success = False
        
        response_data = {
            'success': success,
            'order_id': order.id,
            'order_number': order.order_number,
            'successful_purchases': len(successful_transactions),
            'failed_purchases': len(failed_transactions),
            'total_codes': len(all_product_codes),
            'email_sent': email_sent,
            'invoice_created': invoice_created,
            'message': message
        }
        
        if failed_transactions:
            response_data['errors'] = [ft['error'] for ft in failed_transactions]
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API product purchase error: {e}")
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})


def extract_product_codes_from_onecard_response(response):
    """استخراج أكواد المنتج من استجابة OneCard API"""
    product_codes = []
    
    try:
        if isinstance(response, dict):
            # Pattern 1: مباشرة في codes
            if 'codes' in response and isinstance(response['codes'], list):
                product_codes = [str(code) for code in response['codes']]
            
            # Pattern 2: في serialNumbers
            elif 'serialNumbers' in response and isinstance(response['serialNumbers'], list):
                product_codes = [str(sn) for sn in response['serialNumbers']]
            
            # Pattern 3: كود واحد
            elif 'code' in response:
                product_codes = [str(response['code'])]
            elif 'serialNumber' in response:
                product_codes = [str(response['serialNumber'])]
            
            # Pattern 4: في cards array
            elif 'cards' in response and isinstance(response['cards'], list):
                for card in response['cards']:
                    if isinstance(card, dict):
                        if 'serialNumber' in card:
                            product_codes.append(str(card['serialNumber']))
                        elif 'code' in card:
                            product_codes.append(str(card['code']))
                        elif 'cardNumber' in card:
                            product_codes.append(str(card['cardNumber']))
            
            # Pattern 5: في result
            elif 'result' in response:
                result = response['result']
                if isinstance(result, list):
                    product_codes = [str(item) for item in result]
                elif isinstance(result, dict):
                    # استدعاء recursive للبحث في result
                    product_codes = extract_product_codes_from_onecard_response(result)
                elif isinstance(result, str):
                    product_codes = [str(result)]
            
            # Pattern 6: في data
            elif 'data' in response:
                data = response['data']
                if isinstance(data, list):
                    product_codes = [str(item) for item in data]
                elif isinstance(data, dict):
                    product_codes = extract_product_codes_from_onecard_response(data)
                elif isinstance(data, str):
                    product_codes = [str(data)]
            
            # Pattern 7: البحث في جميع القيم النصية الطويلة (possible codes)
            else:
                for key, value in response.items():
                    if isinstance(value, str) and len(value) > 5 and key.lower() in ['pin', 'password', 'activation', 'redemption']:
                        product_codes.append(str(value))
    
    except Exception as e:
        current_app.logger.error(f"Error extracting codes from OneCard response: {e}")
    
    # تنظيف الأكواد من المساحات والأحرف الزائدة
    cleaned_codes = []
    for code in product_codes:
        if code and isinstance(code, str):
            cleaned_code = code.strip()
            if len(cleaned_code) > 3:
                cleaned_codes.append(cleaned_code)
    
    return cleaned_codes


def send_api_product_codes_email_enhanced(order, transactions, product_codes):
    """إرسال أكواد منتج API بالبريد الإلكتروني مع دعم محسن"""
    try:
        from product_code_email_service import ProductCodeEmailService
        
        if not product_codes:
            current_app.logger.warning(f"No product codes to send for order {order.order_number}")
            return False
        
        # الحصول على معلومات المنتج من أول معاملة ناجحة
        first_transaction = transactions[0]
        product_name = f"منتج OneCard - {first_transaction.external_product_id}"
        
        # محاولة الحصول على اسم المنتج من استجابة API
        try:
            if first_transaction.purchase_response:
                response_data = json.loads(first_transaction.purchase_response)
                if isinstance(response_data, dict):
                    product_name = (response_data.get('productName') or 
                                  response_data.get('name') or 
                                  response_data.get('product_name') or 
                                  product_name)
        except:
            pass
        
        # تحضير بيانات الطلب للبريد الإلكتروني
        order_data = {
            'order_number': order.order_number,
            'customer_name': order.user.full_name or order.user.email.split('@')[0],
            'customer_email': order.user.email,
            'order_date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'product_name': product_name,
            'quantity': len(product_codes),
            'total_amount': float(order.total_amount),
            'currency': order.currency or 'SAR'
        }
        
        # إرسال البريد الإلكتروني
        email_service = ProductCodeEmailService()
        success, message, excel_file_path = email_service.send_product_codes_email(order_data, product_codes)
        
        if success and excel_file_path:
            # حفظ مسار ملف Excel في الطلب
            order.excel_file_path = excel_file_path.replace(os.getcwd() + os.sep, '').replace('\\', '/')
            db.session.commit()
            current_app.logger.info(f"Email sent successfully with Excel file: {excel_file_path}")
        elif success:
            current_app.logger.info(f"Email sent successfully for order {order.order_number}")
        else:
            current_app.logger.error(f"Failed to send email: {message}")
        
        return success
        
    except Exception as e:
        current_app.logger.error(f"Error sending API product codes email: {e}")
        return False


def create_api_product_invoice(order, transactions):
    """إنشاء فاتورة للمنتجات المشتراة من API"""
    try:
        from invoice_service import InvoiceService
        
        # إنشاء الفاتورة
        invoice = InvoiceService.create_invoice(order)
        
        if invoice:
            current_app.logger.info(f"Invoice #{invoice.invoice_number} created for order {order.order_number}")
            return True
        else:
            current_app.logger.error(f"Failed to create invoice for order {order.order_number}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error creating API product invoice: {e}")
        return False


@main.route('/api-product-details/<external_product_id>')
@login_required
def api_product_details(external_product_id):
    """جلب تفاصيل منتج من API"""
    try:
        # البحث عن المنتج في قاعدة البيانات المحلية أولاً
        api_product = APIProduct.query.filter_by(external_product_id=external_product_id).first()
        
        if api_product:
            # إرجاع البيانات المحلية
            return jsonify({
                'success': True,
                'product': {
                    'id': api_product.id,
                    'external_id': api_product.external_product_id,
                    'name': api_product.name,
                    'description': api_product.description,
                    'category': api_product.category,
                    'price': float(api_product.price or 0),
                    'currency': api_product.currency,
                    'stock_status': api_product.stock_status,
                    'provider': api_product.provider or 'onecard'
                },
                'source': 'local'
            })
        
        # إذا لم يوجد محلياً، جلب من API مباشرة
        api_settings = APISettings.query.filter_by(api_type='onecard', is_active=True).first()
        if not api_settings:
            return jsonify({'success': False, 'message': 'خدمة API غير متاحة'})
        
        from api_services import APIManager
        service = APIManager.get_api_service(api_settings)
        response = service.get_product_info(external_product_id)
        
        if 'error' in response:
            return jsonify({'success': False, 'message': f'خطأ في API: {response["error"]}'})
        
        # تنسيق البيانات المُرجعة من API
        product_data = {
            'external_id': external_product_id,
            'name': response.get('name') or response.get('productName', 'غير محدد'),
            'description': response.get('description') or response.get('productDescription', ''),
            'category': response.get('category') or response.get('categoryName', ''),
            'price': float(response.get('price') or response.get('sellingPrice', 0)),
            'currency': response.get('currency', 'SAR'),
            'stock_status': response.get('inStock', True),
            'provider': 'onecard'
        }
        
        return jsonify({
            'success': True,
            'product': product_data,
            'source': 'api'
        })
        
    except Exception as e:
        current_app.logger.error(f"API product details error: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ، يرجى المحاولة مرة أخرى'})


@main.route('/refresh-api-products', methods=['POST'])
def refresh_api_products():
    """تحديث المنتجات من API"""
    try:
        from api_services import APIManager
        
        # جلب إعدادات API النشطة
        api_settings = APISettings.query.filter_by(api_type='onecard', is_active=True).first()
        if not api_settings:
            return jsonify({'success': False, 'message': 'لا توجد إعدادات API نشطة'})
        
        service = APIManager.get_api_service(api_settings)
        response = service.get_products_list()
        
        if 'error' in response:
            return jsonify({'success': False, 'message': f'خطأ في API: {response["error"]}'})
        
        # معالجة البيانات وحفظ المنتجات الجديدة
        products_data = []
        if isinstance(response, dict):
            if 'products' in response:
                products_data = response['products']
            elif 'result' in response:
                products_data = response['result']
            elif 'data' in response:
                products_data = response['data']
        elif isinstance(response, list):
            products_data = response
        
        new_products_count = 0
        updated_products_count = 0
        
        for product_data in products_data[:20]:  # معالجة أول 20 منتج
            try:
                product_id = str(product_data.get('id') or product_data.get('productId') or product_data.get('ProductId', ''))
                if not product_id:
                    continue
                
                # البحث عن المنتج الموجود
                existing_product = APIProduct.query.filter_by(
                    external_product_id=product_id,
                    api_settings_id=api_settings.id
                ).first()
                
                if existing_product:
                    # تحديث المنتج الموجود
                    existing_product.name = product_data.get('name') or product_data.get('productName') or existing_product.name
                    existing_product.price = float(product_data.get('price') or product_data.get('sellingPrice', 0))
                    existing_product.stock_status = product_data.get('inStock', True)
                    existing_product.category = product_data.get('category') or product_data.get('categoryName', existing_product.category)
                    existing_product.updated_at = datetime.utcnow()
                    updated_products_count += 1
                else:
                    # إنشاء منتج جديد
                    new_product = APIProduct(
                        api_settings_id=api_settings.id,
                        external_product_id=product_id,
                        name=product_data.get('name') or product_data.get('productName') or f'منتج {product_id}',
                        description=product_data.get('description') or product_data.get('productDescription', ''),
                        price=float(product_data.get('price') or product_data.get('sellingPrice', 0)),
                        currency=product_data.get('currency', 'SAR'),
                        category=product_data.get('category') or product_data.get('categoryName', 'منتجات OneCard'),
                        provider='OneCard',
                        stock_status=product_data.get('inStock', True),
                        is_active=True,
                        raw_data=json.dumps(product_data, ensure_ascii=False)
                    )
                    db.session.add(new_product)
                    new_products_count += 1
                    
            except Exception as e:
                current_app.logger.warning(f"Error processing product {product_id}: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم التحديث بنجاح - منتجات جديدة: {new_products_count}, منتجات محدثة: {updated_products_count}',
            'new_products': new_products_count,
            'updated_products': updated_products_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Refresh API products error: {e}")
        return jsonify({'success': False, 'message': f'حدث خطأ في التحديث: {str(e)}'})



@main.route('/add-to-cart-old', methods=['POST'])
@login_required
def add_to_cart_old():
    """إضافة منتج إلى السلة - الطريقة القديمة"""
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
            
            # التحقق من صحة السعر
            if price is None or price == 0:
                price = product.regular_price if product.regular_price else 0
            
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'total': price * quantity
            })
            total += price * quantity
    
    # الحصول على رصيد المحفظة للمقارنة
    wallet_balance = 0.0
    current_currency = session.get('currency', 'USD')
    
    try:
        from wallet_utils import get_or_create_wallet, get_currency_rate
        wallet = get_or_create_wallet(current_user)
        
        # تحويل رصيد المحفظة للعملة الحالية
        if wallet.currency != current_currency:
            exchange_rate = get_currency_rate(wallet.currency, current_currency)
            wallet_balance = float(wallet.balance) * exchange_rate
        else:
            wallet_balance = float(wallet.balance)
            
    except Exception as e:
        print(f"خطأ في الحصول على رصيد المحفظة: {e}")
        wallet_balance = 0.0
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         total=float(total),
                         cart_total=float(total),
                         wallet_balance=float(wallet_balance),
                         current_currency=current_currency)

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
                price=price,
                currency=order.currency
            )
            db.session.add(order_item)
            total_amount += price * quantity
    
    order.total_amount = total_amount
    db.session.commit()
    
    # مسح السلة
    session.pop('cart', None)
    
    return jsonify({'success': True, 'order_id': order.id, 'redirect': url_for('main.checkout_payment', order_id=order.id)})

@main.route('/checkout/payment/<int:order_id>')
@login_required
def checkout_payment(order_id):
    """صفحة الدفع الجديدة مع دعم المحفظة والبطاقة البنكية"""
    from wallet_utils import get_user_wallet_balance, get_or_create_wallet
    
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return redirect(url_for('main.index'))
    
    # التحقق من أن الطلب لم يتم دفعه بعد
    if order.payment_status == 'completed':
        flash('تم دفع هذا الطلب بالفعل', 'info')
        return redirect(url_for('main.order_detail', order_id=order.id))
    
    # الحصول على رصيد المحفظة
    wallet_balance = get_user_wallet_balance(current_user.id, order.currency)
    
    # الحصول على تفاصيل المحفظة الكاملة للتحقق
    wallet = get_or_create_wallet(current_user)
    
    # طباعة تفاصيل المحفظة للتطوير والتتبع
    print(f"تفاصيل المحفظة للمستخدم {current_user.id}:")
    print(f"- رصيد المحفظة: {wallet.balance} {wallet.currency}")
    print(f"- رصيد محول لعملة الطلب: {wallet_balance} {order.currency}")
    print(f"- مبلغ الطلب: {order.total_amount} {order.currency}")
    print(f"- كافي للدفع: {'نعم' if wallet_balance >= float(order.total_amount) else 'لا'}")
    
    # الحصول على بوابات الدفع النشطة
    payment_gateways = PaymentGateway.query.filter_by(is_active=True).all()
    
    return render_template('checkout_payment.html', 
                         order=order, 
                         wallet_balance=float(wallet_balance),
                         wallet=wallet,  # إضافة تفاصيل المحفظة الكاملة
                         payment_gateways=payment_gateways)

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
    from api_services import APIManager
    from order_email_service import ProductCodeEmailService
    from wallet_utils import check_spending_limit, record_spending, get_user_wallet_balance, deduct_from_wallet
    from invoice_service import InvoiceService, ExcelReportService
    
    data = request.get_json()
    order_id = data.get('order_id')
    payment_method = data.get('payment_method')
    gateway = data.get('gateway')
    
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    # التحقق من أن الطلب لم يتم دفعه بعد
    if order.payment_status == 'completed':
        return jsonify({'success': False, 'message': 'تم دفع هذا الطلب بالفعل'})
    
    # قائمة للتتبع العمليات المنجزة
    completed_operations = {
        'payment_processed': False,
        'products_purchased': False,
        'invoice_created': False,
        'email_sent': False,
        'spending_recorded': False
    }
    
    try:
        print(f"🔄 بدء معالجة الدفع للطلب #{order.order_number}")
        
        # تحديث طريقة الدفع
        order.payment_method = f"{payment_method}_{gateway}" if gateway else payment_method
        
        # معالجة الدفع حسب الطريقة المختارة
        payment_result = None
        if payment_method == 'wallet':
            # الدفع بالمحفظة
            payment_result = process_wallet_payment(order)
            if not payment_result['success']:
                return jsonify(payment_result)
        elif payment_method == 'card':
            # الدفع بالبطاقة البنكية
            payment_result = process_card_payment(order, gateway)
            if not payment_result['success']:
                return jsonify(payment_result)
        else:
            return jsonify({'success': False, 'message': 'طريقة دفع غير صحيحة'})
        
        completed_operations['payment_processed'] = True
        print(f"✅ تم إنجاز معالجة الدفع")
        
        # تحديث حالة الطلب
        order.payment_status = 'completed'
        order.order_status = 'completed'
        
        # شراء المنتجات وتوليد الأكواد
        purchased_codes = []
        api_manager = APIManager()
        
        for item in order.items:
            product = item.product
            
            # البحث عن المنتج في API
            api_product = APIProduct.query.filter_by(
                product_id=product.id,
                provider='onecard'
            ).first()
            
            if api_product:
                # شراء من OneCard API
                for i in range(item.quantity):
                    purchase_result = api_manager.purchase_onecard_product(
                        product_id=api_product.provider_product_id,
                        amount=item.price,
                        user=current_user,
                        order=order
                    )
                    
                    if purchase_result.get('success'):
                        purchased_codes.append({
                            'اسم المنتج': product.name,
                            'الكود': purchase_result.get('product_code'),
                            'الرقم التسلسلي': purchase_result.get('serial_number', ''),
                            'التعليمات': purchase_result.get('instructions', product.instructions or ''),
                            'السعر': float(item.price),
                            'العملة': order.currency
                        })
            else:
                # شراء من الأكواد المخزنة محلياً
                for i in range(item.quantity):
                    available_code = ProductCode.query.filter_by(
                        product_id=item.product_id,
                        is_used=False
                    ).first()
                    
                    if available_code:
                        available_code.is_used = True
                        available_code.used_at = datetime.utcnow()
                        available_code.order_id = order.id
                        
                        purchased_codes.append({
                            'اسم المنتج': product.name,
                            'الكود': available_code.code,
                            'الرقم التسلسلي': available_code.serial_number or '',
                            'التعليمات': product.instructions or '',
                            'السعر': float(item.price),
                            'العملة': order.currency
                        })
        
        completed_operations['products_purchased'] = True
        print(f"✅ تم إنجاز شراء المنتجات وتوليد {len(purchased_codes)} كود")
        
        # حفظ التغييرات قبل إنشاء الفاتورة
        db.session.commit()
        
        # إنشاء الفاتورة
        try:
            invoice = InvoiceService.create_invoice(order)
            completed_operations['invoice_created'] = True
            print(f"✅ تم إنجاز إنشاء الفاتورة #{invoice.invoice_number}")
        except Exception as e:
            print(f"❌ خطأ في إنشاء الفاتورة: {e}")
            invoice = None
        
        # إرسال البريد الإلكتروني مع ملف Excel
        try:
            from order_email_service import email_service
            
            # تحضير بيانات الطلب للبريد الإلكتروني
            order_data = {
                'order_number': order.order_number,
                'customer_name': current_user.full_name or current_user.username,
                'customer_email': current_user.email,
                'order_date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'product_name': 'منتجات رقمية متنوعة',
                'quantity': sum(item.quantity for item in order.items),
                'total_amount': float(order.total_amount),
                'currency': order.currency
            }
            
            # البحث عن أكواد متاحة للمنتجات المشتراة
            available_codes = []
            products_without_codes = []
            
            for item in order.items:
                # البحث عن أكواد متاحة لهذا المنتج
                available_product_codes = ProductCode.query.filter_by(
                    product_id=item.product_id,
                    is_used=False,
                    order_id=None
                ).limit(item.quantity).all()
                
                if len(available_product_codes) >= item.quantity:
                    # توجد أكواد كافية، تخصيصها للطلب
                    for code in available_product_codes:
                        code.order_id = order.id
                        code.used_at = datetime.utcnow()
                        available_codes.append(code)
                else:
                    # لا توجد أكواد كافية
                    products_without_codes.append({
                        'product': item.product,
                        'quantity': item.quantity,
                        'available_codes': len(available_product_codes)
                    })
            
            # حفظ التغييرات
            db.session.commit()
            
            # إرسال إيميل تأكيد الطلب دائماً
            if available_codes and not products_without_codes:
                # توجد جميع الأكواد المطلوبة - إرسال مع الأكواد
                product_codes = [code.code for code in available_codes]
                success, message, excel_file_path = email_service.send_product_codes_email(order_data, product_codes)
                
                if success and excel_file_path:
                    order.excel_file_path = excel_file_path
                    order.order_status = 'completed'  # الطلب مكتمل
                    db.session.commit()
                    completed_operations['email_sent'] = True
                    print(f"✅ تم إنجاز إرسال البريد الإلكتروني مع الأكواد وحفظ ملف Excel: {excel_file_path}")
                else:
                    print(f"❌ خطأ في إرسال البريد: {message}")
            else:
                # إرسال إيميل تأكيد الطلب بدون أكواد
                success, message = send_order_confirmation_without_codes(order_data, available_codes, products_without_codes)
                
                if success:
                    completed_operations['email_sent'] = True
                    print(f"✅ تم إرسال إيميل تأكيد الطلب بنجاح")
                else:
                    print(f"❌ خطأ في إرسال إيميل التأكيد: {message}")
                
                if available_codes and products_without_codes:
                    # توجد أكواد جزئية
                    order.order_status = 'partial_codes'  # حالة جديدة للأكواد الجزئية
                    db.session.commit()
                    print(f"⚠️ تم تخصيص {len(available_codes)} كود، ولكن يحتاج {len(products_without_codes)} منتج لأكواد إضافية")
                else:
                    # لا توجد أكواد متاحة
                    order.order_status = 'pending_codes'  # الطلب في انتظار الأكواد
                    db.session.commit()
                    print("⚠️ الطلب في انتظار إضافة الأكواد من الإدارة")
                
                # إرسال إشعار للإدارة (اختياري)
                try:
                    from send_by_hostinger import send_custom_email
                    send_custom_email(
                        email="admin@es-gift.com",  # البريد الإداري
                        subject=f"طلب جديد يحتاج أكواد - #{order.order_number}",
                        message_content=f"الطلب #{order.order_number} للعميل {current_user.email} يحتاج إضافة أكواد للمنتجات",
                        message_title="إشعار إداري"
                    )
                except:
                    pass
                
        except Exception as e:
            print(f"❌ خطأ في إرسال البريد الإلكتروني: {e}")
        
        # تسجيل عملية الإنفاق في نظام الحدود
        try:
            from wallet_utils import get_currency_rate
            order_amount_usd = get_currency_rate(order.currency, 'USD') * float(order.total_amount)
            record_spending(
                user_id=current_user.id,
                amount_usd=order_amount_usd,
                transaction_type='purchase',
                description=f"شراء طلب #{order.order_number}",
                reference_id=order.id,
                reference_type='order',
                currency_code=order.currency,
                exchange_rate=get_currency_rate('USD', order.currency)
            )
            completed_operations['spending_recorded'] = True
            print(f"✅ تم إنجاز تسجيل عملية الإنفاق")
        except Exception as e:
            print(f"❌ خطأ في تسجيل الإنفاق: {e}")
        
        # التحقق من إتمام العمليات الأساسية
        essential_operations = ['payment_processed', 'products_purchased']
        all_essential_completed = all(completed_operations[op] for op in essential_operations)
        
        if not all_essential_completed:
            # إذا فشلت العمليات الأساسية، التراجع عن الدفع
            db.session.rollback()
            return jsonify({
                'success': False, 
                'message': 'فشل في إتمام العمليات الأساسية',
                'operations_status': completed_operations
            })
        
        print(f"🎉 تم إتمام الطلب بنجاح!")
        print(f"📊 حالة العمليات: {completed_operations}")
        
        return jsonify({
            'success': True,
            'message': 'تم إتمام الدفع وإرسال الأكواد بنجاح',
            'redirect': url_for('main.order_success', order_id=order.id),
            'invoice_id': invoice.id if invoice else None,
            'operations_completed': completed_operations,
            'codes_generated': len(purchased_codes)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ عام في معالجة الدفع: {e}")
        return jsonify({
            'success': False, 
            'message': f'حدث خطأ في معالجة الدفع: {str(e)}',
            'operations_status': completed_operations
        })


def process_wallet_payment(order):
    """معالجة الدفع بالمحفظة"""
    from wallet_utils import get_user_wallet_balance, deduct_from_wallet, check_spending_limit, get_or_create_wallet
    
    try:
        # الحصول على تفاصيل المحفظة الكاملة
        user = User.query.get(order.user_id)
        wallet = get_or_create_wallet(user)
        
        print(f"معالجة دفع المحفظة:")
        print(f"- مبلغ الطلب: {order.total_amount} {order.currency}")
        print(f"- رصيد المحفظة: {wallet.balance} {wallet.currency}")
        
        # تحويل مبلغ الطلب إلى عملة المحفظة للمقارنة
        from wallet_utils import get_currency_rate
        if order.currency != wallet.currency:
            exchange_rate = get_currency_rate(order.currency, wallet.currency)
            amount_needed_in_wallet_currency = float(order.total_amount) * exchange_rate
            print(f"- المبلغ المطلوب بعملة المحفظة: {amount_needed_in_wallet_currency:.2f} {wallet.currency}")
        else:
            amount_needed_in_wallet_currency = float(order.total_amount)
        
        # التحقق من كفاية الرصيد
        if float(wallet.balance) < amount_needed_in_wallet_currency:
            deficit = amount_needed_in_wallet_currency - float(wallet.balance)
            return {
                'success': False, 
                'message': f'💳 رصيد المحفظة غير كافٍ لإتمام هذا الطلب\n\n'
                          f'📊 تفاصيل العملية:\n'
                          f'• الرصيد المتاح: {wallet.balance:.2f} {wallet.currency}\n'
                          f'• المبلغ المطلوب: {amount_needed_in_wallet_currency:.2f} {wallet.currency}\n'
                          f'• المبلغ الناقص: {deficit:.2f} {wallet.currency}\n\n'
                          f'💡 يمكنك إيداع المبلغ الناقص من خلال الذهاب إلى صفحة المحفظة',
                'error_type': 'insufficient_balance',
                'balance_info': {
                    'current_balance': float(wallet.balance),
                    'required_amount': amount_needed_in_wallet_currency,
                    'deficit': deficit,
                    'currency': wallet.currency
                }
            }
        
        # التحقق من حدود الإنفاق
        order_amount_usd = get_currency_rate(order.currency, 'USD') * float(order.total_amount)
        can_spend, message = check_spending_limit(order.user_id, order_amount_usd)
        if not can_spend:
            return {'success': False, 'message': message}
        
        # خصم المبلغ من المحفظة
        deduction_result = deduct_from_wallet(
            user_id=order.user_id,
            amount=float(order.total_amount),
            currency_code=order.currency,
            description=f"شراء طلب #{order.order_number}",
            order_id=order.id
        )
        
        if not deduction_result['success']:
            return {'success': False, 'message': deduction_result['message']}
        
        print(f"✅ تم خصم المبلغ من المحفظة بنجاح")
        return {'success': True, 'message': 'تم خصم المبلغ من المحفظة بنجاح', 'deduction_details': deduction_result}
        
    except Exception as e:
        print(f"خطأ في معالجة الدفع بالمحفظة: {e}")
        return {'success': False, 'message': 'حدث خطأ في معالجة الدفع بالمحفظة'}


def process_card_payment(order, gateway):
    """معالجة الدفع بالبطاقة البنكية"""
    try:
        # هنا يمكن إضافة التكامل مع بوابات الدفع الحقيقية
        # مثل Moyasar, PayTabs, Hyperpay وغيرها
        
        # للمحاكاة، سنفترض أن الدفع نجح
        # في التطبيق الحقيقي، ستحتاج لاستدعاء API بوابة الدفع
        
        payment_gateway = PaymentGateway.query.filter_by(name=gateway, is_active=True).first()
        if not payment_gateway:
            return {'success': False, 'message': 'بوابة الدفع غير متاحة'}
        
        # محاكاة نجاح الدفع
        # في الواقع، هنا ستقوم بإرسال طلب إلى بوابة الدفع
        payment_success = True  # نتيجة من بوابة الدفع
        
        if payment_success:
            return {'success': True, 'message': 'تم الدفع بالبطاقة البنكية بنجاح'}
        else:
            return {'success': False, 'message': 'فشل في الدفع بالبطاقة البنكية'}
            
    except Exception as e:
        print(f"خطأ في معالجة الدفع بالبطاقة: {e}")
        return {'success': False, 'message': 'حدث خطأ في معالجة الدفع بالبطاقة'}


@main.route('/order/success/<int:order_id>')
@login_required
def order_success(order_id):
    """صفحة نجاح الطلب"""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return redirect(url_for('main.index'))
    
    invoice = Invoice.query.filter_by(order_id=order.id).first()
    
    return render_template('order_success.html', order=order, invoice=invoice)

@main.route('/set-currency/<currency>')
def set_currency(currency):
    """تحديد العملة المختارة"""
    from models import Currency
    
    # التحقق من وجود العملة وكونها نشطة
    currency_obj = Currency.query.filter_by(code=currency, is_active=True).first()
    if currency_obj:
        session['currency'] = currency
        # إضافة رسالة تأكيد محسنة
        flash(f'تم تغيير العملة إلى {currency_obj.name} ({currency_obj.symbol})', 'success')
        
        # إضافة لوج لتتبع تغيير العملة
        current_app.logger.info(f'Currency changed to {currency} by user {current_user.id if current_user.is_authenticated else "guest"}')
    else:
        flash('العملة المطلوبة غير متاحة', 'error')
        current_app.logger.warning(f'Attempted to set invalid currency: {currency}')
        
    return redirect(request.referrer or url_for('main.index'))

@main.route('/api/convert-currency', methods=['POST'])
def api_convert_currency():
    """API لتحويل العملة فورياً"""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        from_currency = data.get('from_currency', 'SAR')
        to_currency = data.get('to_currency', 'SAR')
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'مبلغ غير صالح'})
        
        converted_amount = convert_currency(amount, from_currency, to_currency)
        
        return jsonify({
            'success': True,
            'converted_amount': float(converted_amount),
            'from_currency': from_currency,
            'to_currency': to_currency,
            'original_amount': amount
        })
        
    except Exception as e:
        current_app.logger.error(f'Currency conversion error: {str(e)}')
        return jsonify({'success': False, 'message': 'حدث خطأ في التحويل'})

@main.route('/currency-status')
def currency_status():
    """صفحة عرض حالة العملات للمستخدمين"""
    from models import Currency
    
    # جلب جميع العملات مرتبة حسب الكود
    currencies = Currency.query.order_by(Currency.code).all()
    
    return render_template('currency_status.html', 
                         currencies=currencies,
                         page_title='حالة العملات')

@main.route('/api/get-exchange-rates')
def api_get_exchange_rates():
    """API للحصول على أسعار الصرف الحالية"""
    try:
        from models import Currency
        currencies = Currency.query.filter_by(is_active=True).all()
        
        rates = {}
        for currency in currencies:
            rates[currency.code] = {
                'name': currency.name,
                'symbol': currency.symbol,
                'rate': float(currency.exchange_rate),
                'is_active': currency.is_active
            }
        
        return jsonify({
            'success': True,
            'rates': rates,
            'base_currency': 'SAR'
        })
        
    except Exception as e:
        current_app.logger.error(f'Exchange rates API error: {str(e)}')
        return jsonify({'success': False, 'message': 'حدث خطأ في جلب أسعار الصرف'})

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
    # فلترة بناءً على category_id أولاً، ثم category name كـ fallback
    products_query = get_visible_products(current_user if current_user.is_authenticated else None)
    
    # فلترة المنتجات بناءً على القسم الرئيسي
    products = products_query.filter(
        (Product.category_id == category_id) |  # النظام الجديد
        (Product.category == category.name) |   # النظام القديم
        (Product.category == category.name_en)  # الاسم الإنجليزي
    ).all()
    
    # تحويل الأسعار
    user_currency = session.get('currency', 'SAR')
    for product in products:
        if current_user.is_authenticated:
            price = get_user_price(product, current_user.customer_type, current_user)
        else:
            price = product.regular_price
        
        # التحقق من صحة السعر
        if price is None or price == 0:
            price = product.regular_price if product.regular_price else 0
        
        product.original_price_sar = price
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
    products_query = get_visible_products(current_user if current_user.is_authenticated else None)
    
    # فلترة المنتجات بناءً على القسم الفرعي
    products = products_query.filter(Product.subcategory_id == subcategory_id).all()
    
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

# مسارات الصفحات الثابتة
@main.route('/page/<string:slug>')
def static_page(slug):
    """عرض صفحة ثابتة حسب الـ slug"""
    page = StaticPage.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template('static_page.html', page=page)

@main.route('/privacy-policy')
def privacy_policy():
    """صفحة سياسة الخصوصية"""
    page = StaticPage.query.filter_by(slug='privacy-policy', is_active=True).first()
    if page:
        return render_template('static_page.html', page=page)
    return redirect(url_for('main.index'))

@main.route('/contact-us')
def contact_us():
    """صفحة اتصل بنا"""
    page = StaticPage.query.filter_by(slug='contact-us', is_active=True).first()
    if page:
        return render_template('static_page.html', page=page)
    return redirect(url_for('main.index'))

@main.route('/about-us')
def about_us():
    """صفحة من نحن"""
    page = StaticPage.query.filter_by(slug='about-us', is_active=True).first()
    if page:
        return render_template('static_page.html', page=page)
    return redirect(url_for('main.index'))

@main.route('/terms-of-service')
def terms_of_service():
    """صفحة الشروط والأحكام"""
    page = StaticPage.query.filter_by(slug='terms-of-service', is_active=True).first()
    if page:
        return render_template('static_page.html', page=page)
    return redirect(url_for('main.index'))

# مسارات المقالات
@main.route('/articles')
def all_articles():
    """عرض جميع المقالات المنشورة"""
    page = request.args.get('page', 1, type=int)
    per_page = 12  # عدد المقالات في كل صفحة
    
    articles = Article.query.filter_by(is_published=True)\
                           .order_by(Article.created_at.desc())\
                           .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('articles.html', articles=articles)

@main.route('/article/<int:article_id>')
@main.route('/article/<int:article_id>/<slug>')
def article_detail(article_id, slug=None):
    """عرض تفاصيل مقال واحد"""
    article = Article.query.filter_by(id=article_id, is_published=True).first_or_404()
    
    # المقالات المشابهة (آخر 3 مقالات غير المقال الحالي)
    related_articles = Article.query.filter_by(is_published=True)\
                                   .filter(Article.id != article_id)\
                                   .order_by(Article.created_at.desc())\
                                   .limit(3).all()
    
    return render_template('article_detail.html', article=article, related_articles=related_articles)

@main.route('/download/invoice/<int:invoice_id>')
@login_required
def download_invoice(invoice_id):
    """تحميل ملف PDF للفاتورة"""
    try:
        # الحصول على الفاتورة
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # التحقق من صلاحية المستخدم
        if not current_user.is_admin and invoice.user_id != current_user.id:
            flash('غير مصرح لك بتحميل هذه الفاتورة', 'error')
            return redirect(url_for('main.index'))
        
        # التحقق من وجود ملف PDF
        if not invoice.pdf_file_path:
            # إنشاء الفاتورة إذا لم تكن موجودة
            from modern_invoice_service import ModernInvoiceService
            pdf_path = ModernInvoiceService.generate_modern_pdf(invoice)
            if pdf_path:
                invoice.pdf_file_path = pdf_path
                db.session.commit()
            else:
                flash('فشل في إنشاء ملف الفاتورة', 'error')
                return redirect(url_for('main.index'))
        
        # مسار ملف PDF
        pdf_full_path = os.path.join(current_app.static_folder, invoice.pdf_file_path)
        
        if not os.path.exists(pdf_full_path):
            # إعادة إنشاء الملف إذا لم يكن موجوداً
            from modern_invoice_service import ModernInvoiceService
            pdf_path = ModernInvoiceService.generate_modern_pdf(invoice)
            if pdf_path:
                invoice.pdf_file_path = pdf_path
                db.session.commit()
                pdf_full_path = os.path.join(current_app.static_folder, invoice.pdf_file_path)
            else:
                flash('ملف الفاتورة غير موجود', 'error')
                return redirect(url_for('main.index'))
        
        # تحميل الملف
        return send_file(
            pdf_full_path,
            as_attachment=True,
            download_name=f"ES-GIFT_Invoice_{invoice.invoice_number}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"خطأ في تحميل الفاتورة: {e}")
        flash('حدث خطأ في تحميل الفاتورة', 'error')
        return redirect(url_for('main.index'))
