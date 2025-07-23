from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)  # اسم المستخدم
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    nationality = db.Column(db.String(50))
    customer_type = db.Column(db.String(20), default='regular')  # regular, kyc, reseller
    kyc_status = db.Column(db.String(20), default='none')  # none, pending, approved, rejected
    
    # Google OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)  # Google ID
    profile_picture = db.Column(db.String(300))  # صورة البروفايل من Google
    is_verified = db.Column(db.Boolean, default=False)  # تم التحقق من الإيميل
    
    # KYC Document Type
    document_type = db.Column(db.String(50))  # national_id, passport, driver_license
    
    # Traditional document images (for backward compatibility)
    id_front_image = db.Column(db.String(200))
    id_back_image = db.Column(db.String(200))
    selfie_image = db.Column(db.String(200))
    
    # New KYC document images
    passport_image = db.Column(db.String(200))
    driver_license_image = db.Column(db.String(200))
    
    # Face verification photos
    face_photo_front = db.Column(db.String(200))
    face_photo_right = db.Column(db.String(200))
    face_photo_left = db.Column(db.String(200))
    
    is_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))  # الاسم بالإنجليزية
    description = db.Column(db.Text)
    detailed_description = db.Column(db.Text)  # وصف مفصل
    category = db.Column(db.String(100))  # للتوافق مع النظام القديم
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # القسم الرئيسي الجديد
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'))  # القسم الفرعي
    region = db.Column(db.String(50))
    value = db.Column(db.String(50))
    regular_price = db.Column(db.Numeric(10, 2))
    sale_price = db.Column(db.Numeric(10, 2))  # سعر العرض
    kyc_price = db.Column(db.Numeric(10, 2))
    reseller_price = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(200))
    instructions = db.Column(db.Text)
    expiry_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=0)
    digital_delivery = db.Column(db.Boolean, default=True)  # توصيل رقمي
    instant_delivery = db.Column(db.Boolean, default=True)  # توصيل فوري
    is_featured = db.Column(db.Boolean, default=False)  # منتج مميز
    # إضافة ميزات التحكم في الظهور والأسعار المخصصة
    visibility = db.Column(db.String(20), default='public')  # public, restricted
    restricted_visibility = db.Column(db.Boolean, default=False)  # للتوافق مع النظام القديم
    has_custom_pricing = db.Column(db.Boolean, default=False)  # أسعار مخصصة
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    codes = db.relationship('ProductCode', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    # إضافة العلاقات الجديدة
    allowed_users = db.relationship('ProductUserAccess', backref='product', lazy=True, cascade='all, delete-orphan')
    custom_prices = db.relationship('ProductCustomPrice', backref='product', lazy=True, cascade='all, delete-orphan')
    # العلاقات مع الأقسام
    main_category = db.relationship('Category', backref='products', lazy=True, foreign_keys=[category_id])
    sub_category = db.relationship('Subcategory', backref='products', lazy=True, foreign_keys=[subcategory_id])

class ProductCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    code = db.Column(db.String(500), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='SAR')
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), default='pending')
    order_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy=True)
    codes = db.relationship('ProductCode', backref='order', lazy=True)
    
    @property
    def total_price(self):
        """Backward compatibility property"""
        return self.total_amount
    
    @property
    def status(self):
        """Backward compatibility property"""
        return self.order_status

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='SAR')  # حفظ العملة المستخدمة في الشراء

class PaymentGateway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # visa_mastercard, mada, stc_pay
    is_active = db.Column(db.Boolean, default=True)
    config = db.Column(db.JSON)  # إعدادات JSON للبوابة
    supported_currencies = db.Column(db.JSON)  # قائمة العملات المدعومة
    min_amount = db.Column(db.Numeric(10, 2), default=1.00)
    max_amount = db.Column(db.Numeric(10, 2), default=10000.00)
    fee_percentage = db.Column(db.Numeric(5, 2), default=0)
    fee_fixed = db.Column(db.Numeric(10, 2), default=0.00)
    api_key = db.Column(db.String(200))
    secret_key = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(5), nullable=False)
    exchange_rate = db.Column(db.Numeric(10, 4), default=1.0)  # نسبة إلى الريال السعودي
    is_active = db.Column(db.Boolean, default=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200))
    author = db.Column(db.String(100))
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class APISettings(db.Model):
    __tablename__ = 'api_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    api_name = db.Column(db.String(100), nullable=False)
    api_url = db.Column(db.String(200))
    api_key = db.Column(db.String(200))
    secret_key = db.Column(db.String(200))
    reseller_username = db.Column(db.String(100))
    api_type = db.Column(db.String(50), default='onecard')  # onecard, custom
    is_active = db.Column(db.Boolean, default=True)
    settings_json = db.Column(db.Text)
    last_sync = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')  # pending, success, error
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIProduct(db.Model):
    """منتجات مستقبلة من API"""
    __tablename__ = 'api_product'
    
    id = db.Column(db.Integer, primary_key=True)
    api_settings_id = db.Column(db.Integer, db.ForeignKey('api_settings.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))  # ربط مع منتج محلي
    
    # معرفات المنتج الخارجي
    external_product_id = db.Column(db.String(100), nullable=False)  # معرف المنتج في API
    provider_product_id = db.Column(db.String(100), nullable=False)  # معرف المنتج عند المزود
    provider = db.Column(db.String(50), default='onecard')  # اسم المزود
    provider_name = db.Column(db.String(200))  # اسم المنتج عند المزود
    
    # تفاصيل المنتج
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    
    # معلومات السعر والمخزون
    price = db.Column(db.Numeric(10, 2))
    provider_price = db.Column(db.Numeric(10, 2))  # سعر المزود
    currency = db.Column(db.String(3), default='SAR')
    provider_currency = db.Column(db.String(3), default='SAR')  # عملة المزود
    stock_status = db.Column(db.Boolean, default=True)
    
    # حالة التكامل
    is_active = db.Column(db.Boolean, default=True)
    is_imported = db.Column(db.Boolean, default=False)  # هل تم استيراده كمنتج محلي
    
    # بيانات إضافية
    raw_data = db.Column(db.Text)  # البيانات الخام من API  
    sync_data = db.Column(db.Text)  # بيانات المزامنة
    
    # التوقيتات
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    api_setting = db.relationship('APISettings', backref='api_products')
    local_product = db.relationship('Product', backref='api_products')

class APITransaction(db.Model):
    """معاملات الشراء من API"""
    __tablename__ = 'api_transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    api_settings_id = db.Column(db.Integer, db.ForeignKey('api_settings.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    external_product_id = db.Column(db.String(100), nullable=False)
    reseller_ref_number = db.Column(db.String(100), unique=True, nullable=False)
    transaction_status = db.Column(db.String(20), default='pending')  # pending, success, failed
    purchase_response = db.Column(db.Text)  # استجابة API
    product_codes = db.Column(db.Text)  # أكواد المنتج المستلمة
    amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(3), default='SAR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    api_setting = db.relationship('APISettings', backref='transactions')
    order = db.relationship('Order', backref='api_transactions')

# نماذج إدارة الصفحة الرئيسية
class MainOffer(db.Model):
    """العروض الرئيسية - صورة مع رابط"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))  # العنوان بالإنجليزية
    description = db.Column(db.Text)  # وصف العرض
    image_url = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(500), nullable=False)
    button_text = db.Column(db.String(100), default='اشتري الآن')  # نص الزر
    start_date = db.Column(db.DateTime)  # تاريخ بداية العرض
    end_date = db.Column(db.DateTime)  # تاريخ انتهاء العرض
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class GiftCardSection(db.Model):
    """بطاقات الهدايا - صورة مع رابط"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))  # العنوان بالإنجليزية
    description = db.Column(db.Text)  # وصف القسم
    image_url = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(500), nullable=False)
    button_text = db.Column(db.String(100), default='تصفح الآن')  # نص الزر
    card_type = db.Column(db.String(50), default='gift')  # نوع البطاقة للفلترة (gift, shopping, mobile, films, pc, xbox, stc)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OtherBrand(db.Model):
    """ماركات أخرى - اسم وصورة ورابط"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))  # الاسم بالإنجليزية
    description = db.Column(db.Text)  # وصف العلامة التجارية
    logo_url = db.Column(db.String(500), nullable=False)  # شعار العلامة التجارية
    image_url = db.Column(db.String(500), nullable=False)  # للتوافق مع النظام القديم
    link_url = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نماذج إدارة الأقسام
class Category(db.Model):
    """الأقسام الرئيسية"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))  # الاسم بالإنجليزية
    description = db.Column(db.Text)
    icon_class = db.Column(db.String(100))  # أيقونة FontAwesome
    image_url = db.Column(db.String(500))
    show_in_header = db.Column(db.Boolean, default=True)  # إظهار في الهيدر
    show_in_footer = db.Column(db.Boolean, default=True)  # إظهار في الفوتر
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقة مع الأقسام الفرعية
    subcategories = db.relationship('Subcategory', backref='parent_category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Subcategory(db.Model):
    """الأقسام الفرعية"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))  # الاسم بالإنجليزية
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    icon_class = db.Column(db.String(100))  # أيقونة FontAwesome
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subcategory {self.name}>'

class ProductUserAccess(db.Model):
    """جدول للتحكم في ظهور المنتجات لمستخدمين محددين"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)  # حفظ البريد للمرجعية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقة مع المستخدم
    user = db.relationship('User', backref='product_access', lazy=True)
    
    # فهرس مركب لمنع التكرار
    __table_args__ = (db.UniqueConstraint('product_id', 'user_id', name='unique_product_user_access'),)

class ProductCustomPrice(db.Model):
    """جدول للأسعار المخصصة لمستخدمين محددين"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)  # حفظ البريد للمرجعية
    regular_price = db.Column(db.Numeric(10, 2), nullable=False)  # السعر العادي المخصص
    kyc_price = db.Column(db.Numeric(10, 2), nullable=False)  # سعر KYC المخصص
    custom_price = db.Column(db.Numeric(10, 2))  # للتوافق مع النظام القديم
    note = db.Column(db.String(200))  # ملاحظة على السعر المخصص
    price_note = db.Column(db.String(200))  # للتوافق مع النظام القديم
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقة مع المستخدم
    user = db.relationship('User', backref='custom_prices', lazy=True)
    
    # فهرس مركب لمنع التكرار
    __table_args__ = (db.UniqueConstraint('product_id', 'user_id', name='unique_product_user_price'),)

# نماذج إدارة المحفظة والحدود المالية
class UserLimits(db.Model):
    """حدود الشراء اليومية والشهرية للمستخدمين"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # الحدود اليومية (بالدولار الأمريكي)
    daily_limit_usd = db.Column(db.Numeric(10, 2), default=3000.00)  # افتراضي للعادي
    daily_spent_usd = db.Column(db.Numeric(10, 2), default=0.00)  # المبلغ المنفق اليوم
    
    # الحدود الشهرية (بالدولار الأمريكي) 
    monthly_limit_usd = db.Column(db.Numeric(10, 2), default=90000.00)  # 30 يوم × 3000
    monthly_spent_usd = db.Column(db.Numeric(10, 2), default=0.00)  # المبلغ المنفق هذا الشهر
    
    # تواريخ إعادة تعيين الحدود
    last_daily_reset = db.Column(db.Date, default=datetime.utcnow().date)
    last_monthly_reset = db.Column(db.Date, default=datetime.utcnow().date)
    
    # معلومات إضافية
    is_custom = db.Column(db.Boolean, default=False)  # هل تم تعديلها يدوياً
    notes = db.Column(db.Text)  # ملاحظات من الأدمن
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # علاقة مع المستخدم
    user = db.relationship('User', backref='limits', lazy=True)

class GlobalLimits(db.Model):
    """الحدود الافتراضية حسب نوع المستخدم"""
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), nullable=False, unique=True)  # normal, kyc, distributor
    
    # الحدود اليومية والشهرية (بالدولار الأمريكي)
    daily_limit_usd = db.Column(db.Numeric(10, 2), nullable=False)
    monthly_limit_usd = db.Column(db.Numeric(10, 2), nullable=False)
    
    # وصف نوع المستخدم
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # حالة التفعيل
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WalletTransaction(db.Model):
    """سجل معاملات المحفظة للمستخدمين"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # نوع المعاملة
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, purchase, refund
    
    # المبالغ
    amount_usd = db.Column(db.Numeric(10, 2), nullable=False)  # المبلغ بالدولار
    amount_original = db.Column(db.Numeric(10, 2), nullable=False)  # المبلغ بالعملة الأصلية
    currency_code = db.Column(db.String(3), nullable=False)  # رمز العملة
    exchange_rate = db.Column(db.Numeric(10, 6), nullable=False)  # سعر الصرف المستخدم
    
    # تفاصيل إضافية
    description = db.Column(db.String(500))
    reference_id = db.Column(db.String(100))  # مرجع خارجي (order_id, payment_id, etc.)
    reference_type = db.Column(db.String(50))  # order, payment, manual
    
    # حالة المعاملة
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed, cancelled
    
    # معلومات إضافية
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    admin_notes = db.Column(db.Text)  # ملاحظات الأدمن
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقة مع المستخدم
    user = db.relationship('User', backref='wallet_transactions', lazy=True)

class UserBalance(db.Model):
    """رصيد المستخدمين حسب العملة"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency_code = db.Column(db.String(3), nullable=False)
    
    # الرصيد
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    
    # آخر تحديث
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # علاقة مع المستخدم
    user = db.relationship('User', backref='balances', lazy=True)
    
    # فهرس مركب لمنع التكرار
    __table_args__ = (db.UniqueConstraint('user_id', 'currency_code', name='unique_user_currency_balance'),)

# نماذج إدارة الموظفين والصلاحيات
class Permission(db.Model):
    """جدول الصلاحيات المتاحة في النظام"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # users, products, orders, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Role(db.Model):
    """جدول الأدوار والمناصب"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)  # هل هذا الدور مدير عام؟
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RolePermission(db.Model):
    """جدول ربط الأدوار بالصلاحيات"""
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقات
    role = db.relationship('Role', backref='role_permissions', lazy=True)
    permission = db.relationship('Permission', backref='permission_roles', lazy=True)
    
    # فهرس مركب لمنع التكرار
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),)

class Employee(db.Model):
    """جدول الموظفين مع معلومات إضافية"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # رقم الموظف
    department = db.Column(db.String(100))  # القسم
    position = db.Column(db.String(100))  # المنصب
    hire_date = db.Column(db.Date)  # تاريخ التوظيف
    salary = db.Column(db.Numeric(10, 2))  # الراتب
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'))  # المدير المباشر
    
    # معلومات إضافية
    work_location = db.Column(db.String(200))  # مكان العمل
    contract_type = db.Column(db.String(50), default='full_time')  # نوع العقد
    status = db.Column(db.String(20), default='active')  # حالة الموظف: active, suspended, terminated
    
    # صلاحيات خاصة (إضافية للدور)
    can_access_reports = db.Column(db.Boolean, default=False)
    can_manage_currencies = db.Column(db.Boolean, default=False)
    can_manage_categories = db.Column(db.Boolean, default=False)
    max_discount_percent = db.Column(db.Integer, default=0)  # أقصى نسبة خصم يمكن منحها
    
    # التواريخ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # علاقات
    user = db.relationship('User', backref='employee_profile', lazy=True)
    role = db.relationship('Role', backref='employees', lazy=True)
    manager = db.relationship('Employee', remote_side=[id], backref='subordinates', lazy=True)

class EmployeePermission(db.Model):
    """صلاحيات إضافية خاصة بموظف معين (تجاوز صلاحيات الدور)"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    granted = db.Column(db.Boolean, default=True)  # منحت أم ألغيت
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # من منح الصلاحية
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # تاريخ انتهاء الصلاحية (اختياري)
    reason = db.Column(db.Text)  # سبب منح أو إلغاء الصلاحية
    
    # علاقات
    employee = db.relationship('Employee', backref='special_permissions', lazy=True)
    permission = db.relationship('Permission', backref='special_grants', lazy=True)
    granted_by_user = db.relationship('User', backref='granted_permissions', lazy=True)
    
    # فهرس مركب لمنع التكرار
    __table_args__ = (db.UniqueConstraint('employee_id', 'permission_id', name='unique_employee_permission'),)

class ActivityLog(db.Model):
    """سجل نشاطات الموظفين"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # login, logout, create_product, etc.
    resource_type = db.Column(db.String(50))  # User, Product, Order, etc.
    resource_id = db.Column(db.Integer)  # ID الخاص بالمورد
    description = db.Column(db.Text)  # وصف النشاط
    ip_address = db.Column(db.String(45))  # عنوان IP
    user_agent = db.Column(db.Text)  # معلومات المتصفح
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقة مع الموظف
    employee = db.relationship('Employee', backref='activity_logs', lazy=True)

# نماذج المحفظة ونظام الحدود
class UserWallet(db.Model):
    """محفظة المستخدم ومعلومات الحدود"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # الرصيد
    balance = db.Column(db.Numeric(12, 2), default=0.00)  # الرصيد الحالي
    currency = db.Column(db.String(10), default='USD')  # عملة المحفظة الرئيسية
    
    # الحدود اليومية
    daily_limit = db.Column(db.Numeric(12, 2), default=3000.00)  # الحد الأقصى اليومي
    daily_spent_today = db.Column(db.Numeric(12, 2), default=0.00)  # المبلغ المنفق اليوم
    last_daily_reset = db.Column(db.Date, default=datetime.utcnow().date())  # آخر إعادة تعيين يومية
    
    # الحدود الشهرية
    monthly_limit = db.Column(db.Numeric(12, 2), default=90000.00)  # الحد الأقصى الشهري
    monthly_spent = db.Column(db.Numeric(12, 2), default=0.00)  # المبلغ المنفق هذا الشهر
    last_monthly_reset = db.Column(db.Date, default=datetime.utcnow().replace(day=1).date())  # آخر إعادة تعيين شهرية
    
    # إحصائيات
    total_deposits = db.Column(db.Numeric(12, 2), default=0.00)  # إجمالي الإيداعات
    total_purchases = db.Column(db.Numeric(12, 2), default=0.00)  # إجمالي المشتريات
    total_orders = db.Column(db.Integer, default=0)  # إجمالي الطلبات
    
    # معلومات إضافية
    is_blocked = db.Column(db.Boolean, default=False)  # هل المحفظة محظورة
    block_reason = db.Column(db.Text)  # سبب الحظر
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # علاقة مع المستخدم
    user = db.relationship('User', backref='wallet', lazy=True)

# نماذج إدارة الموظفين والصلاحيات

class StaticPage(db.Model):
    """نموذج الصفحات الثابتة"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # عنوان الصفحة
    slug = db.Column(db.String(100), unique=True, nullable=False)  # الرابط المختصر
    content = db.Column(db.Text, nullable=False)  # محتوى الصفحة
    meta_description = db.Column(db.String(300))  # وصف السيو
    meta_keywords = db.Column(db.String(500))  # كلمات مفتاحية للسيو
    is_active = db.Column(db.Boolean, default=True)  # نشطة أم لا
    show_in_footer = db.Column(db.Boolean, default=True)  # إظهار في الفوتر
    show_in_header = db.Column(db.Boolean, default=False)  # إظهار في الهيدر
    display_order = db.Column(db.Integer, default=0)  # ترتيب العرض
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # من قام بإنشائها
    
    def __repr__(self):
        return f'<StaticPage {self.title}>'
