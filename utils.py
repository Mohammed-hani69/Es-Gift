import json
from flask import current_app
from flask_mail import Message
from models import Currency, db
from datetime import datetime

def to_json_filter(obj):
    """تحويل الكائن إلى JSON"""
    return json.dumps(obj, default=str, ensure_ascii=False)

def get_user_price(product, user_type='regular', user=None):
    """احصل على السعر المناسب للمستخدم مع دعم الأسعار المخصصة"""
    
    # إذا كان المنتج يحتوي على أسعار مخصصة والمستخدم مسجل
    if product.has_custom_pricing and user and user.is_authenticated:
        # البحث عن سعر مخصص للمستخدم
        from models import ProductCustomPrice
        custom_price = ProductCustomPrice.query.filter_by(
            product_id=product.id,
            user_id=user.id
        ).first()
        
        if custom_price:
            return custom_price.custom_price
    
    # الأسعار العادية
    if user_type == 'reseller':
        return product.reseller_price
    elif user_type == 'kyc':
        return product.kyc_price
    else:
        return product.regular_price

def convert_currency(amount, from_currency='SAR', to_currency='SAR'):
    """تحويل العملة مع معالجة شاملة للأخطاء"""
    # إذا كانت العملة الأصلية والمطلوبة نفسها
    if from_currency == to_currency:
        return amount
    
    try:
        # جلب أسعار الصرف من قاعدة البيانات
        from_rate = Currency.query.filter_by(code=from_currency, is_active=True).first()
        to_rate = Currency.query.filter_by(code=to_currency, is_active=True).first()
        
        # التحقق من وجود العملات
        if not from_rate:
            print(f"تحذير: العملة {from_currency} غير موجودة في النظام")
            return amount
            
        if not to_rate:
            print(f"تحذير: العملة {to_currency} غير موجودة في النظام")
            return amount
        
        # استخدام Decimal للحسابات الدقيقة
        from decimal import Decimal, ROUND_HALF_UP
        
        # تحويل القيم إلى Decimal
        from_exchange_rate = Decimal(str(from_rate.exchange_rate))
        to_exchange_rate = Decimal(str(to_rate.exchange_rate))
        amount_decimal = Decimal(str(amount))
        
        # المنطق المصحح للتحويل:
        # exchange_rate في قاعدة البيانات يمثل: كم وحدة من هذه العملة = 1 ريال سعودي
        # مثال: USD = 0.27 يعني 1 ريال = 0.27 دولار
        
        if from_currency == 'SAR':
            # التحويل من الريال إلى عملة أخرى: اضرب في exchange_rate
            final_amount = amount_decimal * to_exchange_rate
        elif to_currency == 'SAR':
            # التحويل من عملة أخرى إلى الريال: اقسم على exchange_rate
            final_amount = amount_decimal / from_exchange_rate
        else:
            # التحويل بين عملتين (ليس الريال): تحويل إلى الريال ثم إلى العملة المطلوبة
            sar_amount = amount_decimal / from_exchange_rate
            final_amount = sar_amount * to_exchange_rate
        
        # تقريب النتيجة إلى منزلتين عشريتين
        result = final_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return float(result)
        
    except Exception as e:
        print(f"خطأ في تحويل العملة من {from_currency} إلى {to_currency}: {e}")
        return amount

def send_email(to_email, subject, body):
    """إرسال بريد إلكتروني"""
    try:
        from flask_mail import Mail
        mail = current_app.extensions.get('mail')
        
        # التحقق من إعدادات الإيميل
        if not current_app.config['MAIL_USERNAME'] or not current_app.config['MAIL_PASSWORD']:
            print("خطأ: لم يتم تكوين إعدادات البريد الإلكتروني")
            return False
            
        if current_app.config['MAIL_USERNAME'] == 'your-email@gmail.com':
            print("خطأ: يجب تغيير إعدادات البريد الإلكتروني في ملف .env")
            return False
        
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[to_email]
        )
        msg.html = body
        mail.send(msg)
        print(f"تم إرسال الإيميل بنجاح إلى: {to_email}")
        return True
    except Exception as e:
        print(f"خطأ في إرسال الإيميل: {e}")
        print("نصائح لحل المشكلة:")
        print("1. تأكد من تفعيل التحقق بخطوتين في حساب Google")
        print("2. استخدم App Password بدلاً من كلمة المرور العادية")
        print("3. تأكد من صحة بيانات البريد في ملف .env")
        return False

def send_order_email(order):
    """إرسال بريد إلكتروني بتفاصيل الطلب والأكواد"""
    from models import ProductCode
    
    codes = ProductCode.query.filter_by(order_id=order.id).all()
    
    email_body = f"""
    <h2>تفاصيل طلبك #{order.order_number}</h2>
    <p>عزيزي العميل،</p>
    <p>تم إتمام طلبك بنجاح. إليك تفاصيل المنتجات والأكواد:</p>
    
    <div style="background-color: #f5f5f5; padding: 20px; border-radius: 10px;">
    """
    
    for code in codes:
        email_body += f"""
        <div style="margin-bottom: 20px; padding: 15px; background-color: white; border-radius: 5px;">
            <h3>{code.product.name}</h3>
            <p><strong>الكود:</strong> {code.code}</p>
            <p><strong>التعليمات:</strong> {code.product.instructions}</p>
        </div>
        """
    
    email_body += """
    </div>
    <p>شكراً لك على الشراء من Es-Gift</p>
    """
    
    send_email(order.user.email, f"تفاصيل طلبك #{order.order_number}", email_body)

def update_currency_rates():
    """تحديث أسعار الصرف من مصدر خارجي (يمكن تطويرها لاحقاً)"""
    try:
        from models import Currency, db
        
        # معدلات محدثة (يمكن استبدالها بـ API حقيقي)
        updated_rates = {
            'USD': 3.75,
            'EUR': 4.05,
            'GBP': 4.75,
            'AED': 1.02,
            'KWD': 0.31,
            'QAR': 1.37,
            'BHD': 0.41,
            'OMR': 0.38,
            'EGP': 48.5,
            'JOD': 0.71
        }
        
        for code, rate in updated_rates.items():
            currency = Currency.query.filter_by(code=code).first()
            if currency:
                currency.exchange_rate = rate
        
        db.session.commit()
        print("تم تحديث أسعار الصرف بنجاح")
        return True
        
    except Exception as e:
        print(f"خطأ في تحديث أسعار الصرف: {e}")
        db.session.rollback()
        return False

def format_currency(amount, currency_code='SAR'):
    """تنسيق العملة للعرض"""
    try:
        from models import Currency
        
        currency = Currency.query.filter_by(code=currency_code).first()
        if not currency:
            return f"{amount:.2f}"
        
        # تنسيق خاص للعملات العربية
        if currency_code in ['SAR', 'AED', 'QAR', 'KWD', 'BHD', 'OMR', 'EGP', 'JOD']:
            return f"{amount:.2f} {currency.symbol}"
        else:
            return f"{currency.symbol}{amount:.2f}"
            
    except Exception as e:
        print(f"خطأ في تنسيق العملة: {e}")
        return f"{amount:.2f}"

def get_currency_info(currency_code):
    """الحصول على معلومات العملة"""
    try:
        from models import Currency
        
        currency = Currency.query.filter_by(code=currency_code, is_active=True).first()
        if currency:
            return {
                'code': currency.code,
                'name': currency.name,
                'symbol': currency.symbol,
                'rate': float(currency.exchange_rate)
            }
        return None
        
    except Exception as e:
        print(f"خطأ في جلب معلومات العملة: {e}")
        return None

def initialize_default_currencies():
    """تهيئة العملات الافتراضية في قاعدة البيانات"""
    from models import Currency, db
    
    default_currencies = [
        # العملة المرجعية (الريال السعودي)
        {'code': 'SAR', 'name': 'ريال سعودي', 'symbol': 'ر.س', 'exchange_rate': 1.0, 'is_active': True},
        
        # العملات الرئيسية
        {'code': 'USD', 'name': 'دولار أمريكي', 'symbol': '$', 'exchange_rate': 3.75, 'is_active': True},
        {'code': 'EUR', 'name': 'يورو', 'symbol': '€', 'exchange_rate': 4.05, 'is_active': True},
        {'code': 'GBP', 'name': 'جنيه إسترليني', 'symbol': '£', 'exchange_rate': 4.75, 'is_active': True},
        
        # عملات الخليج العربي
        {'code': 'AED', 'name': 'درهم إماراتي', 'symbol': 'د.إ', 'exchange_rate': 1.02, 'is_active': True},
        {'code': 'KWD', 'name': 'دينار كويتي', 'symbol': 'د.ك', 'exchange_rate': 0.31, 'is_active': True},
        {'code': 'QAR', 'name': 'ريال قطري', 'symbol': 'ر.ق', 'exchange_rate': 1.37, 'is_active': True},
        {'code': 'BHD', 'name': 'دينار بحريني', 'symbol': 'د.ب', 'exchange_rate': 0.41, 'is_active': True},
        {'code': 'OMR', 'name': 'ريال عماني', 'symbol': 'ر.ع', 'exchange_rate': 0.38, 'is_active': True},
        
        # عملات عربية أخرى
        {'code': 'EGP', 'name': 'جنيه مصري', 'symbol': 'ج.م', 'exchange_rate': 48.5, 'is_active': True},
        {'code': 'JOD', 'name': 'دينار أردني', 'symbol': 'د.أ', 'exchange_rate': 0.71, 'is_active': True},
        {'code': 'LBP', 'name': 'ليرة لبنانية', 'symbol': 'ل.ل', 'exchange_rate': 56250, 'is_active': False},
        
        # عملات آسيوية شائعة
        {'code': 'JPY', 'name': 'ين ياباني', 'symbol': '¥', 'exchange_rate': 555, 'is_active': False},
        {'code': 'CNY', 'name': 'يوان صيني', 'symbol': '¥', 'exchange_rate': 27.2, 'is_active': False},
        {'code': 'INR', 'name': 'روبية هندية', 'symbol': '₹', 'exchange_rate': 312, 'is_active': False}
    ]
    
    for currency_data in default_currencies:
        existing = Currency.query.filter_by(code=currency_data['code']).first()
        if not existing:
            currency = Currency(**currency_data)
            db.session.add(currency)
    
    try:
        db.session.commit()
        print("تم تهيئة العملات الافتراضية بنجاح")
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في تهيئة العملات: {e}")

def filter_products_by_visibility(products_query, user=None):
    """فلترة المنتجات بناءً على قيود الرؤية"""
    from models import ProductUserAccess, Product
    
    if not user or not user.is_authenticated:
        # المستخدمون غير المسجلين: المنتجات العامة فقط
        return products_query.filter_by(restricted_visibility=False)
    
    # المدراء يرون جميع المنتجات
    if user.is_admin:
        return products_query
    
    # المستخدمون المسجلون: المنتجات العامة + المنتجات المخصصة لهم
    from sqlalchemy import or_
    
    return products_query.filter(
        or_(
            # المنتجات العامة (غير مقيدة الرؤية)
            Product.restricted_visibility == False,
            # أو المنتجات المخصصة للمستخدم
            Product.id.in_(
                db.session.query(ProductUserAccess.product_id)
                .filter_by(user_id=user.id)
                .subquery()
            )
        )
    )

def get_visible_products(user=None, **filters):
    """احصل على المنتجات المرئية للمستخدم"""
    from models import Product
    
    # البدء بجميع المنتجات النشطة
    query = Product.query.filter_by(is_active=True)
    
    # إضافة فلاتر إضافية
    for key, value in filters.items():
        if hasattr(Product, key):
            query = query.filter(getattr(Product, key) == value)
    
    # فلترة بناءً على الرؤية
    query = filter_products_by_visibility(query, user)
    
    return query
