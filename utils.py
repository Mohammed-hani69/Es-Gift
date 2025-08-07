import json
from flask import current_app
from send_by_hostinger import send_order_confirmation, send_custom_email, send_email
from models import Currency, db
from datetime import datetime
import time
import random

def generate_order_number():
    """توليد رقم طلب فريد"""
    timestamp = str(int(time.time()))
    random_num = str(random.randint(1000, 9999))
    return f"ES{timestamp}{random_num}"

def log_action(user_id, action_type, description=""):
    """تسجيل إجراء المستخدم في قاعدة البيانات"""
    try:
        print(f"📝 تسجيل إجراء: المستخدم {user_id} - {action_type} - {description}")
        return True
    except Exception as e:
        print(f"❌ خطأ في تسجيل الإجراء: {str(e)}")
        return False

def to_json_filter(obj):
    """تحويل الكائن إلى JSON"""
    return json.dumps(obj, default=str, ensure_ascii=False)

def get_user_price(product, user_type='regular', user=None):
    """احصل على السعر المناسب للمستخدم مع دعم الأسعار المخصصة"""
    
    # التحقق من صحة المعاملات
    if not product:
        return None
    
    # تحديد نوع المستخدم بدقة
    if user and user.is_authenticated:
        # استخدام customer_type من المستخدم مباشرة إذا كان متوفراً
        if hasattr(user, 'customer_type') and user.customer_type:
            user_type = user.customer_type
        # التحقق من حالة KYC
        elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
            user_type = 'kyc'
    
    # إذا كان المنتج يحتوي على أسعار مخصصة والمستخدم مسجل
    if product.has_custom_pricing and user and user.is_authenticated:
        # البحث عن سعر مخصص للمستخدم
        from models import ProductCustomPrice
        custom_price = ProductCustomPrice.query.filter_by(
            product_id=product.id,
            user_id=user.id
        ).first()
        
        if custom_price:
            # اختيار السعر المناسب حسب نوع المستخدم
            if user_type == 'kyc' and custom_price.kyc_price:
                return custom_price.kyc_price
            elif custom_price.regular_price:
                return custom_price.regular_price
            elif custom_price.custom_price:
                return custom_price.custom_price
    
    # الأسعار العادية مع التحقق من وجود السعر
    if user_type == 'reseller' and product.reseller_price is not None:
        return product.reseller_price
    elif user_type == 'kyc' and product.kyc_price is not None:
        return product.kyc_price
    elif product.regular_price is not None:
        return product.regular_price
    
    # في حالة عدم وجود أي سعر، إرجاع 0 كقيمة افتراضية آمنة
    return 0

def convert_currency(amount, from_currency='SAR', to_currency='SAR'):
    """تحويل العملة مع معالجة شاملة للأخطاء"""
    # التحقق من صحة المبلغ
    if amount is None:
        return 0
    
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
    """إرسال بريد إلكتروني باستخدام Email Sender Pro API"""
    try:
        # استخدام خدمة Email Sender Pro المتكاملة
        success, message = send_custom_email(to_email, subject, body)
        
        if success:
            print(f"✅ تم إرسال الإيميل بنجاح إلى: {to_email} باستخدام Email Sender Pro")
            return True
        else:
            print(f"❌ فشل في إرسال الإيميل باستخدام Email Sender Pro: {message}")
            
            # كبديل، محاولة استخدام Flask-Mail التقليدي
            return _send_email_fallback(to_email, subject, body)
            
    except Exception as e:
        print(f"خطأ في إرسال الإيميل: {e}")
        # محاولة استخدام الطريقة التقليدية كبديل
        return _send_email_fallback(to_email, subject, body)

def _send_email_fallback(to_email, subject, body):
    """إرسال بريد إلكتروني باستخدام Flask-Mail (كبديل)"""
    try:
        from flask_mail import Mail, Message
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
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[to_email]
        )
        msg.html = body
        mail.send(msg)
        print(f"تم إرسال الإيميل بنجاح إلى: {to_email} باستخدام Flask-Mail")
        return True
    except Exception as e:
        print(f"خطأ في إرسال الإيميل باستخدام Flask-Mail: {e}")
        print("نصائح لحل المشكلة:")
        print("1. تأكد من تكوين إعدادات Email Sender Pro بشكل صحيح")
        print("2. تحقق من صحة API Key")
        print("3. تأكد من الاتصال بالإنترنت")
        return False

def send_order_email(order):
    """إرسال بريد إلكتروني بتفاصيل الطلب والأكواد باستخدام Email Sender Pro API"""
    from models import ProductCode
    
    codes = ProductCode.query.filter_by(order_id=order.id).all()
    
    # تحضير بيانات الطلب
    try:
        # محاولة استخدام Email Sender Pro API
        success, message = send_order_confirmation(
            email=order.user.email,
            order_number=order.order_number,
            customer_name=order.user.full_name or order.user.username or 'عزيزي العميل',
            total_amount=str(float(order.total_amount)),
            order_date=order.created_at.strftime('%Y-%m-%d') if order.created_at else None
        )
        
        if success:
            print(f"تم إرسال إيميل تأكيد الطلب #{order.order_number} باستخدام Email Sender Pro")
            return True
        else:
            print(f"فشل إرسال إيميل الطلب باستخدام Email Sender Pro: {message}")
            
    except Exception as e:
        print(f"خطأ في استخدام Email Sender Pro: {str(e)}")
    
    # استخدام الطريقة التقليدية كبديل
    
    email_body = f"""
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; direction: rtl;">
        <div style="background: linear-gradient(135deg, #FF0033 0%, #CC0029 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="margin: 0; font-size: 1.8em;">🎁 ES-GIFT</h1>
            <h2 style="margin: 10px 0 0 0; font-weight: normal;">تأكيد طلبك #{order.order_number}</h2>
        </div>
        
        <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
            <p style="font-size: 1.2em; color: #333; margin-bottom: 20px;">عزيزي العميل،</p>
            <p style="color: #666; line-height: 1.6;">تم إتمام طلبك بنجاح. إليك تفاصيل المنتجات والأكواد:</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
    """
    
    for code in codes:
        email_body += f"""
        <div style="margin-bottom: 20px; padding: 20px; background-color: white; border-radius: 8px; border-right: 4px solid #FF0033;">
            <h3 style="color: #FF0033; margin: 0 0 10px 0;">{code.product.name}</h3>
            <div style="background: #f1f1f1; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 1.1em; margin: 10px 0;">
                <strong style="color: #333;">الكود:</strong> <span style="color: #FF0033; font-weight: bold;">{code.code}</span>
            </div>
            {f'<p style="color: #666; margin: 10px 0;"><strong>التعليمات:</strong> {code.product.instructions}</p>' if code.product.instructions else ''}
        </div>
        """
    
    email_body += f"""
            </div>
            
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin: 30px 0;">
                <h3 style="margin: 0 0 10px 0;">💰 ملخص الطلب</h3>
                <p style="margin: 5px 0; font-size: 1.1em;">المجموع: <strong>{order.total_amount} {order.currency or 'SAR'}</strong></p>
                <p style="margin: 5px 0; opacity: 0.9;">تاريخ الطلب: {order.created_at.strftime('%Y/%m/%d %H:%M') if order.created_at else 'غير محدد'}</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <p style="color: #FF0033; font-size: 1.1em; font-weight: bold;">🎉 شكراً لك على الشراء من ES-GIFT</p>
                <p style="color: #666;">نتمنى لك تجربة ممتعة مع منتجاتنا</p>
            </div>
            
            <div style="border-top: 1px solid #eee; padding-top: 20px; text-align: center; color: #999; font-size: 0.9em;">
                <p>إذا كان لديك أي استفسار، لا تتردد في التواصل معنا</p>
                <p>© 2024 ES-GIFT. جميع الحقوق محفوظة</p>
            </div>
        </div>
    </div>
    """
    
    return send_email(order.user.email, f"🎁 تأكيد طلبك #{order.order_number} - ES-GIFT", email_body)

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

def update_user_prices_in_session(user):
    """تحديث أسعار المنتجات في الجلسة بعد ترقية المستخدم"""
    from flask import session
    
    try:
        cart = session.get('cart', {})
        if cart:
            # تحديث أسعار المنتجات في السلة
            from models import Product
            for product_id in cart.keys():
                product = Product.query.get(int(product_id))
                if product:
                    # تحديث السعر في الجلسة إذا لزم الأمر
                    new_price = get_user_price(product, user.customer_type, user)
                    # يمكن حفظ السعر الجديد في الجلسة أو قاعدة البيانات حسب الحاجة
        
        # إجبار تحديث الصفحة أو إشعار المستخدم
        session['price_update_needed'] = True
        return True
        
    except Exception as e:
        print(f"خطأ في تحديث أسعار المستخدم: {e}")
        return False

def refresh_user_data(user):
    """تحديث بيانات المستخدم وإعادة تحميل الجلسة"""
    from flask import session
    try:
        # إعادة تحميل بيانات المستخدم من قاعدة البيانات
        db.session.refresh(user)
        
        # تحديث أسعار المنتجات
        update_user_prices_in_session(user)
        
        # تسجيل تحديث الأسعار
        session['user_type_updated'] = True
        session['last_price_update'] = datetime.utcnow().isoformat()
        session['force_price_refresh'] = True  # إجبار تحديث الأسعار
        
        # إضافة إشارة لتحديث الأسعار في الواجهة الأمامية
        session['show_price_update_notification'] = True
        session['price_update_message'] = f'تم تحديث الأسعار وفقاً لنوع العميل الجديد: {get_customer_type_display_name(user.customer_type)}'
        
        return True
    except Exception as e:
        print(f"خطأ في تحديث بيانات المستخدم: {e}")
        return False

def get_customer_type_display_name(customer_type):
    """الحصول على اسم نوع العميل للعرض"""
    types = {
        'regular': 'عميل عادي',
        'kyc': 'عميل موثق',
        'reseller': 'موزع'
    }
    return types.get(customer_type, customer_type)

def send_order_confirmation_without_codes(order_data, available_codes=None, products_without_codes=None):
    """إرسال إيميل تأكيد الطلب بدون أكواد (في انتظار الأكواد)"""
    try:
        # تحديد حالة الطلب
        if not available_codes and not products_without_codes:
            status_message = "طلبك قيد المراجعة وسيتم إرسال الأكواد فور توفرها"
        elif available_codes and products_without_codes:
            status_message = f"تم توفير {len(available_codes)} كود من أصل {len(available_codes) + len(products_without_codes)} المطلوبة"
        else:
            status_message = "طلبك تحت المعالجة وسيتم إرسال الأكواد قريباً"
        
        # إرسال البريد الإلكتروني باستخدام Email Sender Pro
        custom_message = f"""
        تم تأكيد طلبك رقم {order_data.get('order_number', 'N/A')} بنجاح.
        
        تفاصيل الطلب:
        - رقم الطلب: {order_data.get('order_number', 'N/A')}
        - المبلغ الإجمالي: {order_data.get('total_amount', 'N/A')} {order_data.get('currency', 'SAR')}
        - التاريخ: {order_data.get('order_date', 'N/A')}
        
        حالة الطلب: {status_message}
        
        شكراً لثقتك في ES-GIFT
        """
        
        success, result = send_custom_email(
            email=order_data.get('customer_email', ''),
            subject=f"تأكيد طلبك #{order_data.get('order_number', 'N/A')} - ES-GIFT",
            message_content=custom_message,
            message_title="تأكيد الطلب"
        )
        
        if success:
            print(f"✅ تم إرسال إيميل تأكيد الطلب #{order_data.get('order_number', 'N/A')} بنجاح")
            return True, "تم إرسال إيميل التأكيد بنجاح"
        else:
            print(f"❌ فشل إرسال إيميل التأكيد: {result}")
            return False, f"فشل إرسال الإيميل: {result}"
            
    except Exception as e:
        error_msg = f"خطأ في إرسال إيميل التأكيد: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg
