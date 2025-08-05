#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نظام Hostinger Email الجديد
===================================

هذا الملف لاختبار عمل نظام البريد الإلكتروني الجديد باستخدام Hostinger SMTP
"""

import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from send_by_hostinger import (
    test_email_connection,
    send_verification_email,
    send_order_confirmation,
    send_welcome_email,
    send_custom_email
)

def test_connection():
    """اختبار الاتصال بخادم SMTP"""
    print("=" * 50)
    print("🔍 اختبار الاتصال بخادم Hostinger SMTP")
    print("=" * 50)
    
    success, message = test_email_connection()
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    
    print()
    return success

def test_verification_email():
    """اختبار إرسال كود التحقق"""
    print("=" * 50)
    print("🔐 اختبار إرسال كود التحقق")
    print("=" * 50)
    
    test_email = "test@example.com"  # غيّر هذا لبريد حقيقي للاختبار
    
    success, message, code = send_verification_email(test_email)
    
    if success:
        print(f"✅ تم إرسال كود التحقق بنجاح")
        print(f"📧 البريد: {test_email}")
        print(f"🔢 الكود: {code}")
        print(f"📝 الرسالة: {message}")
    else:
        print(f"❌ فشل إرسال كود التحقق")
        print(f"📝 الرسالة: {message}")
    
    print()
    return success

def test_order_confirmation():
    """اختبار إرسال تأكيد الطلب"""
    print("=" * 50)
    print("📦 اختبار إرسال تأكيد الطلب")
    print("=" * 50)
    
    test_email = "test@example.com"  # غيّر هذا لبريد حقيقي للاختبار
    
    success, message = send_order_confirmation(
        email=test_email,
        order_number="ES12345678",
        customer_name="أحمد محمد",
        total_amount="150.00 ريال سعودي",
        order_date="2025-08-05 15:30"
    )
    
    if success:
        print(f"✅ تم إرسال تأكيد الطلب بنجاح")
        print(f"📧 البريد: {test_email}")
        print(f"📝 الرسالة: {message}")
    else:
        print(f"❌ فشل إرسال تأكيد الطلب")
        print(f"📝 الرسالة: {message}")
    
    print()
    return success

def test_welcome_email():
    """اختبار إرسال رسالة الترحيب"""
    print("=" * 50)
    print("👋 اختبار إرسال رسالة الترحيب")
    print("=" * 50)
    
    test_email = "test@example.com"  # غيّر هذا لبريد حقيقي للاختبار
    
    success, message = send_welcome_email(
        email=test_email,
        customer_name="أحمد محمد"
    )
    
    if success:
        print(f"✅ تم إرسال رسالة الترحيب بنجاح")
        print(f"📧 البريد: {test_email}")
        print(f"📝 الرسالة: {message}")
    else:
        print(f"❌ فشل إرسال رسالة الترحيب")
        print(f"📝 الرسالة: {message}")
    
    print()
    return success

def test_custom_email():
    """اختبار إرسال رسالة مخصصة"""
    print("=" * 50)
    print("📝 اختبار إرسال رسالة مخصصة")
    print("=" * 50)
    
    test_email = "test@example.com"  # غيّر هذا لبريد حقيقي للاختبار
    
    success, message = send_custom_email(
        email=test_email,
        subject="رسالة اختبار من ES-Gift",
        message_content="هذه رسالة اختبار لنظام Hostinger SMTP الجديد.<br><br>تم إرسالها بنجاح!",
        message_title="اختبار النظام"
    )
    
    if success:
        print(f"✅ تم إرسال الرسالة المخصصة بنجاح")
        print(f"📧 البريد: {test_email}")
        print(f"📝 الرسالة: {message}")
    else:
        print(f"❌ فشل إرسال الرسالة المخصصة")
        print(f"📝 الرسالة: {message}")
    
    print()
    return success

def main():
    """تشغيل جميع الاختبارات"""
    print("🎁 ES-Gift - اختبار نظام Hostinger Email")
    print("=" * 60)
    print()
    
    results = []
    
    # اختبار الاتصال
    results.append(("اختبار الاتصال", test_connection()))
    
    # إذا فشل الاتصال، لا نكمل باقي الاختبارات
    if not results[0][1]:
        print("❌ فشل الاتصال بالخادم - توقف الاختبار")
        return
    
    # باقي الاختبارات
    results.append(("اختبار كود التحقق", test_verification_email()))
    results.append(("اختبار تأكيد الطلب", test_order_confirmation()))
    results.append(("اختبار رسالة الترحيب", test_welcome_email()))
    results.append(("اختبار رسالة مخصصة", test_custom_email()))
    
    # عرض النتائج النهائية
    print("=" * 60)
    print("📊 ملخص نتائج الاختبار")
    print("=" * 60)
    
    success_count = 0
    for test_name, success in results:
        status = "✅ نجح" if success else "❌ فشل"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print()
    print(f"النتيجة النهائية: {success_count}/{len(results)} اختبارات نجحت")
    
    if success_count == len(results):
        print("🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام")
    else:
        print("⚠️ بعض الاختبارات فشلت - يرجى مراجعة الإعدادات")

if __name__ == "__main__":
    main()
