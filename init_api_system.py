#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تهيئة نظام API للموقع
"""

from app import app
from models import db, APISettings, APIProduct, APITransaction
from decimal import Decimal

def init_api_system():
    """تهيئة نظام API"""
    with app.app_context():
        try:
            print('🔧 تهيئة نظام API...')
            
            # إنشاء الجداول الجديدة
            db.create_all()
            print('✅ تم إنشاء جداول قاعدة البيانات')
            
            # التحقق من وجود إعدادات API
            existing_apis = APISettings.query.count()
            print(f'📊 إعدادات API الموجودة: {existing_apis}')
            
            if existing_apis == 0:
                print('💡 يمكنك الآن إضافة إعدادات API من لوحة الإدارة')
                print('👉 اذهب إلى: /admin/api/settings')
            else:
                # عرض الإعدادات الموجودة
                apis = APISettings.query.all()
                print(f'\n📋 الإعدادات الموجودة:')
                for api in apis:
                    print(f'  - {api.api_name} ({api.api_type}) - {"نشط" if api.is_active else "معطل"}')
                    if api.last_sync:
                        print(f'    آخر مزامنة: {api.last_sync}')
                    else:
                        print(f'    لم يتم المزامنة بعد')
            
            # إحصائيات المنتجات
            total_products = APIProduct.query.count()
            imported_products = APIProduct.query.filter_by(is_imported=True).count()
            print(f'\n📦 منتجات API: {total_products} (مستورد: {imported_products})')
            
            # إحصائيات المعاملات
            total_transactions = APITransaction.query.count()
            success_transactions = APITransaction.query.filter_by(transaction_status='success').count()
            print(f'💳 المعاملات: {total_transactions} (ناجحة: {success_transactions})')
            
            print('\n✅ تم تهيئة نظام API بنجاح!')
            print('\n📖 الخطوات التالية:')
            print('1. اذهب إلى /admin/api/settings')
            print('2. أضف إعدادات OneCard API')
            print('3. اختبر الاتصال')
            print('4. قم بمزامنة المنتجات')
            print('5. استورد المنتجات المطلوبة')
            
        except Exception as e:
            print(f'❌ خطأ في تهيئة نظام API: {e}')
            raise

if __name__ == '__main__':
    init_api_system()
