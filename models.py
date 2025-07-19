from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    nationality = db.Column(db.String(50))
    customer_type = db.Column(db.String(20), default='regular')  # regular, kyc, reseller
    kyc_status = db.Column(db.String(20), default='none')  # none, pending, approved, rejected
    
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
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # للتوافق مع النظام القديم
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # القسم الرئيسي الجديد
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'))  # القسم الفرعي
    region = db.Column(db.String(50))
    value = db.Column(db.String(50))
    regular_price = db.Column(db.Numeric(10, 2))
    kyc_price = db.Column(db.Numeric(10, 2))
    reseller_price = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(200))
    instructions = db.Column(db.Text)
    expiry_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=0)
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
    fee_percentage = db.Column(db.Numeric(5, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    api_key = db.Column(db.String(200))
    secret_key = db.Column(db.String(200))

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
    id = db.Column(db.Integer, primary_key=True)
    api_name = db.Column(db.String(100), nullable=False)
    api_url = db.Column(db.String(200))
    api_key = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    settings_json = db.Column(db.Text)

# نماذج إدارة الصفحة الرئيسية
class MainOffer(db.Model):
    """العروض الرئيسية - صورة مع رابط"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class GiftCardSection(db.Model):
    """بطاقات الهدايا - صورة مع رابط"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(500), nullable=False)
    card_type = db.Column(db.String(50), default='gift')  # نوع البطاقة للفلترة (gift, shopping, mobile, films, pc, xbox, stc)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OtherBrand(db.Model):
    """ماركات أخرى - اسم وصورة ورابط"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
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
