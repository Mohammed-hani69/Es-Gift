#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إضافة العملات الأساسية إلى قاعدة البيانات
"""

from app import app
from models import db, Currency

def add_currencies():
    """إضافة العملات الأساسية"""
    
    currencies_data = [
        {'code': 'SAR', 'name': 'الريال السعودي', 'symbol': 'ر.س', 'exchange_rate': 1.0, 'is_active': True},
        {'code': 'USD', 'name': 'الدولار الأمريكي', 'symbol': '$', 'exchange_rate': 0.27, 'is_active': True},
        {'code': 'EUR', 'name': 'اليورو', 'symbol': '€', 'exchange_rate': 0.24, 'is_active': True},
        {'code': 'GBP', 'name': 'الجنيه الإسترليني', 'symbol': '£', 'exchange_rate': 0.21, 'is_active': True},
        {'code': 'AED', 'name': 'الدرهم الإماراتي', 'symbol': 'د.إ', 'exchange_rate': 0.98, 'is_active': True},
        {'code': 'KWD', 'name': 'الدينار الكويتي', 'symbol': 'د.ك', 'exchange_rate': 0.08, 'is_active': True},
        {'code': 'QAR', 'name': 'الريال القطري', 'symbol': 'ر.ق', 'exchange_rate': 0.97, 'is_active': True},
        {'code': 'BHD', 'name': 'الدينار البحريني', 'symbol': 'د.ب', 'exchange_rate': 0.10, 'is_active': True},
        {'code': 'OMR', 'name': 'الريال العماني', 'symbol': 'ر.ع', 'exchange_rate': 0.10, 'is_active': True},
        {'code': 'EGP', 'name': 'الجنيه المصري', 'symbol': 'ج.م', 'exchange_rate': 13.0, 'is_active': True},
        {'code': 'JOD', 'name': 'الدينار الأردني', 'symbol': 'د.أ', 'exchange_rate': 0.19, 'is_active': True},
        {'code': 'LBP', 'name': 'الليرة اللبنانية', 'symbol': 'ل.ل', 'exchange_rate': 4050.0, 'is_active': True},
        {'code': 'TRY', 'name': 'الليرة التركية', 'symbol': '₺', 'exchange_rate': 8.5, 'is_active': True},
    ]
    
    with app.app_context():
        # تحقق من وجود العملات مسبقاً
        for currency_data in currencies_data:
            existing_currency = Currency.query.filter_by(code=currency_data['code']).first()
            
            if not existing_currency:
                # إنشاء عملة جديدة
                currency = Currency(
                    code=currency_data['code'],
                    name=currency_data['name'],
                    symbol=currency_data['symbol'],
                    exchange_rate=currency_data['exchange_rate'],
                    is_active=currency_data['is_active']
                )
                db.session.add(currency)
                print(f"تم إضافة العملة: {currency_data['name']} ({currency_data['code']})")
            else:
                print(f"العملة موجودة مسبقاً: {currency_data['name']} ({currency_data['code']})")
        
        try:
            db.session.commit()
            print("تم حفظ جميع العملات بنجاح!")
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في حفظ العملات: {e}")

if __name__ == "__main__":
    add_currencies()
