#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مساعدات إدارة المحفظة والحدود المالية
"""

from models import UserLimits, GlobalLimits, WalletTransaction, UserBalance, User, Currency, UserWallet, db
from datetime import datetime, date
from decimal import Decimal

def get_or_create_wallet(user):
    """الحصول على محفظة المستخدم أو إنشاؤها"""
    wallet = UserWallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        # تحديد نوع المستخدم للحصول على الحدود الافتراضية
        if hasattr(user, 'user_type') and user.user_type == 'distributor':
            user_type = 'distributor'
        elif hasattr(user, 'user_type') and user.user_type == 'reseller':
            user_type = 'reseller'
        elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
            user_type = 'reseller'
        elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
            user_type = 'kyc'
        elif hasattr(user, 'customer_type') and user.customer_type == 'regular':
            user_type = 'regular'
        else:
            user_type = 'regular'
        
        # الحصول على الحدود الافتراضية من GlobalLimits
        global_limit = GlobalLimits.query.filter_by(user_type=user_type, is_active=True).first()
        
        if global_limit:
            wallet = UserWallet(
                user_id=user.id,
                daily_limit=global_limit.daily_limit_usd,
                monthly_limit=global_limit.monthly_limit_usd
            )
        else:
            # إنشاء محفظة بحدود افتراضية
            wallet = UserWallet(
                user_id=user.id,
                daily_limit=Decimal('100.00'),
                monthly_limit=Decimal('2000.00')
            )
        
        db.session.add(wallet)
        db.session.commit()
    
    return wallet

def get_currency_rate(from_currency, to_currency='USD'):
    """الحصول على سعر صرف العملة"""
    if from_currency == to_currency:
        return 1.0
    
    try:
        from_currency_obj = Currency.query.filter_by(code=from_currency, is_active=True).first()
        to_currency_obj = Currency.query.filter_by(code=to_currency, is_active=True).first()
        
        if not from_currency_obj or not to_currency_obj:
            return 1.0
        
        # حساب معدل التحويل - تحويل جميع القيم إلى float
        if from_currency == 'SAR':
            return float(to_currency_obj.exchange_rate)
        elif to_currency == 'SAR':
            return 1.0 / float(from_currency_obj.exchange_rate)
        else:
            # تحويل عبر الريال السعودي
            from_rate = float(from_currency_obj.exchange_rate)
            to_rate = float(to_currency_obj.exchange_rate)
            return to_rate / from_rate
            
    except Exception as e:
        print(f"خطأ في جلب سعر الصرف: {e}")
        return 1.0

def get_user_limits(user_id):
    """الحصول على حدود المستخدم"""
    user_limits = UserLimits.query.filter_by(user_id=user_id).first()
    
    if not user_limits:
        # إنشاء حدود جديدة للمستخدم
        user = User.query.get(user_id)
        if user:
            user_limits = create_user_limits(user)
    
    return user_limits

def ensure_default_limits_exist():
    """التأكد من وجود الحدود الافتراضية في قاعدة البيانات"""
    default_limits = [
        {
            'user_type': 'normal',
            'display_name': 'عميل عادي',
            'daily_limit_usd': 1000.00,
            'monthly_limit_usd': 10000.00,
            'description': 'الحدود الافتراضية للعملاء العاديين'
        },
        {
            'user_type': 'regular',
            'display_name': 'عميل عادي',
            'daily_limit_usd': 2000.00,
            'monthly_limit_usd': 20000.00,
            'description': 'الحدود الافتراضية للعملاء العاديين المسجلين'
        },
        {
            'user_type': 'kyc',
            'display_name': 'عميل موثق (KYC)',
            'daily_limit_usd': 5000.00,
            'monthly_limit_usd': 50000.00,
            'description': 'الحدود الافتراضية للعملاء الموثقين'
        },
        {
            'user_type': 'distributor',
            'display_name': 'موزع',
            'daily_limit_usd': 20000.00,
            'monthly_limit_usd': 200000.00,
            'description': 'الحدود الافتراضية للموزعين'
        },
        {
            'user_type': 'reseller',
            'display_name': 'موزع',
            'daily_limit_usd': 15000.00,
            'monthly_limit_usd': 150000.00,
            'description': 'الحدود الافتراضية لبائعي التجزئة'
        }
    ]
    
    for limit_data in default_limits:
        existing_limit = GlobalLimits.query.filter_by(user_type=limit_data['user_type']).first()
        if not existing_limit:
            new_limit = GlobalLimits(
                user_type=limit_data['user_type'],
                display_name=limit_data['display_name'],
                daily_limit_usd=limit_data['daily_limit_usd'],
                monthly_limit_usd=limit_data['monthly_limit_usd'],
                description=limit_data['description'],
                is_active=True
            )
            db.session.add(new_limit)
    
    db.session.commit()

def create_user_limits(user):
    """إنشاء حدود جديدة للمستخدم بناءً على نوعه"""
    # التأكد من وجود الحدود الافتراضية
    ensure_default_limits_exist()
    
    # التحقق من عدم وجود حدود مسبقة للمستخدم
    existing_limits = UserLimits.query.filter_by(user_id=user.id).first()
    if existing_limits:
        return existing_limits
    
    # تحديد نوع المستخدم
    if hasattr(user, 'user_type') and user.user_type == 'distributor':
        user_type = 'distributor'
    elif hasattr(user, 'user_type') and user.user_type == 'reseller':
        user_type = 'reseller'
    elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
        user_type = 'reseller'
    elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
        user_type = 'kyc'
    elif hasattr(user, 'user_type') and user.user_type == 'regular':
        user_type = 'regular'
    else:
        # للمستخدمين الجدد، استخدم النوع 'normal' كافتراضي
        user_type = 'normal'
    
    # الحصول على الحدود الافتراضية
    global_limit = GlobalLimits.query.filter_by(user_type=user_type, is_active=True).first()
    
    # إذا لم توجد حدود افتراضية لهذا النوع، استخدم الحدود العادية
    if not global_limit:
        global_limit = GlobalLimits.query.filter_by(user_type='normal', is_active=True).first()
    
    # إذا لم توجد حدود 'normal'، إنشاء حدود افتراضية
    if not global_limit:
        global_limit = GlobalLimits(
            user_type='normal',
            display_name='عميل عادي',
            daily_limit_usd=1000.00,
            monthly_limit_usd=10000.00,
            description='الحدود الافتراضية للعملاء العاديين',
            is_active=True
        )
        db.session.add(global_limit)
        db.session.flush()
    
    # إنشاء حدود المستخدم
    user_limits = UserLimits(
        user_id=user.id,
        daily_limit_usd=global_limit.daily_limit_usd,
        monthly_limit_usd=global_limit.monthly_limit_usd,
        daily_spent_usd=0.00,
        monthly_spent_usd=0.00,
        is_custom=False
    )
    db.session.add(user_limits)
    
    return user_limits

def check_spending_limit(user_id, amount_usd):
    """التحقق من إمكانية الشراء ضمن الحدود"""
    user_limits = get_user_limits(user_id)
    if not user_limits:
        return False, "لم يتم العثور على حدود المستخدم"
    
    # إعادة تعيين الحدود إذا لزم الأمر
    reset_limits_if_needed(user_limits)
    
    amount_usd = Decimal(str(amount_usd))
    
    # التحقق من الحد اليومي
    if user_limits.daily_spent_usd + amount_usd > user_limits.daily_limit_usd:
        return False, f"تجاوز الحد اليومي المسموح ({user_limits.daily_limit_usd} دولار)"
    
    # التحقق من الحد الشهري
    if user_limits.monthly_spent_usd + amount_usd > user_limits.monthly_limit_usd:
        return False, f"تجاوز الحد الشهري المسموح ({user_limits.monthly_limit_usd} دولار)"
    
    return True, "ضمن الحدود المسموحة"

def record_spending(user_id, amount_usd, transaction_type='purchase', description=None, reference_id=None, reference_type=None, currency_code='USD', exchange_rate=1.0):
    """تسجيل عملية إنفاق"""
    user_limits = get_user_limits(user_id)
    if not user_limits:
        return False
    
    amount_usd = Decimal(str(amount_usd))
    
    # تحديث المبالغ المنفقة
    user_limits.daily_spent_usd += amount_usd
    user_limits.monthly_spent_usd += amount_usd
    
    # إنشاء سجل المعاملة
    transaction = WalletTransaction(
        user_id=user_id,
        transaction_type=transaction_type,
        amount_usd=amount_usd,
        amount_original=amount_usd / Decimal(str(exchange_rate)),
        currency_code=currency_code,
        exchange_rate=Decimal(str(exchange_rate)),
        description=description,
        reference_id=reference_id,
        reference_type=reference_type,
        status='completed'
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return True

def reset_limits_if_needed(user_limits):
    """إعادة تعيين الحدود اليومية والشهرية إذا لزم الأمر"""
    today = date.today()
    
    # إعادة تعيين الحد اليومي
    if user_limits.last_daily_reset != today:
        user_limits.daily_spent_usd = 0.00
        user_limits.last_daily_reset = today
    
    # إعادة تعيين الحد الشهري (في أول يوم من الشهر)
    if user_limits.last_monthly_reset.month != today.month or user_limits.last_monthly_reset.year != today.year:
        user_limits.monthly_spent_usd = 0.00
        user_limits.last_monthly_reset = today
    
    db.session.commit()

def get_user_spending_summary(user_id):
    """الحصول على ملخص إنفاق المستخدم"""
    user_limits = get_user_limits(user_id)
    if not user_limits:
        return None
    
    reset_limits_if_needed(user_limits)
    
    # حساب النسب المئوية
    daily_percentage = float((user_limits.daily_spent_usd / user_limits.daily_limit_usd) * 100) if user_limits.daily_limit_usd > 0 else 0
    monthly_percentage = float((user_limits.monthly_spent_usd / user_limits.monthly_limit_usd) * 100) if user_limits.monthly_limit_usd > 0 else 0
    
    return {
        'daily_limit': float(user_limits.daily_limit_usd),
        'daily_spent': float(user_limits.daily_spent_usd),
        'daily_remaining': float(user_limits.daily_limit_usd - user_limits.daily_spent_usd),
        'daily_percentage': daily_percentage,
        
        'monthly_limit': float(user_limits.monthly_limit_usd),
        'monthly_spent': float(user_limits.monthly_spent_usd),
        'monthly_remaining': float(user_limits.monthly_limit_usd - user_limits.monthly_spent_usd),
        'monthly_percentage': monthly_percentage,
        
        'is_custom': user_limits.is_custom,
        'notes': user_limits.notes
    }

def update_user_limits(user_id, daily_limit=None, monthly_limit=None, notes=None, admin_id=None):
    """تحديث حدود المستخدم"""
    user_limits = get_user_limits(user_id)
    if not user_limits:
        return False
    
    if daily_limit is not None:
        user_limits.daily_limit_usd = Decimal(str(daily_limit))
        user_limits.is_custom = True
    
    if monthly_limit is not None:
        user_limits.monthly_limit_usd = Decimal(str(monthly_limit))
        user_limits.is_custom = True
    
    if notes is not None:
        user_limits.notes = notes
    
    user_limits.updated_at = datetime.utcnow()
    
    # تسجيل المعاملة
    if admin_id:
        transaction = WalletTransaction(
            user_id=user_id,
            transaction_type='limit_update',
            amount_usd=0.00,
            amount_original=0.00,
            currency_code='USD',
            exchange_rate=1.0,
            description=f"تحديث الحدود - يومي: {daily_limit}, شهري: {monthly_limit}",
            reference_type='admin_update',
            status='completed'
        )
        db.session.add(transaction)
    
    db.session.commit()
    return True

def get_user_balance(user_id, currency_code='USD'):
    """الحصول على رصيد المستخدم في عملة معينة"""
    balance = UserBalance.query.filter_by(user_id=user_id, currency_code=currency_code).first()
    
    if not balance:
        # إنشاء رصيد جديد
        balance = UserBalance(
            user_id=user_id,
            currency_code=currency_code,
            balance=0.00
        )
        db.session.add(balance)
        db.session.commit()
    
    return float(balance.balance)

def get_user_wallet_balance(user_id, currency_code='USD'):
    """الحصول على رصيد محفظة المستخدم من جدول user_wallet"""
    try:
        # البحث عن محفظة المستخدم في جدول user_wallet
        wallet = UserWallet.query.filter_by(user_id=user_id).first()
        
        if wallet:
            # إذا كانت عملة المحفظة تطابق العملة المطلوبة
            if wallet.currency == currency_code:
                return float(wallet.balance)
            
            # إذا كانت المحفظة بالدولار والعملة المطلوبة مختلفة، قم بالتحويل
            elif wallet.currency == 'USD' and currency_code != 'USD':
                exchange_rate = get_currency_rate('USD', currency_code)
                converted_balance = float(wallet.balance) * exchange_rate
                return converted_balance
            
            # إذا كانت المحفظة بعملة مختلفة والعملة المطلوبة بالدولار
            elif wallet.currency != 'USD' and currency_code == 'USD':
                exchange_rate = get_currency_rate(wallet.currency, 'USD')
                converted_balance = float(wallet.balance) * exchange_rate
                return converted_balance
            
            # إذا كانت المحفظة والعملة المطلوبة مختلفتان عن الدولار
            else:
                # تحويل عبر الدولار
                usd_rate = get_currency_rate(wallet.currency, 'USD')
                target_rate = get_currency_rate('USD', currency_code)
                converted_balance = float(wallet.balance) * usd_rate * target_rate
                return converted_balance
        
        # إذا لم توجد محفظة، إنشاء واحدة جديدة
        else:
            user = User.query.get(user_id)
            if user:
                new_wallet = get_or_create_wallet(user)
                return float(new_wallet.balance)
        
        # إذا فشل كل شيء، التحقق من النظام القديم UserBalance
        return get_user_balance(user_id, currency_code)
        
    except Exception as e:
        print(f"خطأ في جلب رصيد المحفظة: {e}")
        # في حالة الخطأ، التحقق من النظام القديم
        return get_user_balance(user_id, currency_code)

def deduct_from_wallet(user_id, amount, currency_code='USD', description='Purchase', order_id=None):
    """خصم مبلغ من محفظة المستخدم مع تحويل العملة إلى عملة المحفظة"""
    try:
        # الحصول على محفظة المستخدم
        wallet = UserWallet.query.filter_by(user_id=user_id).first()
        
        if not wallet:
            # إذا لم توجد محفظة، إنشاء واحدة جديدة
            user = User.query.get(user_id)
            if user:
                wallet = get_or_create_wallet(user)
            else:
                return {'success': False, 'message': 'المستخدم غير موجود'}
        
        # تحويل المبلغ إلى عملة المحفظة
        if currency_code != wallet.currency:
            # حساب سعر التحويل من عملة الطلب إلى عملة المحفظة
            exchange_rate = get_currency_rate(currency_code, wallet.currency)
            amount_in_wallet_currency = float(amount) * exchange_rate
            print(f"تحويل {amount} {currency_code} إلى {amount_in_wallet_currency} {wallet.currency}")
        else:
            amount_in_wallet_currency = float(amount)
            exchange_rate = 1.0
        
        # التحقق من كفاية الرصيد
        if float(wallet.balance) < amount_in_wallet_currency:
            deficit = amount_in_wallet_currency - float(wallet.balance)
            return {
                'success': False, 
                'message': f'❌ رصيد المحفظة غير كافي لإتمام العملية!\n\n'
                          f'💰 الرصيد المتاح: {wallet.balance} {wallet.currency}\n'
                          f'💳 المبلغ المطلوب: {amount_in_wallet_currency:.2f} {wallet.currency}\n'
                          f'⚠️ المبلغ الناقص: {deficit:.2f} {wallet.currency}\n\n'
                          f'💡 يمكنك إيداع المبلغ الناقص من خلال الذهاب إلى صفحة المحفظة وطلب إيداع.',
                'error_type': 'insufficient_balance',
                'balance_info': {
                    'current_balance': float(wallet.balance),
                    'required_amount': amount_in_wallet_currency,
                    'deficit': deficit,
                    'currency': wallet.currency
                }
            }
        
        # خصم المبلغ من المحفظة
        balance_before = float(wallet.balance)
        wallet.balance -= Decimal(str(amount_in_wallet_currency))
        
        # تحديث إحصائيات المحفظة
        # تحويل المبلغ إلى الدولار للإحصائيات
        amount_usd = float(amount_in_wallet_currency) * get_currency_rate(wallet.currency, 'USD')
        wallet.total_purchases += Decimal(str(amount_usd))
        
        if order_id:
            wallet.total_orders += 1
        
        wallet.updated_at = datetime.utcnow()
        
        # تسجيل المعاملة
        transaction = WalletTransaction(
            user_id=user_id,
            transaction_type='purchase',
            amount_usd=Decimal(str(amount_usd)),
            amount_original=Decimal(str(amount)),  # المبلغ الأصلي بعملة الطلب
            currency_code=currency_code,  # عملة الطلب الأصلية
            exchange_rate=Decimal(str(exchange_rate)),
            description=description,
            reference_id=str(order_id) if order_id else None,
            reference_type='order' if order_id else 'manual',
            status='completed'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        print(f"✅ تم خصم {amount_in_wallet_currency} {wallet.currency} من المحفظة. الرصيد الجديد: {wallet.balance} {wallet.currency}")
        
        return {
            'success': True, 
            'message': f'تم خصم {amount_in_wallet_currency:.2f} {wallet.currency} من المحفظة بنجاح',
            'new_balance': float(wallet.balance),
            'deducted_amount': amount_in_wallet_currency,
            'wallet_currency': wallet.currency
        }
                
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في خصم المبلغ من المحفظة: {e}")
        return {'success': False, 'message': f'خطأ في خصم المبلغ: {str(e)}'}

def update_user_balance(user_id, currency_code, amount, transaction_type='deposit', description=None):
    """تحديث رصيد المستخدم"""
    balance = UserBalance.query.filter_by(user_id=user_id, currency_code=currency_code).first()
    
    if not balance:
        balance = UserBalance(
            user_id=user_id,
            currency_code=currency_code,
            balance=0.00
        )
        db.session.add(balance)
    
    balance.balance += Decimal(str(amount))
    balance.last_updated = datetime.utcnow()
    
    # تسجيل المعاملة
    exchange_rate = get_currency_rate(currency_code, 'USD') if currency_code != 'USD' else 1.0
    amount_usd = Decimal(str(amount)) * Decimal(str(exchange_rate))
    
    transaction = WalletTransaction(
        user_id=user_id,
        transaction_type=transaction_type,
        amount_usd=amount_usd,
        amount_original=Decimal(str(amount)),
        currency_code=currency_code,
        exchange_rate=Decimal(str(exchange_rate)),
        description=description or f"{transaction_type} - {amount} {currency_code}",
        status='completed'
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return True

def get_user_transactions(user_id, limit=50, offset=0, transaction_type=None):
    """الحصول على معاملات المستخدم"""
    query = WalletTransaction.query.filter_by(user_id=user_id)
    
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    
    transactions = query.order_by(WalletTransaction.created_at.desc()).offset(offset).limit(limit).all()
    
    return [{
        'id': t.id,
        'type': t.transaction_type,
        'amount_usd': float(t.amount_usd),
        'amount_original': float(t.amount_original),
        'currency_code': t.currency_code,
        'exchange_rate': float(t.exchange_rate),
        'description': t.description,
        'status': t.status,
        'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for t in transactions]

def ensure_all_users_have_limits():
    """التأكد من وجود حدود مالية لجميع المستخدمين"""
    try:
        # البحث عن المستخدمين بدون حدود مالية
        users_without_limits = User.query.outerjoin(UserLimits).filter(UserLimits.user_id.is_(None)).all()
        
        if users_without_limits:
            print(f"وجد {len(users_without_limits)} مستخدم بدون حدود مالية، جاري إنشاء الحدود...")
            
            for user in users_without_limits:
                try:
                    create_user_limits(user)
                    print(f"تم إنشاء حدود مالية للمستخدم: {user.email}")
                except Exception as e:
                    print(f"خطأ في إنشاء حدود للمستخدم {user.email}: {str(e)}")
            
            print(f"تم إنشاء حدود مالية لـ {len(users_without_limits)} مستخدم")
        else:
            print("جميع المستخدمين لديهم حدود مالية بالفعل")
            
    except Exception as e:
        print(f"خطأ في ensure_all_users_have_limits: {str(e)}")

def count_users_by_type(user_type):
    """حساب عدد المستخدمين من نوع معين الذين تم تحديث حدودهم"""
    try:
        # البحث في جميع المستخدمين وتحديد نوعهم
        all_users = User.query.all()
        count = 0
        
        for user in all_users:
            # تحديد نوع المستخدم
            if hasattr(user, 'user_type') and user.user_type == 'distributor':
                detected_user_type = 'distributor'
            elif hasattr(user, 'user_type') and user.user_type == 'reseller':
                detected_user_type = 'reseller'
            elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
                detected_user_type = 'reseller'
            elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
                detected_user_type = 'kyc'
            elif hasattr(user, 'user_type') and user.user_type == 'regular':
                detected_user_type = 'regular'
            else:
                detected_user_type = 'normal'
            
            # إذا كان نوع المستخدم يطابق النوع المحدد
            if detected_user_type == user_type:
                # التحقق من وجود حدود افتراضية (غير مخصصة)
                user_limits = UserLimits.query.filter_by(user_id=user.id, is_custom=False).first()
                if user_limits:
                    count += 1
        
        return count
        
    except Exception as e:
        print(f"خطأ في حساب عدد المستخدمين: {str(e)}")
        return 0

def apply_limits_to_existing_users(user_type, daily_limit, monthly_limit):
    """تطبيق الحدود على العملاء الموجودين من نفس النوع"""
    try:
        from decimal import Decimal
        
        # البحث في جميع المستخدمين وتحديد نوعهم
        all_users = User.query.all()
        users_to_update = []
        
        for user in all_users:
            # تحديد نوع المستخدم
            if hasattr(user, 'user_type') and user.user_type == 'distributor':
                detected_user_type = 'distributor'
            elif hasattr(user, 'user_type') and user.user_type == 'reseller':
                detected_user_type = 'reseller'
            elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
                detected_user_type = 'reseller'
            elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
                detected_user_type = 'kyc'
            elif hasattr(user, 'user_type') and user.user_type == 'regular':
                detected_user_type = 'regular'
            else:
                detected_user_type = 'normal'
            
            # إذا كان نوع المستخدم يطابق النوع المحدد
            if detected_user_type == user_type:
                users_to_update.append(user.id)
        
        # تحديث أو إنشاء حدود للمستخدمين
        updated_count = 0
        for user_id in users_to_update:
            user_limits = UserLimits.query.filter_by(user_id=user_id).first()
            
            if user_limits:
                # تحديث الحدود الموجودة فقط إذا كانت افتراضية
                if not user_limits.is_custom:
                    user_limits.daily_limit_usd = Decimal(str(daily_limit))
                    user_limits.monthly_limit_usd = Decimal(str(monthly_limit))
                    updated_count += 1
            else:
                # إنشاء حدود جديدة
                new_limits = UserLimits(
                    user_id=user_id,
                    daily_limit_usd=Decimal(str(daily_limit)),
                    monthly_limit_usd=Decimal(str(monthly_limit)),
                    daily_spent_usd=Decimal('0.00'),
                    monthly_spent_usd=Decimal('0.00'),
                    is_custom=False
                )
                db.session.add(new_limits)
                updated_count += 1
        
        db.session.commit()
        
        print(f"تم تطبيق الحدود على {updated_count} عميل من نوع {user_type}")
        return updated_count
        
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في تطبيق الحدود على العملاء الموجودين: {str(e)}")
        return 0

def update_global_limits(user_type, daily_limit, monthly_limit, description=""):
    """تحديث الحدود الافتراضية وتطبيقها على جميع العملاء من نفس النوع"""
    try:
        from decimal import Decimal
        
        # تحديث الحدود الافتراضية
        global_limit = GlobalLimits.query.filter_by(user_type=user_type).first()
        if not global_limit:
            raise ValueError(f"لم يتم العثور على حدود افتراضية لنوع العميل: {user_type}")
        
        global_limit.daily_limit_usd = Decimal(str(daily_limit))
        global_limit.monthly_limit_usd = Decimal(str(monthly_limit))
        global_limit.description = description
        
        # الحصول على جميع المستخدمين من نفس النوع الذين لديهم حدود افتراضية (غير مخصصة)
        users_to_update = []
        
        # البحث في جميع المستخدمين وتحديد نوعهم
        all_users = User.query.all()
        for user in all_users:
            # تحديد نوع المستخدم
            if hasattr(user, 'user_type') and user.user_type == 'distributor':
                detected_user_type = 'distributor'
            elif hasattr(user, 'user_type') and user.user_type == 'reseller':
                detected_user_type = 'reseller'
            elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
                detected_user_type = 'reseller'
            elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
                detected_user_type = 'kyc'
            elif hasattr(user, 'user_type') and user.user_type == 'regular':
                detected_user_type = 'regular'
            else:
                detected_user_type = 'normal'
            
            # إذا كان نوع المستخدم يطابق النوع المحدث
            if detected_user_type == user_type:
                users_to_update.append(user.id)
        
        # تحديث حدود المستخدمين الذين لديهم حدود افتراضية فقط
        updated_count = 0
        for user_id in users_to_update:
            user_limits = UserLimits.query.filter_by(user_id=user_id, is_custom=False).first()
            if user_limits:
                user_limits.daily_limit_usd = Decimal(str(daily_limit))
                user_limits.monthly_limit_usd = Decimal(str(monthly_limit))
                updated_count += 1
        
        db.session.commit()
        
        print(f"تم تحديث الحدود الافتراضية لنوع {user_type} وتطبيقها على {updated_count} عميل")
        return global_limit
        
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في تحديث الحدود الافتراضية: {str(e)}")
        raise e

def get_global_limits():
    """الحصول على جميع الحدود الافتراضية"""
    return GlobalLimits.query.filter_by(is_active=True).all()

def get_users_with_limits_paginated(email_filter='', user_type_filter='', limit_type_filter='', page=1, per_page=50):
    """جلب المستخدمين مع الحدود المالية مع pagination"""
    from models import db, User, UserLimits, GlobalLimits
    from sqlalchemy import func, or_
    
    try:
        # بناء الاستعلام الأساسي
        query = db.session.query(User).join(UserLimits, User.id == UserLimits.user_id)
        
        # تطبيق فلاتر البحث
        if email_filter:
            query = query.filter(User.email.ilike(f'%{email_filter}%'))
        
        if user_type_filter:
            # تحديد نوع المستخدم بناءً على الحقول المختلفة
            if user_type_filter == 'distributor':
                query = query.filter(User.user_type == 'distributor')
            elif user_type_filter == 'reseller':
                query = query.filter(or_(
                    User.user_type == 'reseller',
                    User.customer_type == 'reseller'
                ))
            elif user_type_filter == 'kyc':
                query = query.filter(User.kyc_status == 'approved')
            elif user_type_filter == 'regular':
                query = query.filter(User.user_type == 'regular')
            else:  # normal
                query = query.filter(or_(
                    User.user_type.is_(None),
                    User.user_type == 'normal',
                    User.user_type == ''
                ))
        
        if limit_type_filter == 'has_custom':
            # المستخدمين الذين لديهم حدود مخصصة
            query = query.filter(UserLimits.is_custom == True)
        elif limit_type_filter == 'has_default':
            # المستخدمين الذين لديهم حدود افتراضية فقط
            query = query.filter(or_(
                UserLimits.is_custom == False,
                UserLimits.is_custom.is_(None)
            ))
        
        # حساب العدد الإجمالي
        total_count = query.count()
        
        # تطبيق pagination
        offset = (page - 1) * per_page
        users = query.order_by(User.id.desc()).offset(offset).limit(per_page).all()
        
        # إعداد البيانات مع التفاصيل
        users_data = []
        for user in users:
            user_limits = UserLimits.query.filter_by(user_id=user.id).first()
            
            # تحديد نوع المستخدم
            if hasattr(user, 'user_type') and user.user_type == 'distributor':
                detected_user_type = 'distributor'
            elif hasattr(user, 'user_type') and user.user_type == 'reseller':
                detected_user_type = 'reseller'
            elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
                detected_user_type = 'reseller'
            elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
                detected_user_type = 'kyc'
            elif hasattr(user, 'user_type') and user.user_type == 'regular':
                detected_user_type = 'regular'
            else:
                detected_user_type = 'normal'
            
            # جلب الحدود الافتراضية لنوع المستخدم
            global_limit = GlobalLimits.query.filter_by(user_type=detected_user_type).first()
            default_daily = global_limit.daily_limit_usd if global_limit else 1000
            default_monthly = global_limit.monthly_limit_usd if global_limit else 10000
            
            users_data.append({
                'user': user,
                'limits': user_limits,
                'user_type': detected_user_type,
                'has_custom_limits': user_limits.is_custom if user_limits else False,
                'default_daily': float(default_daily),
                'default_monthly': float(default_monthly)
            })
        
        return users_data, total_count
        
    except Exception as e:
        print(f"خطأ في جلب المستخدمين مع الحدود: {str(e)}")
        return [], 0

def update_global_limits(user_type, daily_limit, monthly_limit, description=None):
    """تحديث الحدود الافتراضية لنوع مستخدم"""
    global_limit = GlobalLimits.query.filter_by(user_type=user_type).first()
    
    if global_limit:
        global_limit.daily_limit_usd = Decimal(str(daily_limit))
        global_limit.monthly_limit_usd = Decimal(str(monthly_limit))
        if description:
            global_limit.description = description
        global_limit.updated_at = datetime.utcnow()
    else:
        global_limit = GlobalLimits(
            user_type=user_type,
            display_name=user_type.title(),
            daily_limit_usd=Decimal(str(daily_limit)),
            monthly_limit_usd=Decimal(str(monthly_limit)),
            description=description,
            is_active=True
        )
        db.session.add(global_limit)
    
    db.session.commit()
    return global_limit

def update_global_limits_and_apply_to_users(user_type, daily_limit, monthly_limit, description=None, apply_to_existing=True):
    """تحديث الحدود الافتراضية وتطبيقها على المستخدمين الموجودين"""
    try:
        from models import db, User, UserLimits, GlobalLimits
        from decimal import Decimal
        from datetime import datetime
        
        # تحديث أو إنشاء الحد الافتراضي
        global_limit = GlobalLimits.query.filter_by(user_type=user_type).first()
        
        if global_limit:
            global_limit.daily_limit_usd = Decimal(str(daily_limit))
            global_limit.monthly_limit_usd = Decimal(str(monthly_limit))
            if description:
                global_limit.description = description
            global_limit.updated_at = datetime.utcnow()
        else:
            global_limit = GlobalLimits(
                user_type=user_type,
                display_name=user_type.title(),
                daily_limit_usd=Decimal(str(daily_limit)),
                monthly_limit_usd=Decimal(str(monthly_limit)),
                description=description,
                is_active=True
            )
            db.session.add(global_limit)
        
        updated_users_count = 0
        
        if apply_to_existing:
            # جلب جميع المستخدمين
            all_users = User.query.all()
            
            for user in all_users:
                # تحديد نوع المستخدم
                if hasattr(user, 'user_type') and user.user_type == 'distributor':
                    detected_user_type = 'distributor'
                elif hasattr(user, 'user_type') and user.user_type == 'reseller':
                    detected_user_type = 'reseller'
                elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
                    detected_user_type = 'reseller'
                elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
                    detected_user_type = 'kyc'
                elif hasattr(user, 'user_type') and user.user_type == 'regular':
                    detected_user_type = 'regular'
                else:
                    detected_user_type = 'normal'
                
                # إذا كان نوع المستخدم يطابق النوع المحدد
                if detected_user_type == user_type:
                    user_limits = UserLimits.query.filter_by(user_id=user.id).first()
                    
                    if user_limits:
                        # تحديث فقط المستخدمين الذين لديهم حدود افتراضية (غير مخصصة)
                        if not user_limits.is_custom:
                            user_limits.daily_spending_limit = Decimal(str(daily_limit))
                            user_limits.monthly_spending_limit = Decimal(str(monthly_limit))
                            user_limits.updated_at = datetime.utcnow()
                            updated_users_count += 1
                    else:
                        # إنشاء حدود جديدة للمستخدم
                        user_limits = UserLimits(
                            user_id=user.id,
                            daily_spending_limit=Decimal(str(daily_limit)),
                            monthly_spending_limit=Decimal(str(monthly_limit)),
                            is_custom=False
                        )
                        db.session.add(user_limits)
                        updated_users_count += 1
        
        db.session.commit()
        
        message = f'تم تحديث الحدود الافتراضية لنوع {user_type} بنجاح'
        if apply_to_existing and updated_users_count > 0:
            message += f' وتم تطبيقها على {updated_users_count} مستخدم'
        
        return {
            'success': True,
            'message': message,
            'updated_users_count': updated_users_count
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'خطأ في التحديث: {str(e)}',
            'updated_users_count': 0
        }
