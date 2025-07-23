# -*- coding: utf-8 -*-
"""
إضافة بيانات النظام المالي والمستخدمين لـ ES-Gift
===============================================

هذا الملف يحتوي على بيانات تجريبية للنظام المالي والمستخدمين وأدوارهم

"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# إضافة مسار المشروع إلى Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# استيراد التطبيق والنماذج
from app import create_app
from models import *
from models import UserLimit, CustomUserPrice, APISetting

def init_user_system_data():
    """إضافة بيانات النظام المالي والمستخدمين"""
    app = create_app()
    
    with app.app_context():
        try:
            print("👥 بدء إضافة بيانات النظام المالي والمستخدمين...")
            
            # 1. إضافة الحدود المالية
            add_user_limits()
            
            # 2. إضافة الموظفين
            add_employees()
            
            # 3. إضافة الأدوار
            add_roles()
            
            # 4. إضافة أسعار مخصصة للمستخدمين
            add_custom_user_prices()
            
            # 5. إضافة طلبات KYC تجريبية
            add_kyc_requests()
            
            # 6. إضافة منتجات API
            add_api_products()
            
            # 7. إضافة إعدادات API
            add_api_settings()
            
            db.session.commit()
            print("✅ تم إضافة جميع بيانات النظام المالي والمستخدمين بنجاح!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في إضافة البيانات: {str(e)}")
            raise

def add_user_limits():
    """إضافة الحدود المالية للمستخدمين"""
    print("💰 إضافة الحدود المالية...")
    
    # جلب أو إنشاء المستخدمين
    admin_user = User.query.filter_by(email='admin@esgift.com').first()
    customer1 = User.query.filter_by(email='customer1@example.com').first()
    vip_customer = User.query.filter_by(email='vip@example.com').first()
    
    limits_data = [
        {
            'user_id': admin_user.id if admin_user else 1,
            'daily_limit': Decimal('10000.00'),
            'monthly_limit': Decimal('100000.00'),
            'transaction_limit': Decimal('5000.00'),
            'is_active': True,
            'notes': 'حدود إدارية عالية'
        },
        {
            'user_id': customer1.id if customer1 else 2,
            'daily_limit': Decimal('1000.00'),
            'monthly_limit': Decimal('10000.00'),
            'transaction_limit': Decimal('500.00'),
            'is_active': True,
            'notes': 'حدود عميل عادي'
        },
        {
            'user_id': vip_customer.id if vip_customer else 3,
            'daily_limit': Decimal('5000.00'),
            'monthly_limit': Decimal('50000.00'),
            'transaction_limit': Decimal('2000.00'),
            'is_active': True,
            'notes': 'حدود عميل VIP'
        }
    ]
    
    for limit_data in limits_data:
        existing = UserLimit.query.filter_by(user_id=limit_data['user_id']).first()
        if not existing:
            limit = UserLimit(**limit_data)
            db.session.add(limit)
            print(f"  ✅ تم إضافة حدود مالية للمستخدم {limit_data['user_id']}")

def add_employees():
    """إضافة الموظفين"""
    print("👨‍💼 إضافة الموظفين...")
    
    from werkzeug.security import generate_password_hash
    
    employees_data = [
        {
            'username': 'manager',
            'email': 'manager@esgift.com',
            'password_hash': generate_password_hash('manager123'),
            'full_name': 'مدير العمليات',
            'phone': '+966502345678',
            'employee_id': 'EMP001',
            'department': 'العمليات',
            'position': 'مدير',
            'hire_date': datetime.now() - timedelta(days=365),
            'salary': Decimal('8000.00'),
            'is_active': True,
            'permissions': {
                'manage_products': True,
                'manage_orders': True,
                'view_reports': True,
                'manage_users': False
            },
            'created_at': datetime.now()
        },
        {
            'username': 'support',
            'email': 'support@esgift.com',
            'password_hash': generate_password_hash('support123'),
            'full_name': 'موظف الدعم الفني',
            'phone': '+966503456789',
            'employee_id': 'EMP002',
            'department': 'الدعم الفني',
            'position': 'موظف دعم',
            'hire_date': datetime.now() - timedelta(days=180),
            'salary': Decimal('4000.00'),
            'is_active': True,
            'permissions': {
                'manage_products': False,
                'manage_orders': True,
                'view_reports': False,
                'manage_users': False
            },
            'created_at': datetime.now()
        },
        {
            'username': 'sales',
            'email': 'sales@esgift.com',
            'password_hash': generate_password_hash('sales123'),
            'full_name': 'موظف المبيعات',
            'phone': '+966504567890',
            'employee_id': 'EMP003',
            'department': 'المبيعات',
            'position': 'أخصائي مبيعات',
            'hire_date': datetime.now() - timedelta(days=90),
            'salary': Decimal('5000.00'),
            'is_active': True,
            'permissions': {
                'manage_products': True,
                'manage_orders': True,
                'view_reports': True,
                'manage_users': False
            },
            'created_at': datetime.now()
        }
    ]
    
    for emp_data in employees_data:
        existing = Employee.query.filter_by(email=emp_data['email']).first()
        if not existing:
            employee = Employee(**emp_data)
            db.session.add(employee)
            print(f"  ✅ تم إضافة موظف: {emp_data['full_name']}")

def add_roles():
    """إضافة الأدوار"""
    print("🛡️ إضافة الأدوار...")
    
    roles_data = [
        {
            'name': 'مدير عام',
            'description': 'صلاحيات كاملة لإدارة النظام',
            'permissions': {
                'admin_access': True,
                'manage_users': True,
                'manage_products': True,
                'manage_orders': True,
                'manage_employees': True,
                'view_reports': True,
                'manage_settings': True,
                'manage_api': True
            },
            'is_active': True
        },
        {
            'name': 'مدير عمليات',
            'description': 'إدارة العمليات والمنتجات والطلبات',
            'permissions': {
                'admin_access': True,
                'manage_users': False,
                'manage_products': True,
                'manage_orders': True,
                'manage_employees': False,
                'view_reports': True,
                'manage_settings': False,
                'manage_api': False
            },
            'is_active': True
        },
        {
            'name': 'موظف دعم',
            'description': 'دعم العملاء وإدارة الطلبات',
            'permissions': {
                'admin_access': True,
                'manage_users': False,
                'manage_products': False,
                'manage_orders': True,
                'manage_employees': False,
                'view_reports': False,
                'manage_settings': False,
                'manage_api': False
            },
            'is_active': True
        },
        {
            'name': 'أخصائي مبيعات',
            'description': 'إدارة المنتجات والتقارير',
            'permissions': {
                'admin_access': True,
                'manage_users': False,
                'manage_products': True,
                'manage_orders': True,
                'manage_employees': False,
                'view_reports': True,
                'manage_settings': False,
                'manage_api': False
            },
            'is_active': True
        }
    ]
    
    for role_data in roles_data:
        existing = Role.query.filter_by(name=role_data['name']).first()
        if not existing:
            role = Role(**role_data)
            db.session.add(role)
            print(f"  ✅ تم إضافة دور: {role_data['name']}")

def add_custom_user_prices():
    """إضافة أسعار مخصصة للمستخدمين"""
    print("💲 إضافة أسعار مخصصة...")
    
    # جلب المنتجات والمستخدمين
    products = Product.query.limit(3).all()
    vip_customer = User.query.filter_by(email='vip@example.com').first()
    admin_user = User.query.filter_by(email='admin@esgift.com').first()
    
    if products and vip_customer:
        for product in products:
            # سعر VIP مخفض بـ 15%
            vip_price = Decimal(str(float(product.regular_price) * 0.85))
            
            custom_price = CustomUserPrice(
                user_id=vip_customer.id,
                product_id=product.id,
                custom_price=vip_price,
                discount_percentage=Decimal('15.00'),
                is_active=True,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=365),
                notes='خصم VIP - 15%'
            )
            db.session.add(custom_price)
            print(f"  ✅ تم إضافة سعر مخصص لـ {product.name}")
    
    if products and admin_user:
        for product in products[:2]:  # أول منتجين فقط
            # سعر إداري مخفض بـ 50%
            admin_price = Decimal(str(float(product.regular_price) * 0.5))
            
            custom_price = CustomUserPrice(
                user_id=admin_user.id,
                product_id=product.id,
                custom_price=admin_price,
                discount_percentage=Decimal('50.00'),
                is_active=True,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=365),
                notes='خصم إداري - 50%'
            )
            db.session.add(custom_price)
            print(f"  ✅ تم إضافة سعر إداري لـ {product.name}")

def add_kyc_requests():
    """إضافة طلبات KYC تجريبية"""
    print("📋 إضافة طلبات KYC...")
    
    customer1 = User.query.filter_by(email='customer1@example.com').first()
    
    if customer1:
        # إنشاء طلب KYC للعميل
        customer1.kyc_status = 'pending'
        customer1.full_name = 'أحمد محمد عبدالله'
        customer1.phone = '+966501234567'
        customer1.nationality = 'سعودي'
        customer1.document_type = 'national_id'
        
        print(f"  ✅ تم تحديث بيانات KYC للعميل: {customer1.full_name}")

def add_api_products():
    """إضافة منتجات API"""
    print("🔌 إضافة منتجات API...")
    
    products = Product.query.limit(3).all()
    
    api_products_data = [
        {
            'product_id': products[0].id if len(products) > 0 else 1,
            'provider': 'onecard',
            'provider_product_id': 'OC_PUBG_60UC',
            'provider_name': 'PUBG Mobile 60 UC',
            'provider_price': Decimal('15.00'),
            'provider_currency': 'SAR',
            'is_active': True,
            'sync_enabled': True,
            'auto_purchase': True,
            'last_sync': datetime.now()
        },
        {
            'product_id': products[1].id if len(products) > 1 else 2,
            'provider': 'onecard',
            'provider_product_id': 'OC_PUBG_300UC',
            'provider_name': 'PUBG Mobile 300 UC',
            'provider_price': Decimal('75.00'),
            'provider_currency': 'SAR',
            'is_active': True,
            'sync_enabled': True,
            'auto_purchase': True,
            'last_sync': datetime.now()
        },
        {
            'product_id': products[2].id if len(products) > 2 else 3,
            'provider': 'manual',
            'provider_product_id': 'MAN_FREEFIRE_100',
            'provider_name': 'Free Fire 100 Diamonds',
            'provider_price': Decimal('20.00'),
            'provider_currency': 'SAR',
            'is_active': True,
            'sync_enabled': False,
            'auto_purchase': False,
            'last_sync': datetime.now()
        }
    ]
    
    for api_data in api_products_data:
        existing = APIProduct.query.filter_by(
            product_id=api_data['product_id'],
            provider=api_data['provider']
        ).first()
        if not existing:
            api_product = APIProduct(**api_data)
            db.session.add(api_product)
            print(f"  ✅ تم إضافة منتج API: {api_data['provider_name']}")

def add_api_settings():
    """إضافة إعدادات API"""
    print("⚙️ إضافة إعدادات API...")
    
    settings_data = [
        {
            'key': 'onecard_api_enabled',
            'value': 'true',
            'description': 'تفعيل OneCard API',
            'category': 'api'
        },
        {
            'key': 'onecard_api_url',
            'value': 'https://api.onecard.com/v1',
            'description': 'رابط OneCard API',
            'category': 'api'
        },
        {
            'key': 'onecard_api_key',
            'value': 'your_api_key_here',
            'description': 'مفتاح OneCard API',
            'category': 'api'
        },
        {
            'key': 'auto_purchase_enabled',
            'value': 'true',
            'description': 'تفعيل الشراء التلقائي',
            'category': 'system'
        },
        {
            'key': 'email_notifications_enabled',
            'value': 'true',
            'description': 'تفعيل إشعارات البريد الإلكتروني',
            'category': 'notifications'
        },
        {
            'key': 'sms_notifications_enabled',
            'value': 'false',
            'description': 'تفعيل إشعارات SMS',
            'category': 'notifications'
        },
        {
            'key': 'currency_auto_update',
            'value': 'true',
            'description': 'تحديث أسعار العملات تلقائياً',
            'category': 'currency'
        },
        {
            'key': 'max_daily_orders',
            'value': '100',
            'description': 'الحد الأقصى للطلبات اليومية',
            'category': 'limits'
        }
    ]
    
    for setting_data in settings_data:
        existing = APISetting.query.filter_by(key=setting_data['key']).first()
        if not existing:
            setting = APISetting(**setting_data)
            db.session.add(setting)
            print(f"  ✅ تم إضافة إعداد: {setting_data['key']}")

if __name__ == '__main__':
    print("💼 نظام إضافة بيانات النظام المالي والمستخدمين")
    print("=" * 60)
    
    confirm = input("هل تريد إضافة بيانات النظام المالي والمستخدمين؟ (y/n): ")
    if confirm.lower() in ['y', 'yes', 'نعم']:
        init_user_system_data()
        print("\n" + "=" * 60)
        print("🎉 تم الانتهاء من إضافة جميع بيانات النظام المالي!")
        print("يمكنك الآن تسجيل الدخول باستخدام الحسابات التجريبية:")
        print("- المدير: admin@esgift.com / admin123")
        print("- العميل: customer1@example.com / customer123") 
        print("- VIP: vip@example.com / vip123")
        print("- المدير: manager@esgift.com / manager123")
        print("- الدعم: support@esgift.com / support123")
    else:
        print("تم إلغاء العملية.")
