#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
دوال مساعدة لنظام API
"""

import uuid
from datetime import datetime
from decimal import Decimal
from flask import current_app
from models import db, APISettings, APIProduct, APITransaction, Product, Order, ProductCode
from api_services import APIManager

def generate_reference_number():
    """توليد رقم مرجع فريد للمعاملة"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"ES{timestamp}{unique_id}"

def process_order_with_api(order_id):
    """معالجة طلب باستخدام API"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return False, "الطلب غير موجود"
        
        # البحث عن API نشط
        api_setting = APISettings.query.filter_by(is_active=True).first()
        if not api_setting:
            return False, "لا يوجد API نشط"
        
        success_count = 0
        failed_count = 0
        
        for order_item in order.items:
            product = order_item.product
            
            # البحث عن المنتج في API
            api_product = APIProduct.query.filter_by(
                product_id=product.id,
                is_imported=True
            ).first()
            
            if not api_product:
                # محاولة البحث بالاسم
                api_product = APIProduct.query.filter(
                    APIProduct.name.ilike(f'%{product.name}%'),
                    APIProduct.api_settings_id == api_setting.id
                ).first()
            
            if api_product:
                # محاولة شراء المنتج من API
                for _ in range(order_item.quantity):
                    ref_number = generate_reference_number()
                    
                    success, response = APIManager.purchase_from_api(
                        api_setting.id,
                        api_product.external_product_id,
                        order.id,
                        ref_number
                    )
                    
                    if success:
                        success_count += 1
                        
                        # إضافة أكواد المنتج إذا كانت متوفرة
                        if isinstance(response, dict) and 'codes' in response:
                            codes = response['codes']
                            if isinstance(codes, list):
                                for code in codes:
                                    product_code = ProductCode(
                                        product_id=product.id,
                                        code=str(code),
                                        is_used=True,
                                        used_at=datetime.utcnow(),
                                        order_id=order.id
                                    )
                                    db.session.add(product_code)
                            else:
                                product_code = ProductCode(
                                    product_id=product.id,
                                    code=str(codes),
                                    is_used=True,
                                    used_at=datetime.utcnow(),
                                    order_id=order.id
                                )
                                db.session.add(product_code)
                    else:
                        failed_count += 1
                        current_app.logger.error(f"فشل شراء {product.name}: {response}")
            else:
                # المنتج غير متوفر في API
                failed_count += order_item.quantity
                current_app.logger.warning(f"المنتج {product.name} غير متوفر في API")
        
        # تحديث حالة الطلب
        if failed_count == 0:
            order.order_status = 'completed'
            order.payment_status = 'paid'
        elif success_count > 0:
            order.order_status = 'partially_completed'
        else:
            order.order_status = 'failed'
        
        db.session.commit()
        
        return True, f"تم معالجة الطلب - نجح: {success_count}, فشل: {failed_count}"
        
    except Exception as e:
        current_app.logger.error(f"خطأ في معالجة الطلب: {e}")
        db.session.rollback()
        return False, str(e)

def sync_all_apis():
    """مزامنة جميع APIs النشطة"""
    try:
        active_apis = APISettings.query.filter_by(is_active=True).all()
        
        total_synced = 0
        for api_setting in active_apis:
            try:
                success, message = APIManager.sync_products(api_setting.id)
                if success:
                    # استخراج عدد المنتجات من الرسالة
                    import re
                    numbers = re.findall(r'\d+', message)
                    if numbers:
                        total_synced += int(numbers[0])
                
                current_app.logger.info(f"مزامنة {api_setting.api_name}: {message}")
                
            except Exception as e:
                current_app.logger.error(f"خطأ في مزامنة {api_setting.api_name}: {e}")
                continue
        
        return True, f"تم مزامنة {total_synced} منتج من {len(active_apis)} API"
        
    except Exception as e:
        current_app.logger.error(f"خطأ في مزامنة APIs: {e}")
        return False, str(e)

def auto_import_popular_products():
    """استيراد تلقائي للمنتجات الشائعة"""
    try:
        # البحث عن منتجات شائعة للاستيراد
        popular_products = APIProduct.query.filter(
            APIProduct.is_imported == False,
            APIProduct.stock_status == True,
            APIProduct.name.ilike('%PlayStation%') |
            APIProduct.name.ilike('%Xbox%') |
            APIProduct.name.ilike('%Steam%') |
            APIProduct.name.ilike('%Google Play%') |
            APIProduct.name.ilike('%iTunes%')
        ).limit(20).all()
        
        imported_count = 0
        for api_product in popular_products:
            try:
                success, message = APIManager.import_api_product_to_local(api_product.id)
                if success:
                    imported_count += 1
                    current_app.logger.info(f"تم استيراد {api_product.name}")
                else:
                    current_app.logger.warning(f"فشل استيراد {api_product.name}: {message}")
                    
            except Exception as e:
                current_app.logger.error(f"خطأ في استيراد {api_product.name}: {e}")
                continue
        
        return True, f"تم استيراد {imported_count} منتج شائع"
        
    except Exception as e:
        current_app.logger.error(f"خطأ في الاستيراد التلقائي: {e}")
        return False, str(e)

def check_api_health():
    """فحص صحة جميع APIs"""
    try:
        apis = APISettings.query.filter_by(is_active=True).all()
        health_status = []
        
        for api_setting in apis:
            try:
                service = APIManager.get_api_service(api_setting)
                response = service.check_balance()
                
                if 'error' in response:
                    status = {
                        'api_name': api_setting.api_name,
                        'status': 'error',
                        'message': response['error']
                    }
                else:
                    status = {
                        'api_name': api_setting.api_name,
                        'status': 'healthy',
                        'balance': response.get('balance', 'N/A')
                    }
                
                health_status.append(status)
                
            except Exception as e:
                health_status.append({
                    'api_name': api_setting.api_name,
                    'status': 'error',
                    'message': str(e)
                })
        
        return True, health_status
        
    except Exception as e:
        current_app.logger.error(f"خطأ في فحص صحة APIs: {e}")
        return False, str(e)

def get_api_stats():
    """الحصول على إحصائيات نظام API"""
    try:
        stats = {
            'total_apis': APISettings.query.count(),
            'active_apis': APISettings.query.filter_by(is_active=True).count(),
            'total_products': APIProduct.query.count(),
            'imported_products': APIProduct.query.filter_by(is_imported=True).count(),
            'available_products': APIProduct.query.filter_by(stock_status=True).count(),
            'total_transactions': APITransaction.query.count(),
            'successful_transactions': APITransaction.query.filter_by(transaction_status='success').count(),
            'pending_transactions': APITransaction.query.filter_by(transaction_status='pending').count(),
            'failed_transactions': APITransaction.query.filter_by(transaction_status='failed').count(),
        }
        
        # حساب معدل النجاح
        if stats['total_transactions'] > 0:
            stats['success_rate'] = (stats['successful_transactions'] / stats['total_transactions']) * 100
        else:
            stats['success_rate'] = 0
        
        return stats
        
    except Exception as e:
        current_app.logger.error(f"خطأ في جلب إحصائيات API: {e}")
        return {}

def cleanup_old_transactions(days=30):
    """تنظيف المعاملات القديمة"""
    try:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_transactions = APITransaction.query.filter(
            APITransaction.created_at < cutoff_date,
            APITransaction.transaction_status.in_(['failed', 'success'])
        ).all()
        
        deleted_count = len(old_transactions)
        for transaction in old_transactions:
            db.session.delete(transaction)
        
        db.session.commit()
        
        return True, f"تم حذف {deleted_count} معاملة قديمة"
        
    except Exception as e:
        current_app.logger.error(f"خطأ في تنظيف المعاملات: {e}")
        db.session.rollback()
        return False, str(e)
