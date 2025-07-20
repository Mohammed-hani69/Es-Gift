from flask import Flask, url_for
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
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
    
    # تهيئة Flask-Migrate
    migrate = Migrate(app, db)
    
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
        from utils import format_currency, convert_currency
        from flask import session
        
        # جلب الأقسام النشطة مرتبة حسب الترتيب
        main_categories = Category.query.filter_by(is_active=True).order_by(Category.display_order, Category.name).limit(8).all()
        # جلب العملات النشطة
        currencies = Currency.query.filter_by(is_active=True).order_by(Currency.code).all()
        current_currency = session.get('currency', 'SAR')
        
        return dict(
            main_categories=main_categories, 
            currencies=currencies,
            current_currency=current_currency,
            format_currency=format_currency,
            convert_currency=convert_currency
        )
    
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
    
    # تسجيل blueprint المحفظة
    from wallet_routes import wallet_bp
    app.register_blueprint(wallet_bp)
    
    # تسجيل blueprint إدارة الحدود المالية
    from admin_routes_financial import financial_bp
    app.register_blueprint(financial_bp)
    
    return app

app = create_app()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
