#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف لإضافة بيانات اختبار شاملة لجميع جداول النظام
"""

from flask import Flask
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import random
import string
import uuid

from config import Config
from models import (
    db, User, Product, ProductCode, Order, OrderItem, 
    PaymentGateway, Currency, Article, APISettings,
    MainOffer, QuickCategory, GiftCardSection, OtherBrand,
    Category, Subcategory
)

def create_app():
    """إنشاء التطبيق للاختبار"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def generate_random_string(length=10):
    """إنشاء نص عشوائي"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_order_number():
    """إنشاء رقم طلب فريد"""
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{generate_random_string(6).upper()}"

def populate_users():
    """إضافة مستخدمين تجريبيين"""
    print("إضافة المستخدمين...")
    
    users_data = [
        # المدير الرئيسي
        {
            'email': 'admin@es-gift.com',
            'password_hash': generate_password_hash('admin123'),
            'full_name': 'المدير العام',
            'phone': '+966501234567',
            'birth_date': date(1990, 1, 15),
            'nationality': 'السعودية',
            'customer_type': 'admin',
            'kyc_status': 'approved',
            'is_admin': True,
            'last_login': datetime.utcnow() - timedelta(hours=2)
        },
        # عملاء عاديين
        {
            'email': 'ahmed.mohammed@gmail.com',
            'password_hash': generate_password_hash('password123'),
            'full_name': 'أحمد محمد السعودي',
            'phone': '+966501234568',
            'birth_date': date(1995, 3, 20),
            'nationality': 'السعودية',
            'customer_type': 'regular',
            'kyc_status': 'none',
            'is_admin': False,
            'last_login': datetime.utcnow() - timedelta(hours=5)
        },
        {
            'email': 'fatima.ali@gmail.com',
            'password_hash': generate_password_hash('password123'),
            'full_name': 'فاطمة علي الأحمد',
            'phone': '+966501234569',
            'birth_date': date(1992, 7, 10),
            'nationality': 'السعودية',
            'customer_type': 'kyc',
            'kyc_status': 'approved',
            'is_admin': False,
            'last_login': datetime.utcnow() - timedelta(hours=1)
        },
        {
            'email': 'omar.hassan@gmail.com',
            'password_hash': generate_password_hash('password123'),
            'full_name': 'عمر حسن المطيري',
            'phone': '+966501234570',
            'birth_date': date(1988, 12, 5),
            'nationality': 'السعودية',
            'customer_type': 'reseller',
            'kyc_status': 'approved',
            'is_admin': False,
            'last_login': datetime.utcnow() - timedelta(hours=3)
        },
        {
            'email': 'sara.khalid@gmail.com',
            'password_hash': generate_password_hash('password123'),
            'full_name': 'سارة خالد العتيبي',
            'phone': '+966501234571',
            'birth_date': date(1997, 9, 25),
            'nationality': 'السعودية',
            'customer_type': 'regular',
            'kyc_status': 'pending',
            'is_admin': False,
            'last_login': datetime.utcnow() - timedelta(minutes=30)
        },
        {
            'email': 'mohammed.abdullah@gmail.com',
            'password_hash': generate_password_hash('password123'),
            'full_name': 'محمد عبدالله القحطاني',
            'phone': '+966501234572',
            'birth_date': date(1993, 4, 18),
            'nationality': 'السعودية',
            'customer_type': 'kyc',
            'kyc_status': 'rejected',
            'is_admin': False,
            'last_login': datetime.utcnow() - timedelta(days=2)
        }
    ]
    
    added_count = 0
    for user_data in users_data:
        # التحقق من وجود المستخدم
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if not existing_user:
            user = User(**user_data)
            db.session.add(user)
            added_count += 1
        else:
            # تحديث البيانات إذا كان المستخدم موجود
            for key, value in user_data.items():
                if key != 'password_hash':  # لا نحدث كلمة المرور إذا كان المستخدم موجود
                    setattr(existing_user, key, value)
    
    db.session.commit()
    print(f"تم إضافة/تحديث {added_count} مستخدم")

def populate_currencies():
    """إضافة العملات"""
    print("إضافة العملات...")
    
    currencies_data = [
        {'code': 'SAR', 'name': 'الريال السعودي', 'symbol': 'ر.س', 'exchange_rate': 1.0, 'is_active': True},
        {'code': 'USD', 'name': 'الدولار الأمريكي', 'symbol': '$', 'exchange_rate': 3.75, 'is_active': True},
        {'code': 'EUR', 'name': 'اليورو', 'symbol': '€', 'exchange_rate': 4.10, 'is_active': True},
        {'code': 'AED', 'name': 'الدرهم الإماراتي', 'symbol': 'د.إ', 'exchange_rate': 1.02, 'is_active': True},
        {'code': 'EGP', 'name': 'الجنيه المصري', 'symbol': 'ج.م', 'exchange_rate': 0.12, 'is_active': True},
        {'code': 'GBP', 'name': 'الجنيه الإسترليني', 'symbol': '£', 'exchange_rate': 4.68, 'is_active': False}
    ]
    
    added_count = 0
    for currency_data in currencies_data:
        # التحقق من وجود العملة
        existing_currency = Currency.query.filter_by(code=currency_data['code']).first()
        if not existing_currency:
            currency = Currency(**currency_data)
            db.session.add(currency)
            added_count += 1
        else:
            # تحديث البيانات إذا كانت موجودة
            for key, value in currency_data.items():
                setattr(existing_currency, key, value)
    
    db.session.commit()
    print(f"تم إضافة/تحديث {added_count} عملة")

def populate_payment_gateways():
    """إضافة بوابات الدفع"""
    print("إضافة بوابات الدفع...")
    
    gateways_data = [
        {'name': 'فيزا/ماستركارد', 'fee_percentage': 2.9, 'is_active': True, 'api_key': 'visa_test_key', 'secret_key': 'visa_secret'},
        {'name': 'مدى', 'fee_percentage': 1.5, 'is_active': True, 'api_key': 'mada_test_key', 'secret_key': 'mada_secret'},
        {'name': 'أبل باي', 'fee_percentage': 2.5, 'is_active': True, 'api_key': 'apple_test_key', 'secret_key': 'apple_secret'},
        {'name': 'التحويل البنكي', 'fee_percentage': 0.0, 'is_active': True},
        {'name': 'STC Pay', 'fee_percentage': 2.0, 'is_active': True, 'api_key': 'stc_test_key', 'secret_key': 'stc_secret'},
        {'name': 'PayPal', 'fee_percentage': 3.4, 'is_active': False, 'api_key': 'paypal_test_key', 'secret_key': 'paypal_secret'}
    ]
    
    added_count = 0
    for gateway_data in gateways_data:
        # التحقق من وجود بوابة الدفع
        existing_gateway = PaymentGateway.query.filter_by(name=gateway_data['name']).first()
        if not existing_gateway:
            gateway = PaymentGateway(**gateway_data)
            db.session.add(gateway)
            added_count += 1
        else:
            # تحديث البيانات إذا كانت موجودة
            for key, value in gateway_data.items():
                setattr(existing_gateway, key, value)
    
    db.session.commit()
    print(f"تم إضافة/تحديث {added_count} بوابة دفع")

def populate_categories():
    """إضافة الأقسام الرئيسية والفرعية"""
    print("إضافة الأقسام...")
    
    categories_data = [
        {
            'name': 'ألعاب الفيديو',
            'name_en': 'Gaming',
            'description': 'بطاقات شحن الألعاب وبطاقات اللعب الجماعي',
            'icon_class': 'fas fa-gamepad',
            'image_url': '/static/images/gaming-category.jpg',
            'is_active': True,
            'display_order': 1,
            'subcategories': [
                {'name': 'PlayStation', 'name_en': 'PlayStation', 'description': 'بطاقات PlayStation Store', 'icon_class': 'fab fa-playstation'},
                {'name': 'Xbox', 'name_en': 'Xbox', 'description': 'بطاقات Xbox Live', 'icon_class': 'fab fa-xbox'},
                {'name': 'Steam', 'name_en': 'Steam', 'description': 'بطاقات Steam Wallet', 'icon_class': 'fab fa-steam'},
                {'name': 'Nintendo', 'name_en': 'Nintendo', 'description': 'بطاقات Nintendo eShop', 'icon_class': 'fas fa-gamepad'}
            ]
        },
        {
            'name': 'التطبيقات والجوال',
            'name_en': 'Mobile Apps',
            'description': 'بطاقات شحن التطبيقات والألعاب الجوالة',
            'icon_class': 'fas fa-mobile-alt',
            'image_url': '/static/images/mobile-category.jpg',
            'is_active': True,
            'display_order': 2,
            'subcategories': [
                {'name': 'Google Play', 'name_en': 'Google Play', 'description': 'بطاقات Google Play Store', 'icon_class': 'fab fa-google-play'},
                {'name': 'App Store', 'name_en': 'App Store', 'description': 'بطاقات Apple App Store', 'icon_class': 'fab fa-apple'},
                {'name': 'PUBG Mobile', 'name_en': 'PUBG Mobile', 'description': 'شحن UC لـ PUBG Mobile', 'icon_class': 'fas fa-crosshairs'},
                {'name': 'Free Fire', 'name_en': 'Free Fire', 'description': 'شحن الماس لـ Free Fire', 'icon_class': 'fas fa-fire'}
            ]
        },
        {
            'name': 'التسوق والترفيه',
            'name_en': 'Shopping & Entertainment',
            'description': 'بطاقات التسوق الإلكتروني والترفيه',
            'icon_class': 'fas fa-shopping-cart',
            'image_url': '/static/images/shopping-category.jpg',
            'is_active': True,
            'display_order': 3,
            'subcategories': [
                {'name': 'أمازون', 'name_en': 'Amazon', 'description': 'بطاقات هدايا أمازون', 'icon_class': 'fab fa-amazon'},
                {'name': 'نون', 'name_en': 'Noon', 'description': 'بطاقات هدايا نون', 'icon_class': 'fas fa-shopping-bag'},
                {'name': 'نتفليكس', 'name_en': 'Netflix', 'description': 'اشتراكات نتفليكس', 'icon_class': 'fas fa-film'},
                {'name': 'سبوتيفاي', 'name_en': 'Spotify', 'description': 'اشتراكات سبوتيفاي', 'icon_class': 'fab fa-spotify'}
            ]
        }
    ]
    
    added_categories = 0
    for cat_data in categories_data:
        subcats_data = cat_data.pop('subcategories', [])
        
        # التحقق من وجود القسم الرئيسي
        existing_category = Category.query.filter_by(name=cat_data['name']).first()
        if not existing_category:
            category = Category(**cat_data)
            db.session.add(category)
            db.session.flush()  # للحصول على ID
            added_categories += 1
        else:
            category = existing_category
            # تحديث البيانات
            for key, value in cat_data.items():
                setattr(category, key, value)
            db.session.flush()
        
        # إضافة/تحديث الأقسام الفرعية
        for subcat_data in subcats_data:
            existing_subcat = Subcategory.query.filter_by(
                name=subcat_data['name'], 
                category_id=category.id
            ).first()
            
            if not existing_subcat:
                subcat_data['category_id'] = category.id
                subcat_data['is_active'] = True
                subcat_data['display_order'] = subcats_data.index(subcat_data) + 1
                subcategory = Subcategory(**subcat_data)
                db.session.add(subcategory)
            else:
                # تحديث القسم الفرعي
                for key, value in subcat_data.items():
                    setattr(existing_subcat, key, value)
                existing_subcat.category_id = category.id
                existing_subcat.is_active = True
                existing_subcat.display_order = subcats_data.index(subcat_data) + 1
    
    db.session.commit()
    print(f"تم إضافة/تحديث {added_categories} أقسام رئيسية مع أقسامها الفرعية")

def populate_products():
    """إضافة المنتجات"""
    print("إضافة المنتجات...")
    
    products_data = [
        # منتجات الألعاب
        {
            'name': 'بطاقة PlayStation Store 50 ر.س',
            'description': 'بطاقة شحن PlayStation Store للحصول على الألعاب والمحتوى الإضافي، صالحة لجميع الحسابات السعودية',
            'category': 'gaming',
            'region': 'السعودية',
            'value': '50 ر.س',
            'regular_price': 50.00,
            'kyc_price': 47.50,
            'reseller_price': 45.00,
            'image_url': '/static/images/playstation-50.jpg',
            'instructions': 'ادخل إلى PlayStation Store واستخدم الكود في قسم استرداد الأكواد',
            'stock_quantity': 150
        },
        {
            'name': 'بطاقة PlayStation Store 100 ر.س',
            'description': 'بطاقة شحن PlayStation Store بقيمة 100 ريال سعودي',
            'category': 'gaming',
            'region': 'السعودية',
            'value': '100 ر.س',
            'regular_price': 100.00,
            'kyc_price': 95.00,
            'reseller_price': 90.00,
            'image_url': '/static/images/playstation-100.jpg',
            'instructions': 'ادخل إلى PlayStation Store واستخدم الكود في قسم استرداد الأكواد',
            'stock_quantity': 200
        },
        {
            'name': 'بطاقة Xbox Live Gold 25 دولار',
            'description': 'بطاقة هدية Xbox Live Gold للعب الألعاب الجماعية والحصول على العروض الشهرية',
            'category': 'gaming',
            'region': 'عالمي',
            'value': '25 دولار',
            'regular_price': 95.00,
            'kyc_price': 90.25,
            'reseller_price': 85.50,
            'image_url': '/static/images/xbox-25.jpg',
            'instructions': 'ادخل إلى Xbox وأدخل الكود في قسم استرداد الأكواد',
            'stock_quantity': 100
        },
        {
            'name': 'بطاقة Steam Wallet 20 دولار',
            'description': 'بطاقة شحن Steam لشراء الألعاب والمحتوى من متجر Steam العالمي',
            'category': 'gaming',
            'region': 'عالمي',
            'value': '20 دولار',
            'regular_price': 76.00,
            'kyc_price': 72.20,
            'reseller_price': 68.40,
            'image_url': '/static/images/steam-20.jpg',
            'instructions': 'ادخل إلى Steam وأضف الأموال إلى محفظتك باستخدام الكود',
            'stock_quantity': 180
        },
        # منتجات الجوال
        {
            'name': 'بطاقة Google Play 100 ر.س',
            'description': 'بطاقة هدية Google Play للحصول على التطبيقات والألعاب والمحتوى',
            'category': 'mobile',
            'region': 'السعودية',
            'value': '100 ر.س',
            'regular_price': 100.00,
            'kyc_price': 95.00,
            'reseller_price': 90.00,
            'image_url': '/static/images/google-play-100.jpg',
            'instructions': 'ادخل إلى Google Play وأدخل الكود في قسم استرداد الأكواد',
            'stock_quantity': 250
        },
        {
            'name': 'بطاقة iTunes 15 دولار',
            'description': 'بطاقة هدية iTunes للحصول على الموسيقى والأفلام والتطبيقات من App Store',
            'category': 'mobile',
            'region': 'الولايات المتحدة',
            'value': '15 دولار',
            'regular_price': 57.00,
            'kyc_price': 54.15,
            'reseller_price': 51.30,
            'image_url': '/static/images/itunes-15.jpg',
            'instructions': 'ادخل إلى App Store أو iTunes وأدخل الكود',
            'stock_quantity': 120
        },
        {
            'name': 'شحن PUBG Mobile 1800 UC',
            'description': 'بطاقة شحن PUBG Mobile للحصول على 1800 UC لشراء الأسلحة والملابس',
            'category': 'mobile',
            'region': 'عالمي',
            'value': '1800 UC',
            'regular_price': 85.00,
            'kyc_price': 80.75,
            'reseller_price': 76.50,
            'image_url': '/static/images/pubg-1800.jpg',
            'instructions': 'ادخل إلى PUBG Mobile وأدخل الكود في قسم الشحن',
            'stock_quantity': 300
        },
        {
            'name': 'شحن Free Fire 2200 ماسة',
            'description': 'بطاقة شحن Free Fire للحصول على 2200 ماسة لشراء الشخصيات والأسلحة',
            'category': 'mobile',
            'region': 'عالمي',
            'value': '2200 ماسة',
            'regular_price': 70.00,
            'kyc_price': 66.50,
            'reseller_price': 63.00,
            'image_url': '/static/images/freefire-2200.jpg',
            'instructions': 'ادخل إلى Free Fire وأدخل الكود في قسم الشحن',
            'stock_quantity': 280
        }
    ]
    
    added_count = 0
    for product_data in products_data:
        # التحقق من وجود المنتج
        existing_product = Product.query.filter_by(name=product_data['name']).first()
        if not existing_product:
            product_data['expiry_date'] = date.today() + timedelta(days=365)
            product_data['is_active'] = True
            product = Product(**product_data)
            db.session.add(product)
            added_count += 1
        else:
            # تحديث المنتج الموجود
            for key, value in product_data.items():
                setattr(existing_product, key, value)
            existing_product.expiry_date = date.today() + timedelta(days=365)
            existing_product.is_active = True
    
    db.session.commit()
    print(f"تم إضافة/تحديث {added_count} منتج")

def populate_product_codes():
    """إضافة أكواد المنتجات"""
    print("إضافة أكواد المنتجات...")
    
    products = Product.query.all()
    total_codes = 0
    
    for product in products:
        # التحقق من وجود أكواد للمنتج
        existing_codes_count = ProductCode.query.filter_by(product_id=product.id).count()
        
        if existing_codes_count < 50:  # إضافة أكواد إضافية إذا كانت قليلة
            codes_to_add = 100 - existing_codes_count
            for i in range(codes_to_add):
                # التأكد من عدم تكرار الكود
                while True:
                    new_code = f"{product.name[:3].upper()}-{generate_random_string(12).upper()}"
                    existing_code = ProductCode.query.filter_by(code=new_code).first()
                    if not existing_code:
                        break
                
                code = ProductCode(
                    product_id=product.id,
                    code=new_code,
                    is_used=random.choice([True, False]) if i < codes_to_add * 0.3 else False,
                    used_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)) if random.random() < 0.3 else None
                )
                db.session.add(code)
                total_codes += 1
    
    db.session.commit()
    print(f"تم إضافة {total_codes} كود منتج جديد")

def populate_orders():
    """إضافة الطلبات"""
    print("إضافة الطلبات...")
    
    users = User.query.filter_by(is_admin=False).all()
    products = Product.query.all()
    payment_methods = ['visa', 'mada', 'apple_pay', 'bank_transfer', 'stc_pay']
    order_statuses = ['pending', 'completed', 'cancelled', 'processing']
    payment_statuses = ['pending', 'completed', 'failed', 'refunded']
    
    orders_data = []
    for i in range(50):  # إنشاء 50 طلب
        user = random.choice(users)
        order_date = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        
        order = Order(
            user_id=user.id,
            order_number=generate_order_number(),
            total_amount=0,  # سيتم حسابه لاحقاً
            currency='SAR',
            payment_method=random.choice(payment_methods),
            payment_status=random.choice(payment_statuses),
            order_status=random.choice(order_statuses),
            created_at=order_date
        )
        
        db.session.add(order)
        db.session.flush()  # للحصول على ID
        
        # إضافة عناصر الطلب
        items_count = random.randint(1, 4)
        total_amount = 0
        
        for j in range(items_count):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            
            # تحديد السعر حسب نوع العميل
            if user.customer_type == 'reseller':
                price = product.reseller_price
            elif user.customer_type == 'kyc':
                price = product.kyc_price
            else:
                price = product.regular_price
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                price=price
            )
            
            db.session.add(order_item)
            total_amount += float(price) * quantity
        
        # تحديث إجمالي مبلغ الطلب
        order.total_amount = total_amount
        orders_data.append(order)
    
    db.session.commit()
    print(f"تم إضافة {len(orders_data)} طلب")

def populate_articles():
    """إضافة المقالات"""
    print("إضافة المقالات...")
    
    articles_data = [
        {
            'title': 'كيفية استخدام بطاقات PlayStation Store',
            'content': '''
            بطاقات PlayStation Store هي وسيلة آمنة ومريحة لشحن محفظتك الرقمية على PlayStation.
            
            خطوات الاستخدام:
            1. تسجيل الدخول إلى حساب PlayStation الخاص بك
            2. الدخول إلى PlayStation Store
            3. اختيار "استرداد الأكواد" من القائمة
            4. إدخال الكود المكون من 12 رقم
            5. تأكيد العملية
            
            ملاحظات مهمة:
            - تأكد من أن منطقة حسابك تتطابق مع منطقة البطاقة
            - الأكواد صالحة لمدة سنة من تاريخ الشراء
            - لا يمكن استرداد قيمة البطاقة نقداً
            ''',
            'image_url': '/static/images/playstation-guide.jpg',
            'author': 'فريق الدعم الفني',
            'is_published': True,
            'created_at': datetime.utcnow() - timedelta(days=15)
        },
        {
            'title': 'أفضل الألعاب المجانية على Steam',
            'content': '''
            يحتوي متجر Steam على مجموعة كبيرة من الألعاب المجانية عالية الجودة.
            
            قائمة بأفضل الألعاب:
            1. Dota 2 - لعبة استراتيجية جماعية
            2. Counter-Strike 2 - لعبة إطلاق نار تكتيكية
            3. Team Fortress 2 - لعبة إطلاق نار جماعية
            4. Warframe - لعبة حركة وقتال
            5. Path of Exile - لعبة أر بي جي
            
            نصائح للاعبين الجدد:
            - ابدأ بالألعاب البسيطة
            - اقرأ التقييمات قبل التحميل
            - استفد من العروض الموسمية
            ''',
            'image_url': '/static/images/steam-games.jpg',
            'author': 'خبير الألعاب',
            'is_published': True,
            'created_at': datetime.utcnow() - timedelta(days=8)
        },
        {
            'title': 'مقارنة بين بطاقات Google Play و App Store',
            'content': '''
            مقارنة شاملة بين متجري التطبيقات الرئيسيين.
            
            Google Play Store:
            - متوفر على أجهزة Android
            - أسعار متنوعة للبطاقات
            - يدعم العملات المحلية
            - مجموعة واسعة من التطبيقات
            
            Apple App Store:
            - متوفر على أجهزة iOS
            - جودة عالية للتطبيقات
            - نظام أمان متقدم
            - تحديثات منتظمة
            
            الخلاصة:
            كلا المتجرين يوفران تجربة ممتازة، والاختيار يعتمد على نوع جهازك.
            ''',
            'image_url': '/static/images/stores-comparison.jpg',
            'author': 'محلل التكنولوجيا',
            'is_published': False,
            'created_at': datetime.utcnow() - timedelta(days=3)
        }
    ]
    
    added_count = 0
    for article_data in articles_data:
        # التحقق من وجود المقال
        existing_article = Article.query.filter_by(title=article_data['title']).first()
        if not existing_article:
            article = Article(**article_data)
            db.session.add(article)
            added_count += 1
        else:
            # تحديث المقال الموجود
            for key, value in article_data.items():
                setattr(existing_article, key, value)
    
    db.session.commit()
    print(f"تم إضافة/تحديث {added_count} مقال")

def populate_api_settings():
    """إضافة إعدادات API"""
    print("إضافة إعدادات API...")
    
    api_settings_data = [
        {
            'api_name': 'Payment Gateway API',
            'api_url': 'https://api.payment-gateway.com/v1',
            'api_key': 'test_api_key_12345',
            'is_active': True,
            'settings_json': '{"timeout": 30, "retry_count": 3, "webhook_url": "https://es-gift.com/webhook"}'
        },
        {
            'api_name': 'SMS Service API',
            'api_url': 'https://api.sms-service.com/v2',
            'api_key': 'sms_api_key_67890',
            'is_active': True,
            'settings_json': '{"sender_name": "ES-Gift", "language": "ar", "unicode": true}'
        },
        {
            'api_name': 'Email Service API',
            'api_url': 'https://api.email-service.com/v1',
            'api_key': 'email_api_key_abcde',
            'is_active': False,
            'settings_json': '{"from_email": "noreply@es-gift.com", "template_id": "default"}'
        }
    ]
    
    added_count = 0
    for settings_data in api_settings_data:
        # التحقق من وجود الإعداد
        existing_settings = APISettings.query.filter_by(api_name=settings_data['api_name']).first()
        if not existing_settings:
            api_settings = APISettings(**settings_data)
            db.session.add(api_settings)
            added_count += 1
        else:
            # تحديث الإعدادات الموجودة
            for key, value in settings_data.items():
                setattr(existing_settings, key, value)
    
    db.session.commit()
    print(f"تم إضافة/تحديث {added_count} إعداد API")

def populate_homepage_content():
    """إضافة محتوى الصفحة الرئيسية"""
    print("إضافة محتوى الصفحة الرئيسية...")
    
    # العروض الرئيسية
    main_offers_data = [
        {
            'title': 'عرض خاص على بطاقات PlayStation',
            'image_url': '/static/images/offers/playstation-offer.jpg',
            'link_url': '/products?category=gaming&brand=playstation',
            'is_active': True,
            'display_order': 1
        },
        {
            'title': 'خصم 20% على جميع بطاقات Google Play',
            'image_url': '/static/images/offers/google-play-offer.jpg',
            'link_url': '/products?category=mobile&brand=google',
            'is_active': True,
            'display_order': 2
        },
        {
            'title': 'أحدث الألعاب بأفضل الأسعار',
            'image_url': '/static/images/offers/games-offer.jpg',
            'link_url': '/products?category=gaming',
            'is_active': True,
            'display_order': 3
        }
    ]
    
    # الفئات السريعة
    quick_categories_data = [
        {
            'name': 'ألعاب الفيديو',
            'icon_class': 'fas fa-gamepad',
            'link_url': '/products?category=gaming',
            'is_active': True,
            'display_order': 1
        },
        {
            'name': 'تطبيقات الجوال',
            'icon_class': 'fas fa-mobile-alt',
            'link_url': '/products?category=mobile',
            'is_active': True,
            'display_order': 2
        },
        {
            'name': 'التسوق الإلكتروني',
            'icon_class': 'fas fa-shopping-cart',
            'link_url': '/products?category=shopping',
            'is_active': True,
            'display_order': 3
        },
        {
            'name': 'الترفيه والإعلام',
            'icon_class': 'fas fa-film',
            'link_url': '/products?category=entertainment',
            'is_active': True,
            'display_order': 4
        }
    ]
    
    # بطاقات الهدايا
    gift_cards_data = [
        {
            'title': 'بطاقات PlayStation Store',
            'image_url': '/static/images/cards/playstation-card.jpg',
            'link_url': '/products?brand=playstation',
            'is_active': True,
            'display_order': 1
        },
        {
            'title': 'بطاقات Xbox Live',
            'image_url': '/static/images/cards/xbox-card.jpg',
            'link_url': '/products?brand=xbox',
            'is_active': True,
            'display_order': 2
        },
        {
            'title': 'بطاقات Steam',
            'image_url': '/static/images/cards/steam-card.jpg',
            'link_url': '/products?brand=steam',
            'is_active': True,
            'display_order': 3
        }
    ]
    
    # الماركات الأخرى
    other_brands_data = [
        {
            'name': 'Netflix',
            'image_url': '/static/images/brands/netflix.jpg',
            'link_url': '/products?brand=netflix',
            'is_active': True,
            'display_order': 1
        },
        {
            'name': 'Spotify',
            'image_url': '/static/images/brands/spotify.jpg',
            'link_url': '/products?brand=spotify',
            'is_active': True,
            'display_order': 2
        },
        {
            'name': 'Amazon',
            'image_url': '/static/images/brands/amazon.jpg',
            'link_url': '/products?brand=amazon',
            'is_active': True,
            'display_order': 3
        }
    ]
    
    # إضافة العروض الرئيسية
    added_offers = 0
    for offer_data in main_offers_data:
        existing_offer = MainOffer.query.filter_by(title=offer_data['title']).first()
        if not existing_offer:
            offer = MainOffer(**offer_data)
            db.session.add(offer)
            added_offers += 1
        else:
            for key, value in offer_data.items():
                setattr(existing_offer, key, value)
    
    # الفئات السريعة
    added_categories = 0
    for category_data in quick_categories_data:
        existing_category = QuickCategory.query.filter_by(name=category_data['name']).first()
        if not existing_category:
            category = QuickCategory(**category_data)
            db.session.add(category)
            added_categories += 1
        else:
            for key, value in category_data.items():
                setattr(existing_category, key, value)
    
    # بطاقات الهدايا
    added_cards = 0
    for card_data in gift_cards_data:
        existing_card = GiftCardSection.query.filter_by(title=card_data['title']).first()
        if not existing_card:
            card = GiftCardSection(**card_data)
            db.session.add(card)
            added_cards += 1
        else:
            for key, value in card_data.items():
                setattr(existing_card, key, value)
    
    # الماركات الأخرى
    added_brands = 0
    for brand_data in other_brands_data:
        existing_brand = OtherBrand.query.filter_by(name=brand_data['name']).first()
        if not existing_brand:
            brand = OtherBrand(**brand_data)
            db.session.add(brand)
            added_brands += 1
        else:
            for key, value in brand_data.items():
                setattr(existing_brand, key, value)
    
    db.session.commit()
    print(f"تم إضافة/تحديث محتوى الصفحة الرئيسية: {added_offers} عروض، {added_categories} فئات، {added_cards} بطاقات، {added_brands} ماركات")

def update_product_codes_with_orders():
    """ربط أكواد المنتجات بالطلبات المكتملة"""
    print("ربط الأكواد بالطلبات...")
    
    completed_orders = Order.query.filter_by(order_status='completed').all()
    
    for order in completed_orders:
        for item in order.items:
            # البحث عن أكواد غير مستخدمة للمنتج
            available_codes = ProductCode.query.filter_by(
                product_id=item.product_id,
                is_used=False,
                order_id=None
            ).limit(item.quantity).all()
            
            for i, code in enumerate(available_codes):
                if i < item.quantity:
                    code.is_used = True
                    code.used_at = order.created_at
                    code.order_id = order.id
    
    db.session.commit()
    print("تم ربط الأكواد بالطلبات المكتملة")

def main():
    """الدالة الرئيسية لتشغيل إضافة البيانات"""
    app = create_app()
    
    with app.app_context():
        print("=== بدء إضافة البيانات التجريبية ===")
        print(f"التاريخ والوقت: {datetime.now()}")
        print("-" * 50)
        
        try:
            # إنشاء الجداول إذا لم تكن موجودة
            db.create_all()
            
            # إضافة البيانات بالتسلسل الصحيح
            populate_currencies()
            populate_payment_gateways()
            populate_users()
            populate_categories()
            populate_products()
            populate_product_codes()
            populate_orders()
            populate_articles()
            populate_api_settings()
            populate_homepage_content()
            update_product_codes_with_orders()
            
            print("-" * 50)
            print("✅ تم إنجاز إضافة جميع البيانات التجريبية بنجاح!")
            print("\nملخص البيانات المضافة:")
            print(f"- المستخدمين: {User.query.count()}")
            print(f"- المنتجات: {Product.query.count()}")
            print(f"- أكواد المنتجات: {ProductCode.query.count()}")
            print(f"- الطلبات: {Order.query.count()}")
            print(f"- عناصر الطلبات: {OrderItem.query.count()}")
            print(f"- العملات: {Currency.query.count()}")
            print(f"- بوابات الدفع: {PaymentGateway.query.count()}")
            print(f"- الأقسام الرئيسية: {Category.query.count()}")
            print(f"- الأقسام الفرعية: {Subcategory.query.count()}")
            print(f"- المقالات: {Article.query.count()}")
            print(f"- إعدادات API: {APISettings.query.count()}")
            
            print("\n=== بيانات تسجيل الدخول ===")
            print("المدير الرئيسي:")
            print("البريد الإلكتروني: admin@es-gift.com")
            print("كلمة المرور: admin123")
            print("\nعملاء تجريبيون:")
            print("ahmed.mohammed@gmail.com - password123")
            print("fatima.ali@gmail.com - password123")
            print("omar.hassan@gmail.com - password123")
            
        except Exception as e:
            print(f"❌ حدث خطأ أثناء إضافة البيانات: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()
