#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات إدارة الأدوار والصلاحيات
"""

import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Role, Employee, Permission, RolePermission
from employee_utils import requires_page_access, log_activity
from admin_pages import ADMIN_PAGES, PAGE_CATEGORIES

# إنشاء Blueprint للأدوار
roles_bp = Blueprint('roles', __name__, url_prefix='/admin/roles')

@roles_bp.route('/')
@login_required
@requires_page_access('admin.roles')
def roles_management():
    """صفحة إدارة الأدوار"""
    try:
        roles = Role.query.order_by(Role.created_at.desc()).all()
        return render_template('admin/roles.html', 
                             roles=roles, 
                             admin_pages=ADMIN_PAGES,
                             page_categories=PAGE_CATEGORIES)
    except Exception as e:
        flash(f'خطأ في تحميل الأدوار: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@roles_bp.route('/create', methods=['GET', 'POST'])
@login_required
@requires_page_access('admin.roles')
def create_role():
    """إنشاء دور جديد"""
    if request.method == 'GET':
        return render_template('admin/create_role.html', 
                             admin_pages=ADMIN_PAGES,
                             page_categories=PAGE_CATEGORIES)
    
    try:
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        description = request.form.get('description', '').strip()
        is_admin = request.form.get('is_admin') == 'on'
        allowed_pages = request.form.getlist('allowed_pages')
        
        # التحقق من البيانات
        if not name or not display_name:
            flash('اسم الدور والاسم المعروض مطلوبان', 'error')
            return render_template('admin/create_role.html', 
                                 admin_pages=ADMIN_PAGES,
                                 page_categories=PAGE_CATEGORIES)
        
        # التحقق من عدم تكرار الاسم
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role:
            flash('اسم الدور موجود بالفعل', 'error')
            return render_template('admin/create_role.html', 
                                 admin_pages=ADMIN_PAGES,
                                 page_categories=PAGE_CATEGORIES)
        
        # إنشاء الدور الجديد
        new_role = Role(
            name=name,
            display_name=display_name,
            description=description,
            is_admin=is_admin,
            allowed_pages=json.dumps(allowed_pages) if allowed_pages else None
        )
        
        db.session.add(new_role)
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(current_user.id, 'role_created', f'تم إنشاء دور جديد: {display_name}')
        
        flash(f'تم إنشاء الدور "{display_name}" بنجاح', 'success')
        return redirect(url_for('roles.roles_management'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إنشاء الدور: {str(e)}', 'error')
        return render_template('admin/create_role.html', 
                             admin_pages=ADMIN_PAGES,
                             page_categories=PAGE_CATEGORIES)

@roles_bp.route('/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
@requires_page_access('admin.roles')
def edit_role(role_id):
    """تعديل دور موجود"""
    role = Role.query.get_or_404(role_id)
    
    if request.method == 'GET':
        # جلب الصفحات المسموحة حالياً
        current_allowed_pages = []
        if role.allowed_pages:
            try:
                current_allowed_pages = json.loads(role.allowed_pages)
            except:
                current_allowed_pages = []
        
        return render_template('admin/edit_role.html', 
                             role=role,
                             current_allowed_pages=current_allowed_pages,
                             admin_pages=ADMIN_PAGES,
                             page_categories=PAGE_CATEGORIES)
    
    try:
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        description = request.form.get('description', '').strip()
        is_admin = request.form.get('is_admin') == 'on'
        allowed_pages = request.form.getlist('allowed_pages')
        
        # التحقق من البيانات
        if not name or not display_name:
            flash('اسم الدور والاسم المعروض مطلوبان', 'error')
            return redirect(url_for('roles.edit_role', role_id=role_id))
        
        # التحقق من عدم تكرار الاسم (باستثناء الدور الحالي)
        existing_role = Role.query.filter(Role.name == name, Role.id != role_id).first()
        if existing_role:
            flash('اسم الدور موجود بالفعل', 'error')
            return redirect(url_for('roles.edit_role', role_id=role_id))
        
        # تحديث بيانات الدور
        role.name = name
        role.display_name = display_name
        role.description = description
        role.is_admin = is_admin
        role.allowed_pages = json.dumps(allowed_pages) if allowed_pages else None
        
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(current_user.id, 'role_updated', f'تم تحديث الدور: {display_name}')
        
        flash(f'تم تحديث الدور "{display_name}" بنجاح', 'success')
        return redirect(url_for('roles.roles_management'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في تحديث الدور: {str(e)}', 'error')
        return redirect(url_for('roles.edit_role', role_id=role_id))

@roles_bp.route('/delete/<int:role_id>', methods=['POST'])
@login_required
@requires_page_access('admin.roles')
def delete_role(role_id):
    """حذف دور"""
    try:
        role = Role.query.get_or_404(role_id)
        
        # التحقق من عدم وجود موظفين بهذا الدور
        employees_count = Employee.query.filter_by(role_id=role_id).count()
        if employees_count > 0:
            return jsonify({
                'success': False,
                'message': f'لا يمكن حذف هذا الدور لأنه مرتبط بـ {employees_count} موظف'
            })
        
        role_name = role.display_name
        db.session.delete(role)
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(current_user.id, 'role_deleted', f'تم حذف الدور: {role_name}')
        
        return jsonify({
            'success': True,
            'message': f'تم حذف الدور "{role_name}" بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف الدور: {str(e)}'
        })

@roles_bp.route('/get_pages_by_category')
@login_required
@requires_page_access('admin.roles')
def get_pages_by_category():
    """الحصول على الصفحات مقسمة حسب الفئات (للـ API)"""
    try:
        result = {}
        for category, name in PAGE_CATEGORIES.items():
            result[category] = {
                'name': name,
                'pages': []
            }
            
            # جلب الصفحات للفئة
            for page_id, page_info in ADMIN_PAGES.items():
                if page_info.get('category') == category:
                    result[category]['pages'].append({
                        'id': page_id,
                        'name': page_info['name'],
                        'description': page_info['description']
                    })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
