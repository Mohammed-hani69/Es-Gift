#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسارات إدارة API
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, APISettings, APIProduct, APITransaction
from api_services import APIManager
import json
from datetime import datetime

# إنشاء Blueprint
api_admin_bp = Blueprint('api_admin', __name__, url_prefix='/admin/api')

@api_admin_bp.route('/settings')
@login_required
def api_settings():
    """صفحة إعدادات API"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    api_settings = APISettings.query.all()
    return render_template('admin/api_settings.html', api_settings=api_settings)

@api_admin_bp.route('/settings/add', methods=['GET', 'POST'])
@login_required
def add_api_setting():
    """إضافة إعدادات API جديدة"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            api_setting = APISettings(
                api_name=request.form.get('api_name'),
                api_url=request.form.get('api_url'),
                api_key=request.form.get('api_key'),
                secret_key=request.form.get('secret_key'),
                reseller_username=request.form.get('reseller_username'),
                api_type=request.form.get('api_type', 'onecard'),
                is_active=request.form.get('is_active') == 'on'
            )
            
            # إعدادات إضافية
            additional_settings = {}
            if request.form.get('base_url'):
                additional_settings['base_url'] = request.form.get('base_url')
            if request.form.get('timeout'):
                additional_settings['timeout'] = int(request.form.get('timeout', 30))
            
            if additional_settings:
                api_setting.settings_json = json.dumps(additional_settings)
            
            db.session.add(api_setting)
            db.session.commit()
            
            flash('تم إضافة إعدادات API بنجاح', 'success')
            return redirect(url_for('api_admin.api_settings'))
            
        except Exception as e:
            flash(f'خطأ في إضافة إعدادات API: {str(e)}', 'error')
    
    return render_template('admin/api_setting_form_new.html')

@api_admin_bp.route('/settings/edit/<int:setting_id>', methods=['GET', 'POST'])
@login_required
def edit_api_setting(setting_id):
    """تعديل إعدادات API"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    api_setting = APISettings.query.get_or_404(setting_id)
    
    if request.method == 'POST':
        try:
            api_setting.api_name = request.form.get('api_name')
            api_setting.api_url = request.form.get('api_url')
            api_setting.api_key = request.form.get('api_key')
            api_setting.secret_key = request.form.get('secret_key')
            api_setting.reseller_username = request.form.get('reseller_username')
            api_setting.api_type = request.form.get('api_type', 'onecard')
            api_setting.is_active = request.form.get('is_active') == 'on'
            api_setting.updated_at = datetime.utcnow()
            
            # إعدادات إضافية
            additional_settings = {}
            if request.form.get('base_url'):
                additional_settings['base_url'] = request.form.get('base_url')
            if request.form.get('timeout'):
                additional_settings['timeout'] = int(request.form.get('timeout', 30))
            
            if additional_settings:
                api_setting.settings_json = json.dumps(additional_settings)
            
            db.session.commit()
            
            flash('تم تحديث إعدادات API بنجاح', 'success')
            return redirect(url_for('api_admin.api_settings'))
            
        except Exception as e:
            flash(f'خطأ في تحديث إعدادات API: {str(e)}', 'error')
    
    return render_template('admin/api_setting_form_new.html', api_setting=api_setting)

@api_admin_bp.route('/settings/delete/<int:setting_id>', methods=['POST'])
@login_required
def delete_api_setting(setting_id):
    """حذف إعدادات API"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        api_setting = APISettings.query.get_or_404(setting_id)
        db.session.delete(api_setting)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف إعدادات API بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في الحذف: {str(e)}'})

@api_admin_bp.route('/settings/test/<int:setting_id>', methods=['POST'])
@login_required
def test_api_connection(setting_id):
    """اختبار الاتصال بـ API مع تفاصيل محسنة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        api_setting = APISettings.query.get_or_404(setting_id)
        
        # اختبار الاتصال
        success, message, data = APIManager.test_api_connection(api_setting)
        
        if success:
            return jsonify({
                'success': True, 
                'message': 'تم الاتصال بنجاح!',
                'data': data,
                'balance_info': f"الرصيد: {data.get('balance', 'غير متوفر')}" if isinstance(data, dict) else None
            })
        else:
            return jsonify({
                'success': False, 
                'message': f'فشل الاتصال: {message}'
            })
        
    except Exception as e:
        current_app.logger.error(f"Test connection error: {e}")
        return jsonify({'success': False, 'message': f'خطأ في الاختبار: {str(e)}'})

@api_admin_bp.route('/products/<int:setting_id>')
@login_required
def api_products(setting_id):
    """صفحة منتجات API"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    api_setting = APISettings.query.get_or_404(setting_id)
    products = APIProduct.query.filter_by(api_settings_id=setting_id).all()
    
    return render_template('admin/api_products.html', 
                         api_setting=api_setting, 
                         products=products)

@api_admin_bp.route('/sync/<int:setting_id>', methods=['POST'])
@login_required
def sync_products(setting_id):
    """مزامنة المنتجات من API مع تقرير مفصل"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        api_setting = APISettings.query.get_or_404(setting_id)
        
        if not api_setting.is_active:
            return jsonify({'success': False, 'message': 'API غير مفعل'})
        
        success, message = APIManager.sync_products(setting_id)
        
        if success:
            # جلب إحصائيات محدثة
            total_products = APIProduct.query.filter_by(api_settings_id=setting_id).count()
            imported_products = APIProduct.query.filter_by(api_settings_id=setting_id, is_imported=True).count()
            
            return jsonify({
                'success': True, 
                'message': message,
                'stats': {
                    'total_products': total_products,
                    'imported_products': imported_products,
                    'pending_products': total_products - imported_products
                }
            })
        else:
            return jsonify({'success': False, 'message': message})
        
    except Exception as e:
        current_app.logger.error(f"Sync products error: {e}")
        return jsonify({'success': False, 'message': f'خطأ في المزامنة: {str(e)}'})

@api_admin_bp.route('/import-product/<int:product_id>', methods=['POST'])
@login_required
def import_product(product_id):
    """استيراد منتج من API كمنتج محلي"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        success, message = APIManager.import_product_to_local(product_id)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        current_app.logger.error(f"Import product error: {e}")
        return jsonify({'success': False, 'message': f'خطأ في الاستيراد: {str(e)}'})

@api_admin_bp.route('/transactions/<int:setting_id>')
@login_required
def api_transactions(setting_id):
    """صفحة معاملات API"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    api_setting = APISettings.query.get_or_404(setting_id)
    transactions = APITransaction.query.filter_by(api_settings_id=setting_id)\
                                      .order_by(APITransaction.created_at.desc()).all()
    
    return render_template('admin/api_transactions.html', 
                         api_setting=api_setting, 
                         transactions=transactions)

@api_admin_bp.route('/transaction-status/<int:transaction_id>', methods=['POST'])
@login_required
def check_transaction_status(transaction_id):
    """فحص حالة معاملة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        transaction = APITransaction.query.get_or_404(transaction_id)
        service = APIManager.get_api_service(transaction.api_setting)
        
        response = service.check_transaction_status(transaction.reseller_ref_number)
        
        # تحديث حالة المعاملة
        if 'status' in response:
            transaction.transaction_status = response['status']
            if 'codes' in response:
                transaction.product_codes = json.dumps(response['codes'])
            transaction.updated_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم فحص الحالة بنجاح',
            'data': response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في فحص الحالة: {str(e)}'})

@api_admin_bp.route('/dashboard')
@login_required
def api_dashboard():
    """لوحة تحكم API مع معلومات شاملة"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    # إحصائيات عامة
    total_apis = APISettings.query.count()
    active_apis = APISettings.query.filter_by(is_active=True).count()
    total_products = APIProduct.query.count()
    imported_products = APIProduct.query.filter_by(is_imported=True).count()
    recent_transactions = APITransaction.query.order_by(APITransaction.created_at.desc()).limit(10).all()
    
    # إحصائيات لكل API
    api_stats = []
    for api_setting in APISettings.query.all():
        products_count = APIProduct.query.filter_by(api_settings_id=api_setting.id).count()
        imported_count = APIProduct.query.filter_by(api_settings_id=api_setting.id, is_imported=True).count()
        transactions_count = APITransaction.query.filter_by(api_settings_id=api_setting.id).count()
        
        api_stats.append({
            'api_setting': api_setting,
            'products_count': products_count,
            'imported_count': imported_count,
            'transactions_count': transactions_count,
            'success_rate': 0 if transactions_count == 0 else (
                APITransaction.query.filter_by(
                    api_settings_id=api_setting.id, 
                    transaction_status='success'
                ).count() / transactions_count * 100
            )
        })
    
    stats = {
        'total_apis': total_apis,
        'active_apis': active_apis,
        'total_products': total_products,
        'imported_products': imported_products,
        'recent_transactions': recent_transactions,
        'api_stats': api_stats
    }
    
    return render_template('admin/api_dashboard.html', stats=stats)

@api_admin_bp.route('/onecard-operations/<int:setting_id>')
@login_required
def onecard_operations(setting_id):
    """صفحة عمليات OneCard المتقدمة"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    api_setting = APISettings.query.get_or_404(setting_id)
    
    if api_setting.api_type != 'onecard':
        flash('هذه الصفحة مخصصة لـ OneCard API فقط', 'error')
        return redirect(url_for('api_admin.api_settings'))
    
    return render_template('admin/onecard_operations.html', api_setting=api_setting)

@api_admin_bp.route('/onecard-balance/<int:setting_id>', methods=['POST'])
@login_required
def check_onecard_balance(setting_id):
    """فحص رصيد OneCard"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        api_setting = APISettings.query.get_or_404(setting_id)
        service = APIManager.get_api_service(api_setting)
        
        response = service.check_balance()
        
        if 'error' in response:
            return jsonify({'success': False, 'message': response['error']})
        
        return jsonify({'success': True, 'data': response})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'})

@api_admin_bp.route('/onecard-merchants/<int:setting_id>', methods=['POST'])
@login_required
def get_onecard_merchants(setting_id):
    """جلب قائمة التجار من OneCard"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        api_setting = APISettings.query.get_or_404(setting_id)
        service = APIManager.get_api_service(api_setting)
        
        response = service.get_merchant_list()
        
        if 'error' in response:
            return jsonify({'success': False, 'message': response['error']})
        
        return jsonify({'success': True, 'data': response})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'})

@api_admin_bp.route('/onecard-product-details/<int:setting_id>/<product_id>', methods=['POST'])
@login_required
def get_onecard_product_details(setting_id, product_id):
    """جلب تفاصيل منتج محدد من OneCard"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        api_setting = APISettings.query.get_or_404(setting_id)
        service = APIManager.get_api_service(api_setting)
        
        response = service.get_product_info(product_id)
        
        if 'error' in response:
            return jsonify({'success': False, 'message': response['error']})
        
        return jsonify({'success': True, 'data': response})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'})

@api_admin_bp.route('/reconcile/<int:setting_id>', methods=['POST'])
@login_required
def reconcile_transactions(setting_id):
    """تسوية المعاملات"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        data = request.get_json()
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        is_successful = data.get('is_successful', True)
        
        api_setting = APISettings.query.get_or_404(setting_id)
        service = APIManager.get_api_service(api_setting)
        
        response = service.reconcile(date_from, date_to, is_successful)
        
        if 'error' in response:
            return jsonify({'success': False, 'message': response['error']})
        
        return jsonify({'success': True, 'data': response})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'})
