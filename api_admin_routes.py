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
from decimal import Decimal

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
    """صفحة منتجات API مع جلب مباشر من OneCard"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    api_setting = APISettings.query.get_or_404(setting_id)
    
    # جلب المنتجات المحفوظة من قاعدة البيانات
    saved_products = APIProduct.query.filter_by(api_settings_id=setting_id).all()
    
    # جلب المنتجات مباشرة من OneCard API للمقارنة
    live_products = []
    api_products_status = "success"
    api_error_message = None
    
    try:
        if api_setting.api_type == 'onecard' and api_setting.is_active:
            service = APIManager.get_api_service(api_setting)
            
            # أولاً: جلب منتجات الاختبار المحددة مباشرة
            test_products = []
            for test_id in ["3770", "3771", "3772", "3773", "3774"]:
                try:
                    test_response = service.get_product_info(test_id)
                    if 'error' not in test_response:
                        test_product = {
                            'id': len(test_products) + 1,
                            'external_product_id': test_id,
                            'name': test_response.get('name') or test_response.get('productName') or test_response.get('ProductName', f'منتج اختبار {test_id}'),
                            'description': test_response.get('description') or test_response.get('productDescription', 'منتج للاختبار - OneCard'),
                            'category': test_response.get('category') or test_response.get('categoryName', 'منتجات الاختبار'),
                            'price': float(test_response.get('price') or test_response.get('sellingPrice', 0)),
                            'currency': test_response.get('currency', 'SAR'),
                            'stock_status': test_response.get('inStock', True),
                            'is_imported': False,
                            'is_test_product': True,
                            'raw_data': json.dumps(test_response, ensure_ascii=False)
                        }
                        
                        # تحقق إذا كان المنتج مستورد مسبقاً
                        existing_saved = next((p for p in saved_products if p.external_product_id == test_id), None)
                        if existing_saved:
                            test_product['is_imported'] = existing_saved.is_imported
                            test_product['local_product'] = existing_saved.local_product
                        
                        test_products.append(test_product)
                        current_app.logger.info(f"✅ تم جلب منتج الاختبار {test_id}: {test_product['name']}")
                    else:
                        current_app.logger.warning(f"⚠️ فشل جلب منتج الاختبار {test_id}: {test_response['error']}")
                except Exception as e:
                    current_app.logger.error(f"❌ خطأ في جلب منتج الاختبار {test_id}: {e}")
            
            # ثانياً: جلب باقي المنتجات من القائمة العامة
            response = service.get_products_list()
            
            if 'error' not in response:
                # معالجة بيانات المنتجات من OneCard
                products_data = []
                if isinstance(response, dict):
                    if 'products' in response:
                        products_data = response['products']
                    elif 'result' in response and isinstance(response['result'], list):
                        products_data = response['result']
                    elif 'data' in response:
                        products_data = response['data']
                elif isinstance(response, list):
                    products_data = response
                
                # إضافة منتجات الاختبار أولاً
                live_products.extend(test_products)
                
                # ثم إضافة باقي المنتجات (تجنب التكرار مع منتجات الاختبار)
                test_ids = ["3770", "3771", "3772", "3773", "3774"]
                for product_data in products_data[:47]:  # 47 منتج إضافي مع 3 منتجات اختبار = 50 منتج إجمالي
                    try:
                        product_id = str(product_data.get('id') or product_data.get('productId') or product_data.get('ProductId', ''))
                        
                        # تجنب إضافة منتجات الاختبار مرة أخرى
                        if product_id and product_id not in test_ids:
                            live_product = {
                                'id': len(live_products) + 1,  # معرف مؤقت للعرض
                                'external_product_id': product_id,
                                'name': product_data.get('name') or product_data.get('productName') or product_data.get('ProductName', 'غير محدد'),
                                'description': product_data.get('description') or product_data.get('productDescription', ''),
                                'category': product_data.get('category') or product_data.get('categoryName', 'غير محدد'),
                                'price': float(product_data.get('price') or product_data.get('sellingPrice', 0)),
                                'currency': product_data.get('currency', 'SAR'),
                                'stock_status': product_data.get('inStock', True),
                                'is_imported': False,  # تأكد من أنه غير مستورد افتراضياً
                                'is_test_product': False,
                                'raw_data': json.dumps(product_data, ensure_ascii=False)
                            }
                            
                            # تحقق إذا كان المنتج مستورد مسبقاً
                            existing_saved = next((p for p in saved_products if p.external_product_id == product_id), None)
                            if existing_saved:
                                live_product['is_imported'] = existing_saved.is_imported
                                live_product['local_product'] = existing_saved.local_product
                            
                            live_products.append(live_product)
                    except Exception as e:
                        current_app.logger.error(f"Error processing product data: {e}")
                        continue
            else:
                # حتى لو فشل جلب القائمة العامة، نعرض منتجات الاختبار
                live_products.extend(test_products)
                if not test_products:  # فقط إذا لم نجد حتى منتجات الاختبار
                    api_products_status = "error"
                    api_error_message = response['error']
    except Exception as e:
        current_app.logger.error(f"Error fetching live products: {e}")
        api_products_status = "error"
        api_error_message = str(e)
    
    # إذا لم نتمكن من جلب المنتجات المباشرة، استخدم المحفوظة
    products_to_display = live_products if live_products else saved_products
    
    return render_template('admin/api_products.html', 
                         api_setting=api_setting, 
                         products=products_to_display,
                         saved_products_count=len(saved_products),
                         live_products_count=len(live_products),
                         api_status=api_products_status,
                         api_error=api_error_message)

@api_admin_bp.route('/test-products/<int:setting_id>', methods=['POST'])
@login_required
def test_api_products(setting_id):
    """اختبار منتجات API المحددة للاختبار"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        api_setting = APISettings.query.get_or_404(setting_id)
        service = APIManager.get_api_service(api_setting)
        
        # اختبار المنتجات المحددة
        test_results = service.test_products_availability()
        
        return jsonify({
            'success': True,
            'message': 'تم اختبار المنتجات بنجاح',
            'data': test_results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في الاختبار: {str(e)}'})

@api_admin_bp.route('/live-products/<int:setting_id>', methods=['POST'])
@login_required  
def get_live_products(setting_id):
    """جلب المنتجات المباشرة من OneCard API"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        api_setting = APISettings.query.get_or_404(setting_id)
        service = APIManager.get_api_service(api_setting)
        
        # جلب قائمة المنتجات
        response = service.get_products_list()
        
        if 'error' in response:
            return jsonify({'success': False, 'message': response['error']})
        
        # معالجة البيانات
        products_data = []
        if isinstance(response, dict):
            if 'products' in response:
                products_data = response['products']
            elif 'result' in response and isinstance(response['result'], list):
                products_data = response['result']
            elif 'data' in response:
                products_data = response['data']
        elif isinstance(response, list):
            products_data = response
        
        # تحويل البيانات للعرض
        formatted_products = []
        for product_data in products_data[:100]:  # أول 100 منتج
            try:
                product_id = str(product_data.get('id') or product_data.get('productId') or product_data.get('ProductId', ''))
                if product_id:
                    formatted_products.append({
                        'external_product_id': product_id,
                        'name': product_data.get('name') or product_data.get('productName') or product_data.get('ProductName', 'غير محدد'),
                        'price': float(product_data.get('price') or product_data.get('sellingPrice', 0)),
                        'currency': product_data.get('currency', 'SAR'), 
                        'category': product_data.get('category') or product_data.get('categoryName', 'غير محدد'),
                        'stock_status': product_data.get('inStock', True),
                        'is_test_product': product_id in ["3770", "3771", "3772", "3773", "3774"]
                    })
            except Exception as e:
                continue
        
        return jsonify({
            'success': True,
            'message': f'تم جلب {len(formatted_products)} منتج بنجاح',
            'data': formatted_products,
            'total_count': len(products_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في جلب المنتجات: {str(e)}'})

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

@api_admin_bp.route('/import-product-by-external-id/<external_id>', methods=['POST'])
@login_required
def import_product_by_external_id(external_id):
    """استيراد منتج باستخدام المعرف الخارجي"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        data = request.get_json()
        api_settings_id = data.get('api_settings_id')
        
        if not api_settings_id:
            return jsonify({'success': False, 'message': 'معرف إعدادات API مطلوب'})
        
        # البحث عن المنتج في قاعدة البيانات
        api_product = APIProduct.query.filter_by(
            api_settings_id=api_settings_id,
            external_product_id=external_id
        ).first()
        
        if not api_product:
            # إذا لم يكن المنتج موجود، قم بجلبه من API أولاً
            api_setting = APISettings.query.get(api_settings_id)
            service = APIManager.get_api_service(api_setting)
            
            # جلب تفاصيل المنتج من API
            product_data = service.get_product_info(external_id)
            
            if 'error' in product_data:
                return jsonify({'success': False, 'message': f'فشل في جلب المنتج من API: {product_data["error"]}'})
            
            # إنشاء منتج API جديد
            api_product = APIProduct(
                api_settings_id=api_settings_id,
                external_product_id=external_id,
                name=product_data.get('name') or product_data.get('productName', 'غير محدد'),
                description=product_data.get('description') or product_data.get('productDescription', ''),
                category=product_data.get('category') or product_data.get('categoryName', 'غير محدد'),
                price=Decimal(str(float(product_data.get('price') or product_data.get('sellingPrice', 0)))),
                currency=product_data.get('currency', 'SAR'),
                stock_status=product_data.get('inStock', True),
                raw_data=json.dumps(product_data, ensure_ascii=False)
            )
            db.session.add(api_product)
            db.session.commit()
        
        # استيراد المنتج كمنتج محلي
        success, message = APIManager.import_product_to_local(api_product.id)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        current_app.logger.error(f"Import product by external ID error: {e}")
        return jsonify({'success': False, 'message': f'خطأ في الاستيراد: {str(e)}'})

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
