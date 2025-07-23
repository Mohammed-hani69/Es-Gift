#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف مساعد لإدارة الموظفين والصلاحيات
"""

import json
from functools import wraps
from flask import abort, current_app, request, jsonify, redirect, url_for, flash
from flask_login import current_user
from models import Employee, Permission, Role, RolePermission, EmployeePermission, ActivityLog, db
from datetime import datetime

def requires_page_access(page_route):
    """
    ديكوريتر للتحقق من صلاحية الوصول للصفحة
    يستخدم لحماية صفحات لوحة التحكم بناءً على الأدوار
    page_route: مسار الصفحة مثل 'admin.products' أو 'admin.users'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # المديرون العامون لهم وصول كامل
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # التحقق من أن المستخدم موظف
            employee = Employee.query.filter_by(user_id=current_user.id).first()
            if not employee:
                flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
                return redirect(url_for('main.index'))
            
            # التحقق من حالة الموظف
            if hasattr(employee, 'status') and employee.status != 'active':
                flash('حسابك الوظيفي غير نشط', 'error')
                return redirect(url_for('main.index'))
            
            # التحقق من صلاحية الوصول للصفحة
            if has_page_access(employee, page_route):
                # تسجيل النشاط
                log_activity(employee, f"page_access", f"وصول للصفحة: {page_route}")
                return f(*args, **kwargs)
            else:
                flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
                return redirect(url_for('admin.dashboard'))
        
        return decorated_function
    return decorator

def has_page_access(employee, page_route):
    """
    التحقق من صلاحية الوصول لصفحة محددة
    """
    if not employee or not employee.role:
        return False
    
    # الأدوار الإدارية لها وصول كامل
    if employee.role.is_admin:
        return True
    
    # التحقق من الصفحات المسموحة للدور
    if employee.role.allowed_pages:
        try:
            allowed_pages = json.loads(employee.role.allowed_pages)
            return page_route in allowed_pages
        except (json.JSONDecodeError, TypeError):
            return False
    
    return False

def requires_permission(permission_name):
    """
    ديكوريتر للتحقق من صلاحية الموظف
    يستخدم لحماية المسارات الإدارية
    permission_name: اسم الصلاحية مثل 'users.read' أو 'products.create'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # غير مسجل دخول
            
            # التحقق من أن المستخدم موظف
            employee = Employee.query.filter_by(user_id=current_user.id).first()
            if not employee:
                # إذا كان مدير عام (is_admin) ولكن ليس في جدول الموظفين
                if current_user.is_admin:
                    return f(*args, **kwargs)
                abort(403)  # غير مخول
            
            # التحقق من حالة الموظف
            if hasattr(employee, 'status') and employee.status != 'active':
                abort(403)  # موظف غير نشط
            
            # التحقق من الصلاحية
            if has_permission(employee, permission_name):
                # تسجيل النشاط
                log_activity(employee, f"accessed_{permission_name}", request.endpoint)
                return f(*args, **kwargs)
            else:
                abort(403)  # لا يملك الصلاحية
        
        return decorated_function
    return decorator

def has_permission(employee, permission_name):
    """
    التحقق من وجود صلاحية محددة للموظف
    """
    # البحث عن الصلاحية
    permission = Permission.query.filter_by(name=permission_name, is_active=True).first()
    if not permission:
        return False
    
    # التحقق من الصلاحيات الخاصة للموظف
    special_perm = EmployeePermission.query.filter_by(
        employee_id=employee.id,
        permission_id=permission.id
    ).first()
    
    if special_perm:
        # التحقق من تاريخ انتهاء الصلاحية
        if special_perm.expires_at and special_perm.expires_at < datetime.utcnow():
            return False
        return special_perm.granted
    
    # التحقق من صلاحيات الدور
    role_perm = RolePermission.query.filter_by(
        role_id=employee.role_id,
        permission_id=permission.id
    ).first()
    
    return bool(role_perm)

def get_user_permissions(user_id):
    """
    الحصول على جميع صلاحيات المستخدم
    """
    employee = Employee.query.filter_by(user_id=user_id).first()
    if not employee:
        return []
    
    permissions = []
    
    # صلاحيات الدور
    role_permissions = db.session.query(Permission).join(RolePermission).filter(
        RolePermission.role_id == employee.role_id,
        Permission.is_active == True
    ).all()
    
    for perm in role_permissions:
        permissions.append({
            'name': perm.name,
            'display_name': perm.display_name,
            'category': perm.category,
            'source': 'role'
        })
    
    # الصلاحيات الخاصة
    special_permissions = db.session.query(Permission, EmployeePermission).join(EmployeePermission).filter(
        EmployeePermission.employee_id == employee.id,
        Permission.is_active == True,
        EmployeePermission.granted == True,
        db.or_(
            EmployeePermission.expires_at.is_(None),
            EmployeePermission.expires_at > datetime.utcnow()
        )
    ).all()
    
    for perm, emp_perm in special_permissions:
        # إضافة أو تحديث الصلاحية
        existing = next((p for p in permissions if p['name'] == perm.name), None)
        if existing:
            existing['source'] = 'special'
        else:
            permissions.append({
                'name': perm.name,
                'display_name': perm.display_name,
                'category': perm.category,
                'source': 'special'
            })
    
    return permissions

def can_manage_employee(manager_employee, target_employee):
    """
    التحقق من إمكانية مدير إدارة موظف معين
    """
    # المدير العام يستطيع إدارة الجميع
    if manager_employee.role.is_admin:
        return True
    
    # الموظف لا يستطيع إدارة نفسه
    if manager_employee.id == target_employee.id:
        return False
    
    # التحقق من التسلسل الإداري
    current_emp = target_employee
    while current_emp.manager_id:
        if current_emp.manager_id == manager_employee.id:
            return True
        current_emp = Employee.query.get(current_emp.manager_id)
    
    return False

def log_activity(employee_or_id, action, description=None, resource_type=None, resource_id=None):
    """
    تسجيل نشاط الموظف
    employee_or_id: يمكن أن يكون Employee object أو employee_id
    """
    try:
        # التحقق من نوع المعامل
        if isinstance(employee_or_id, Employee):
            employee_id = employee_or_id.id
        else:
            employee_id = employee_or_id
        
        activity = ActivityLog(
            employee_id=employee_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error logging activity: {e}")

def generate_employee_id():
    """
    توليد رقم موظف جديد
    """
    # البحث عن آخر رقم موظف
    last_employee = Employee.query.order_by(Employee.id.desc()).first()
    if last_employee and last_employee.employee_id:
        try:
            last_num = int(last_employee.employee_id.replace('EMP', ''))
            new_num = last_num + 1
        except:
            new_num = 1001
    else:
        new_num = 1001
    
    return f"EMP{new_num:04d}"

def get_employee_hierarchy(employee_id):
    """
    الحصول على التسلسل الإداري للموظف
    """
    employee = Employee.query.get(employee_id)
    if not employee:
        return []
    
    hierarchy = []
    current_emp = employee
    
    # البحث عن المدراء
    while current_emp:
        hierarchy.append({
            'id': current_emp.id,
            'name': current_emp.user.full_name,
            'position': current_emp.position,
            'role': current_emp.role.display_name
        })
        if current_emp.manager_id:
            current_emp = Employee.query.get(current_emp.manager_id)
        else:
            break
    
    return list(reversed(hierarchy))

def get_subordinates(employee_id):
    """
    الحصول على المرؤوسين المباشرين وغير المباشرين
    """
    def get_direct_subordinates(emp_id):
        return Employee.query.filter_by(manager_id=emp_id, status='active').all()
    
    def get_all_subordinates(emp_id, result=None):
        if result is None:
            result = []
        
        direct_subs = get_direct_subordinates(emp_id)
        for sub in direct_subs:
            result.append(sub)
            get_all_subordinates(sub.id, result)
        
        return result
    
    return get_all_subordinates(employee_id)

def check_circular_management(employee_id, new_manager_id):
    """
    التحقق من عدم وجود دورة في التسلسل الإداري
    """
    if employee_id == new_manager_id:
        return False
    
    # التحقق من أن المدير الجديد ليس من مرؤوسي الموظف
    subordinates = get_subordinates(employee_id)
    subordinate_ids = [sub.id for sub in subordinates]
    
    return new_manager_id not in subordinate_ids

def get_permission_categories():
    """
    الحصول على فئات الصلاحيات المختلفة
    """
    categories = db.session.query(Permission.category).distinct().all()
    return [cat[0] for cat in categories]

def get_permissions_by_category():
    """
    الحصول على الصلاحيات مجمعة حسب الفئة
    """
    permissions = Permission.query.filter_by(is_active=True).order_by(Permission.category, Permission.display_name).all()
    
    result = {}
    for perm in permissions:
        if perm.category not in result:
            result[perm.category] = []
        result[perm.category].append({
            'id': perm.id,
            'name': perm.name,
            'display_name': perm.display_name,
            'description': perm.description
        })
    
    return result

def validate_employee_data(data, employee_id=None):
    """
    التحقق من صحة بيانات الموظف
    """
    errors = []
    
    # التحقق من المتطلبات الأساسية
    required_fields = ['user_id', 'role_id', 'department', 'position']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"حقل {field} مطلوب")
    
    # التحقق من عدم تكرار المستخدم
    if data.get('user_id'):
        existing = Employee.query.filter_by(user_id=data['user_id']).first()
        if existing and (not employee_id or existing.id != employee_id):
            errors.append("هذا المستخدم موظف بالفعل")
    
    # التحقق من صحة التسلسل الإداري
    if data.get('manager_id') and employee_id:
        if not check_circular_management(employee_id, data['manager_id']):
            errors.append("لا يمكن تعيين مرؤوس كمدير")
    
    return errors
