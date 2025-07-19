#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# إضافة مجلد المشروع إلى المسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from utils import convert_currency
from models import Currency

def test_currency_conversion():
    """اختبار وظيفة تحويل العملات"""
    
    with app.app_context():
        print("=" * 50)
        print("اختبار نظام تحويل العملات")
        print("=" * 50)
        
        # الحصول على العملات المتاحة
        currencies = Currency.query.all()
        print(f"\nالعملات المتاحة:")
        for currency in currencies:
            print(f"- {currency.code}: {currency.name} (معدل التحويل: {currency.exchange_rate})")
        
        print("\n" + "=" * 30)
        print("اختبارات التحويل")
        print("=" * 30)
        
        # اختبار 1: تحويل من الريال إلى الدولار
        try:
            result = convert_currency(100, 'SAR', 'USD')
            print(f"\n✅ اختبار 1: 100 ريال سعودي = {result} دولار أمريكي")
        except Exception as e:
            print(f"❌ خطأ في اختبار 1: {e}")
        
        # اختبار 2: تحويل من الدولار إلى الريال
        try:
            result = convert_currency(100, 'USD', 'SAR')
            print(f"✅ اختبار 2: 100 دولار أمريكي = {result} ريال سعودي")
        except Exception as e:
            print(f"❌ خطأ في اختبار 2: {e}")
        
        # اختبار 3: تحويل من اليورو إلى الدولار (عبر الريال)
        try:
            result = convert_currency(100, 'EUR', 'USD')
            print(f"✅ اختبار 3: 100 يورو = {result} دولار أمريكي")
        except Exception as e:
            print(f"❌ خطأ في اختبار 3: {e}")
        
        # اختبار 4: تحويل من الريال إلى الريال (نفس العملة)
        try:
            result = convert_currency(100, 'SAR', 'SAR')
            print(f"✅ اختبار 4: 100 ريال سعودي = {result} ريال سعودي")
        except Exception as e:
            print(f"❌ خطأ في اختبار 4: {e}")
        
        print("\n" + "=" * 50)
        print("انتهاء الاختبارات")
        print("=" * 50)

if __name__ == "__main__":
    test_currency_conversion()
