#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف إعداد نظام إدارة الموظفين
يقوم بإضافة الصلاحيات والأدوار الأساسية للنظام
"""

from app import app, db
from models import Permission, Role, RolePermission, Employee

def init_permissions():
    """إضافة الصلاحيات الأساسية للنظام"""
    permissions_data = [
        # إدارة المستخدمين
        {'name': 'users.read', 'display_name': 'عرض المستخدمين', 'category': 'users', 'description': 'إمكانية عرض قائمة المستخدمين'},
        {'name': 'users.create', 'display_name': 'إضافة مستخدمين', 'category': 'users', 'description': 'إمكانية إضافة مستخدمين جدد'},
        {'name': 'users.update', 'display_name': 'تعديل المستخدمين', 'category': 'users', 'description': 'إمكانية تعديل بيانات المستخدمين'},
        {'name': 'users.delete', 'display_name': 'حذف المستخدمين', 'category': 'users', 'description': 'إمكانية حذف المستخدمين'},
        
        # إدارة المنتجات
        {'name': 'products.read', 'display_name': 'عرض المنتجات', 'category': 'products', 'description': 'إمكانية عرض قائمة المنتجات'},
        {'name': 'products.create', 'display_name': 'إضافة منتجات', 'category': 'products', 'description': 'إمكانية إضافة منتجات جديدة'},
        {'name': 'products.update', 'display_name': 'تعديل المنتجات', 'category': 'products', 'description': 'إمكانية تعديل بيانات المنتجات'},
        {'name': 'products.delete', 'display_name': 'حذف المنتجات', 'category': 'products', 'description': 'إمكانية حذف المنتجات'},
        
        # إدارة الطلبات
        {'name': 'orders.read', 'display_name': 'عرض الطلبات', 'category': 'orders', 'description': 'إمكانية عرض قائمة الطلبات'},
        {'name': 'orders.update', 'display_name': 'تعديل الطلبات', 'category': 'orders', 'description': 'إمكانية تعديل حالة الطلبات'},
        {'name': 'orders.delete', 'display_name': 'إلغاء الطلبات', 'category': 'orders', 'description': 'إمكانية إلغاء الطلبات'},
        
        # إدارة التصنيفات
        {'name': 'categories.read', 'display_name': 'عرض التصنيفات', 'category': 'categories', 'description': 'إمكانية عرض التصنيفات'},
        {'name': 'categories.create', 'display_name': 'إضافة تصنيفات', 'category': 'categories', 'description': 'إمكانية إضافة تصنيفات جديدة'},
        {'name': 'categories.update', 'display_name': 'تعديل التصنيفات', 'category': 'categories', 'description': 'إمكانية تعديل التصنيفات'},
        {'name': 'categories.delete', 'display_name': 'حذف التصنيفات', 'category': 'categories', 'description': 'إمكانية حذف التصنيفات'},
        
        # إدارة العملات
        {'name': 'currencies.read', 'display_name': 'عرض العملات', 'category': 'currencies', 'description': 'إمكانية عرض العملات'},
        {'name': 'currencies.create', 'display_name': 'إضافة عملات', 'category': 'currencies', 'description': 'إمكانية إضافة عملات جديدة'},
        {'name': 'currencies.update', 'display_name': 'تعديل العملات', 'category': 'currencies', 'description': 'إمكانية تعديل أسعار العملات'},
        {'name': 'currencies.delete', 'display_name': 'حذف العملات', 'category': 'currencies', 'description': 'إمكانية حذف العملات'},
        
        # التقارير والإحصائيات
        {'name': 'reports.read', 'display_name': 'عرض التقارير', 'category': 'reports', 'description': 'إمكانية عرض التقارير والإحصائيات'},
        
        # إدارة الموظفين
        {'name': 'employees.read', 'display_name': 'عرض الموظفين', 'category': 'employees', 'description': 'إمكانية عرض قائمة الموظفين'},
        {'name': 'employees.create', 'display_name': 'إضافة موظفين', 'category': 'employees', 'description': 'إمكانية إضافة موظفين جدد'},
        {'name': 'employees.update', 'display_name': 'تعديل الموظفين', 'category': 'employees', 'description': 'إمكانية تعديل بيانات الموظفين'},
        {'name': 'employees.delete', 'display_name': 'حذف الموظفين', 'category': 'employees', 'description': 'إمكانية حذف الموظفين'},
        
        # إدارة الأدوار
        {'name': 'roles.read', 'display_name': 'عرض الأدوار', 'category': 'roles', 'description': 'إمكانية عرض الأدوار'},
        {'name': 'roles.create', 'display_name': 'إضافة أدوار', 'category': 'roles', 'description': 'إمكانية إضافة أدوار جديدة'},
        {'name': 'roles.update', 'display_name': 'تعديل الأدوار', 'category': 'roles', 'description': 'إمكانية تعديل الأدوار'},
        {'name': 'roles.delete', 'display_name': 'حذف الأدوار', 'category': 'roles', 'description': 'إمكانية حذف الأدوار'},
        
        # إعدادات النظام
        {'name': 'system.settings', 'display_name': 'إعدادات النظام', 'category': 'system', 'description': 'إمكانية الوصول لإعدادات النظام'},
        {'name': 'system.api_settings', 'display_name': 'إعدادات API', 'category': 'system', 'description': 'إمكانية تعديل إعدادات API'},
        {'name': 'system.backup', 'display_name': 'النسخ الاحتياطي', 'category': 'system', 'description': 'إمكانية إجراء نسخ احتياطي'},
        
        # الصفحة الرئيسية والمحتوى
        {'name': 'homepage.manage', 'display_name': 'إدارة الصفحة الرئيسية', 'category': 'content', 'description': 'إمكانية إدارة محتوى الصفحة الرئيسية'},
        {'name': 'articles.manage', 'display_name': 'إدارة المقالات', 'category': 'content', 'description': 'إمكانية إدارة المقالات والمحتوى'},
    ]
    
    for perm_data in permissions_data:
        existing = Permission.query.filter_by(name=perm_data['name']).first()
        if not existing:
            permission = Permission(**perm_data)
            db.session.add(permission)
            print(f"تم إضافة الصلاحية: {perm_data['display_name']}")
    
    db.session.commit()
    print("تم إضافة جميع الصلاحيات الأساسية")

def init_roles():
    """إضافة الأدوار الأساسية للنظام"""
    roles_data = [
        {
            'name': 'super_admin',
            'display_name': 'مدير عام',
            'description': 'مدير عام مع صلاحية كاملة على النظام',
            'is_admin': True
        },
        {
            'name': 'admin',
            'display_name': 'مدير',
            'description': 'مدير مع صلاحيات واسعة',
            'is_admin': True
        },
        {
            'name': 'products_manager',
            'display_name': 'مدير المنتجات',
            'description': 'مسؤول عن إدارة المنتجات والتصنيفات',
            'is_admin': False
        },
        {
            'name': 'orders_manager',
            'display_name': 'مدير الطلبات',
            'description': 'مسؤول عن متابعة ومعالجة الطلبات',
            'is_admin': False
        },
        {
            'name': 'customer_service',
            'display_name': 'خدمة العملاء',
            'description': 'موظف خدمة عملاء',
            'is_admin': False
        },
        {
            'name': 'accountant',
            'display_name': 'محاسب',
            'description': 'مسؤول عن التقارير المالية والعملات',
            'is_admin': False
        },
        {
            'name': 'content_manager',
            'display_name': 'مدير المحتوى',
            'description': 'مسؤول عن إدارة المحتوى والمقالات',
            'is_admin': False
        }
    ]
    
    for role_data in roles_data:
        existing = Role.query.filter_by(name=role_data['name']).first()
        if not existing:
            role = Role(**role_data)
            db.session.add(role)
            print(f"تم إضافة الدور: {role_data['display_name']}")
    
    db.session.commit()
    print("تم إضافة جميع الأدوار الأساسية")

def assign_role_permissions():
    """ربط الأدوار بالصلاحيات المناسبة"""
    
    # الحصول على الأدوار والصلاحيات
    super_admin = Role.query.filter_by(name='super_admin').first()
    admin = Role.query.filter_by(name='admin').first()
    products_manager = Role.query.filter_by(name='products_manager').first()
    orders_manager = Role.query.filter_by(name='orders_manager').first()
    customer_service = Role.query.filter_by(name='customer_service').first()
    accountant = Role.query.filter_by(name='accountant').first()
    content_manager = Role.query.filter_by(name='content_manager').first()
    
    # المدير العام - جميع الصلاحيات
    if super_admin:
        all_permissions = Permission.query.all()
        for permission in all_permissions:
            existing = RolePermission.query.filter_by(role_id=super_admin.id, permission_id=permission.id).first()
            if not existing:
                role_perm = RolePermission(role_id=super_admin.id, permission_id=permission.id)
                db.session.add(role_perm)
        print("تم منح المدير العام جميع الصلاحيات")
    
    # مدير - معظم الصلاحيات ماعدا إدارة الموظفين والأدوار
    if admin:
        admin_permissions = [
            'users.view', 'users.create', 'users.edit', 'users.approve_kyc',
            'products.view', 'products.create', 'products.edit', 'products.manage_pricing',
            'orders.view', 'orders.edit', 'orders.cancel', 'orders.refund',
            'categories.view', 'categories.create', 'categories.edit',
            'currencies.view', 'currencies.edit',
            'reports.view', 'reports.export',
            'homepage.manage', 'articles.manage'
        ]
        assign_permissions_to_role(admin, admin_permissions)
        print("تم منح المدير الصلاحيات المناسبة")
    
    # مدير المنتجات
    if products_manager:
        product_permissions = [
            'products.view', 'products.create', 'products.edit', 'products.manage_pricing',
            'categories.view', 'categories.create', 'categories.edit',
            'users.view'
        ]
        assign_permissions_to_role(products_manager, product_permissions)
        print("تم منح مدير المنتجات الصلاحيات المناسبة")
    
    # مدير الطلبات
    if orders_manager:
        order_permissions = [
            'orders.view', 'orders.edit', 'orders.cancel', 'orders.refund',
            'users.view', 'products.view',
            'reports.view'
        ]
        assign_permissions_to_role(orders_manager, order_permissions)
        print("تم منح مدير الطلبات الصلاحيات المناسبة")
    
    # خدمة العملاء
    if customer_service:
        cs_permissions = [
            'users.view', 'users.edit', 'users.approve_kyc',
            'orders.view', 'orders.edit',
            'products.view'
        ]
        assign_permissions_to_role(customer_service, cs_permissions)
        print("تم منح خدمة العملاء الصلاحيات المناسبة")
    
    # المحاسب
    if accountant:
        accountant_permissions = [
            'orders.view', 'reports.view', 'reports.export',
            'currencies.view', 'currencies.edit',
            'users.view'
        ]
        assign_permissions_to_role(accountant, accountant_permissions)
        print("تم منح المحاسب الصلاحيات المناسبة")
    
    # مدير المحتوى
    if content_manager:
        content_permissions = [
            'homepage.manage', 'articles.manage',
            'categories.view', 'products.view'
        ]
        assign_permissions_to_role(content_manager, content_permissions)
        print("تم منح مدير المحتوى الصلاحيات المناسبة")
    
    db.session.commit()
    print("تم ربط جميع الأدوار بالصلاحيات المناسبة")

def assign_permissions_to_role(role, permission_names):
    """منح صلاحيات محددة لدور معين"""
    for perm_name in permission_names:
        permission = Permission.query.filter_by(name=perm_name).first()
        if permission:
            existing = RolePermission.query.filter_by(role_id=role.id, permission_id=permission.id).first()
            if not existing:
                role_perm = RolePermission(role_id=role.id, permission_id=permission.id)
                db.session.add(role_perm)

def main():
    """دالة رئيسية لتشغيل إعداد النظام"""
    with app.app_context():
        print("بدء إعداد نظام إدارة الموظفين...")
        
        # إضافة الصلاحيات
        print("\n--- إضافة الصلاحيات ---")
        init_permissions()
        
        # إضافة الأدوار
        print("\n--- إضافة الأدوار ---")
        init_roles()
        
        # ربط الأدوار بالصلاحيات
        print("\n--- ربط الأدوار بالصلاحيات ---")
        assign_role_permissions()
        
        print("\n✅ تم إعداد نظام إدارة الموظفين بنجاح!")
        print("يمكنك الآن إضافة موظفين وتخصيص أدوار لهم من لوحة الإدارة")

if __name__ == '__main__':
    main()
