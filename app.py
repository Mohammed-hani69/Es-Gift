from flask import Flask, url_for
from flask_login import LoginManager
from flask_mail import Mail
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

from config import Config
from models import db, User
from utils import to_json_filter
from routes import main
from admin_routes import admin

def create_app():
    """إنشاء وتكوين التطبيق"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # تهيئة الإضافات
    db.init_app(app)
    
    mail = Mail(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # إنشاء مجلد التحميلات
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # إضافة فلتر JSON لـ Jinja2
    app.template_filter('tojsonfilter')(to_json_filter)
    
    # إضافة دالة إنشاء الـ slug كفلتر للقوالب
    @app.template_filter('create_slug')
    def create_slug_filter(text):
        """إنشاء slug من النص العربي أو الإنجليزي"""
        if not text:
            return ""
        
        import re
        
        # تحويل إلى نص صغير
        text = text.lower()
        
        # إزالة الأحرف الخاصة والرموز
        text = re.sub(r'[^\w\s\u0600-\u06FF-]', '', text)
        
        # استبدال المساحات بشرطات
        text = re.sub(r'[-\s]+', '-', text)
        
        # إزالة الشرطات من البداية والنهاية
        text = text.strip('-')
        
        return text
    
    # إضافة context processor للأقسام والعملات
    @app.context_processor
    def inject_global_data():
        from models import Category, Currency
        # جلب الأقسام النشطة مرتبة حسب الترتيب
        main_categories = Category.query.filter_by(is_active=True).order_by(Category.display_order, Category.name).limit(8).all()
        # جلب العملات النشطة
        currencies = Currency.query.filter_by(is_active=True).order_by(Currency.code).all()
        return dict(main_categories=main_categories, currencies=currencies)
    
    # إضافة دالة مساعدة لحل مسارات الصور
    @app.template_filter('image_url')
    def image_url_filter(image_path):
        """دالة لحل مسارات الصور بطريقة صحيحة"""
        if not image_path:
            return url_for('static', filename='images/default-product.jpg')
        
        # إذا كان المسار يبدأ بـ http فهو رابط خارجي
        if image_path.startswith('http'):
            return image_path
        
        # إذا كان المسار يبدأ بـ /static/ فهو مسار كامل (بيانات قديمة)
        if image_path.startswith('/static/'):
            return image_path
        
        # إذا كان المسار يحتوي على /static/ في الوسط (بيانات قديمة محفوظة خطأ)
        if '/static/' in image_path:
            return image_path.replace('/static/', '/').replace('//', '/')
        
        # إذا كان المسار لا يحتوي على /static/ فهو اسم ملف في مجلد uploads
        return url_for('static', filename='uploads/' + image_path)
    
    # تسجيل Blueprints
    app.register_blueprint(main)
    app.register_blueprint(admin)
    
    return app

def init_database(app):
    """تهيئة قاعدة البيانات مع البيانات الأولية"""
    with app.app_context():
        # حذف قاعدة البيانات القديمة وإنشاء واحدة جديدة لتطبيق التحديثات
        db.drop_all()
        db.create_all()
        
        # إنشاء مستخدم إداري افتراضي
        admin = User(
            email='admin@es-gift.com',
            password_hash=generate_password_hash('admin123'),
            full_name='المدير العام',
            is_admin=True,
            customer_type='admin',
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        
        # إنشاء منتجات عينة
        from models import Product
        
        sample_products = [
            {
                'name': 'بطاقة PlayStation Store 50 ر.س',
                'description': 'بطاقة شحن PlayStation Store للحصول على الألعاب والمحتوى الإضافي',
                'category': 'gaming',
                'region': 'السعودية',
                'value': '50 ر.س',
                'regular_price': 50.00,
                'kyc_price': 47.50,
                'reseller_price': 45.00,
                'image_url': '/static/images/playstation-card.jpg',
                'instructions': 'ادخل إلى PlayStation Store واستخدم الكود في قسم استرداد الأكواد',
                'stock_quantity': 100
            },
            {
                'name': 'بطاقة Xbox Live Gold 25 دولار',
                'description': 'بطاقة هدية Xbox Live Gold للعب الألعاب الجماعية والحصول على العروض',
                'category': 'gaming',
                'region': 'عالمي',
                'value': '25 دولار',
                'regular_price': 95.00,
                'kyc_price': 90.25,
                'reseller_price': 85.50,
                'image_url': '/static/images/xbox-card.jpg',
                'instructions': 'ادخل إلى Xbox وأدخل الكود في قسم استرداد الأكواد',
                'stock_quantity': 75
            },
            {
                'name': 'بطاقة Steam Wallet 20 دولار',
                'description': 'بطاقة شحن Steam لشراء الألعاب والمحتوى من متجر Steam',
                'category': 'gaming',
                'region': 'عالمي',
                'value': '20 دولار',
                'regular_price': 76.00,
                'kyc_price': 72.20,
                'reseller_price': 68.40,
                'image_url': '/static/images/steam-card.jpg',
                'instructions': 'ادخل إلى Steam وأضف الأموال إلى محفظتك باستخدام الكود',
                'stock_quantity': 150
            },
            {
                'name': 'بطاقة Google Play 100 ر.س',
                'description': 'بطاقة هدية Google Play للحصول على التطبيقات والألعاب والمحتوى',
                'category': 'mobile',
                'region': 'السعودية',
                'value': '100 ر.س',
                'regular_price': 100.00,
                'kyc_price': 95.00,
                'reseller_price': 90.00,
                'image_url': '/static/images/google-play-card.jpg',
                'instructions': 'ادخل إلى Google Play وأدخل الكود في قسم استرداد الأكواد',
                'stock_quantity': 200
            },
            {
                'name': 'بطاقة iTunes 15 دولار',
                'description': 'بطاقة هدية iTunes للحصول على الموسيقى والأفلام والتطبيقات',
                'category': 'mobile',
                'region': 'الولايات المتحدة',
                'value': '15 دولار',
                'regular_price': 57.00,
                'kyc_price': 54.15,
                'reseller_price': 51.30,
                'image_url': '/static/images/itunes-card.jpg',
                'instructions': 'ادخل إلى App Store أو iTunes وأدخل الكود',
                'stock_quantity': 80
            },
            {
                'name': 'بطاقة Nintendo eShop 35 دولار',
                'description': 'بطاقة هدية Nintendo eShop للحصول على الألعاب والمحتوى الإضافي',
                'category': 'gaming',
                'region': 'الولايات المتحدة',
                'value': '35 دولار',
                'regular_price': 133.00,
                'kyc_price': 126.35,
                'reseller_price': 119.70,
                'image_url': '/static/images/nintendo-card.jpg',
                'instructions': 'ادخل إلى Nintendo eShop وأدخل الكود',
                'stock_quantity': 60
            },
            {
                'name': 'بطاقة PUBG Mobile 1800 UC',
                'description': 'بطاقة شحن PUBG Mobile للحصول على 1800 UC',
                'category': 'mobile',
                'region': 'عالمي',
                'value': '1800 UC',
                'regular_price': 85.00,
                'kyc_price': 80.75,
                'reseller_price': 76.50,
                'image_url': '/static/images/pubg-card.jpg',
                'instructions': 'ادخل إلى PUBG Mobile وأدخل الكود في قسم الشحن',
                'stock_quantity': 300
            },
            {
                'name': 'بطاقة Free Fire 2200 ماسة',
                'description': 'بطاقة شحن Free Fire للحصول على 2200 ماسة',
                'category': 'mobile',
                'region': 'عالمي',
                'value': '2200 ماسة',
                'regular_price': 70.00,
                'kyc_price': 66.50,
                'reseller_price': 63.00,
                'image_url': '/static/images/freefire-card.jpg',
                'instructions': 'ادخل إلى Free Fire وأدخل الكود في قسم الشحن',
                'stock_quantity': 250
            }
        ]
        
        for product_data in sample_products:
            product = Product(**product_data)
            db.session.add(product)
        
        # إنشاء عملات افتراضية
        from models import Currency
        
        currencies = [
            {'code': 'SAR', 'name': 'الريال السعودي', 'symbol': 'ر.س', 'exchange_rate': 1.0},
            {'code': 'USD', 'name': 'الدولار الأمريكي', 'symbol': '$', 'exchange_rate': 3.75},
            {'code': 'AED', 'name': 'الدرهم الإماراتي', 'symbol': 'د.إ', 'exchange_rate': 1.02}
        ]
        
        for currency_data in currencies:
            currency = Currency(**currency_data)
            db.session.add(currency)
        
        # إنشاء بوابات دفع افتراضية
        from models import PaymentGateway
        
        gateways = [
            {'name': 'فيزا/ماستركارد', 'fee_percentage': 2.9, 'is_active': True},
            {'name': 'مدى', 'fee_percentage': 1.5, 'is_active': True},
            {'name': 'أبل باي', 'fee_percentage': 2.5, 'is_active': True},
            {'name': 'التحويل البنكي', 'fee_percentage': 0.0, 'is_active': True}
        ]
        
        for gateway_data in gateways:
            gateway = PaymentGateway(**gateway_data)
            db.session.add(gateway)
        
        db.session.commit()
        print("تم إنشاء قاعدة البيانات والبيانات الأولية بنجاح!")
        print("بيانات الدخول للمدير:")
        print("البريد الإلكتروني: admin@es-gift.com")
        print("كلمة المرور: admin123")

if __name__ == '__main__':
    app = create_app()
    
    # تهيئة قاعدة البيانات في المرة الأولى فقط
    init_database(app)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
