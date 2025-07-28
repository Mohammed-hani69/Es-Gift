#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار تكامل Brevo
=================

يختبر إرسال رسائل التحقق والطلبات باستخدام Brevo
"""

import sys
import os

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import User, Order, OrderItem, Product, db
from email_verification_service import EmailVerificationService
from brevo_email_service import send_order_confirmation_pending_codes, test_brevo_connection
from utils import send_order_confirmation_without_codes

def test_brevo_connection_status():
    """اختبار الاتصال مع Brevo"""
    print("🔗 اختبار الاتصال مع Brevo...")
    
    success, message = test_brevo_connection()
    
    if success:
        print("✅ تم الاتصال بـ Brevo بنجاح!")
        print(f"📞 الرد: {message}")
    else:
        print("❌ فشل الاتصال بـ Brevo!")
        print(f"❌ الخطأ: {message}")
    
    return success

def test_verification_email():
    """اختبار إرسال بريد التحقق"""
    print("\n📧 اختبار إرسال بريد التحقق...")
    
    with app.app_context():
        # البحث عن مستخدم للاختبار أو إنشاء مستخدم مؤقت
        test_user = User.query.filter_by(email='test@example.com').first()
        
        if not test_user:
            test_user = User(
                username='test_user',
                email='test@example.com',
                full_name='مستخدم تجريبي',
                password_hash='test_hash',
                is_verified=False
            )
            db.session.add(test_user)
            db.session.commit()
            print("👤 تم إنشاء مستخدم تجريبي")
        
        # اختبار إرسال بريد التحقق
        success = EmailVerificationService.send_verification_email(test_user)
        
        if success:
            print("✅ تم إرسال بريد التحقق بنجاح!")
        else:
            print("❌ فشل إرسال بريد التحقق!")
        
        return success

def test_order_confirmation_email():
    """اختبار إرسال إيميل تأكيد الطلب"""
    print("\n📦 اختبار إرسال إيميل تأكيد الطلب...")
    
    # بيانات طلب تجريبي
    test_order_data = {
        'order_number': 'ORD20250729001',
        'customer_name': 'مستخدم تجريبي',
        'customer_email': 'test@example.com',
        'order_date': '2025-07-29 15:30:00',
        'product_name': 'بطاقة ايتونز - 100 ريال',
        'quantity': 1,
        'total_amount': 100.0,
        'currency': 'SAR'
    }
    
    # اختبار الدالة الجديدة
    success, message = send_order_confirmation_without_codes(
        order_data=test_order_data,
        available_codes=None,
        products_without_codes=[]
    )
    
    if success:
        print("✅ تم إرسال إيميل تأكيد الطلب بنجاح!")
    else:
        print(f"❌ فشل إرسال إيميل تأكيد الطلب: {message}")
    
    return success

def test_brevo_direct():
    """اختبار مباشر لـ Brevo"""
    print("\n🎯 اختبار مباشر لـ Brevo...")
    
    test_order_data = {
        'order_number': 'TEST001',
        'customer_name': 'اختبار مباشر',
        'customer_email': 'test@example.com',
        'order_date': '2025-07-29 15:30:00',
        'product_name': 'منتج تجريبي',
        'total_amount': 50.0,
        'currency': 'SAR'
    }
    
    success, message = send_order_confirmation_pending_codes(
        user_email='test@example.com',
        user_name='اختبار مباشر',
        order_data=test_order_data,
        status_message="هذا اختبار لتكامل Brevo"
    )
    
    if success:
        print("✅ تم الإرسال المباشر بنجاح!")
    else:
        print(f"❌ فشل الإرسال المباشر: {message}")
    
    return success

def main():
    """تشغيل جميع الاختبارات"""
    print("🧪 بدء اختبار تكامل Brevo")
    print("="*50)
    
    tests_passed = 0
    total_tests = 4
    
    # اختبار الاتصال
    if test_brevo_connection_status():
        tests_passed += 1
    
    # اختبار بريد التحقق
    if test_verification_email():
        tests_passed += 1
    
    # اختبار إيميل تأكيد الطلب
    if test_order_confirmation_email():
        tests_passed += 1
    
    # اختبار Brevo مباشر
    if test_brevo_direct():
        tests_passed += 1
    
    print("\n" + "="*50)
    print(f"📊 نتائج الاختبار: {tests_passed}/{total_tests} نجح")
    
    if tests_passed == total_tests:
        print("🎉 تم اجتياز جميع الاختبارات!")
        print("✅ تكامل Brevo يعمل بشكل صحيح")
    else:
        print(f"⚠️ فشل {total_tests - tests_passed} اختبار")
        print("🔧 يحتاج إلى مراجعة الإعدادات")
    
    return tests_passed == total_tests

if __name__ == '__main__':
    main()
