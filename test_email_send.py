#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إرسال البريد الإلكتروني الفعلي
===================================
"""

import sys
import os
from datetime import datetime

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import current_app
from email_service import email_service

def test_send_real_email():
    """اختبار إرسال بريد إلكتروني حقيقي"""
    
    app = create_app()
    
    with app.app_context():
        with app.test_request_context():  # إضافة request context
            print("🧪 اختبار إرسال البريد الإلكتروني...")
            print("=" * 50)
        
        # بيانات طلب وهمي للاختبار
        test_order_data = {
            'order_number': 'TEST-' + datetime.now().strftime('%Y%m%d-%H%M%S'),
            'customer_name': 'عميل تجريبي',
            'customer_email': 'business@es-gift.com',  # بريد إلكتروني حقيقي للاختبار
            'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'product_name': 'بطاقة iTunes اختبار',
            'quantity': 1,
            'total_amount': 50.0,
            'currency': 'SAR'
        }
        
        # أكواد وهمية للاختبار
        test_codes = [
            'TEST-CODE-123456789',
            'TEST-CODE-987654321'
        ]
        
        print(f"📧 إرسال بريد تجريبي إلى: {test_order_data['customer_email']}")
        print(f"📦 طلب رقم: {test_order_data['order_number']}")
        print(f"🔑 عدد الأكواد: {len(test_codes)}")
        
        try:
            # إرسال البريد
            success, message = email_service.send_product_codes_email(test_order_data, test_codes)
            
            if success:
                print(f"\n✅ {message}")
                print("🎉 تم إرسال البريد بنجاح!")
                
                print("\n📋 تفاصيل ما تم إرساله:")
                print(f"   - العنوان: أكواد منتجاتك - طلب رقم {test_order_data['order_number']}")
                print(f"   - المستلم: {test_order_data['customer_email']}")
                print(f"   - المرفق: ملف Excel يحتوي على {len(test_codes)} كود")
                
                print("\n📝 يرجى التحقق من صندوق البريد الوارد (وصندوق الرسائل غير المرغوب فيها)")
                
            else:
                print(f"\n❌ {message}")
                
                # طباعة معلومات إضافية للتشخيص
                print("\n🔍 معلومات التشخيص:")
                print(f"   - MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}")
                print(f"   - MAIL_PORT: {current_app.config.get('MAIL_PORT')}")
                print(f"   - MAIL_USE_TLS: {current_app.config.get('MAIL_USE_TLS')}")
                print(f"   - MAIL_USERNAME: {'مُعرّف' if current_app.config.get('MAIL_USERNAME') else 'غير مُعرّف'}")
                print(f"   - MAIL_DEFAULT_SENDER: {'مُعرّف' if current_app.config.get('MAIL_DEFAULT_SENDER') else 'غير مُعرّف'}")
                
        except Exception as e:
            print(f"\n❌ حدث خطأ: {str(e)}")
            import traceback
            print(f"📋 تفاصيل الخطأ: {traceback.format_exc()}")

def test_simple_email():
    """اختبار إرسال بريد بسيط"""
    
    app = create_app()
    
    with app.app_context():
        with app.test_request_context():  # إضافة request context
            print("\n🧪 اختبار إرسال بريد بسيط...")
            print("=" * 40)
        
        try:
            from flask_mail import Mail, Message
            
            mail = Mail(current_app)
            
            msg = Message(
                subject="اختبار البريد الإلكتروني - ES-Gift",
                sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
                recipients=['business@es-gift.com']  # بريد إلكتروني حقيقي
            )
            
            msg.body = """
            مرحباً!
            
            هذا اختبار لخدمة البريد الإلكتروني في نظام ES-Gift.
            
            إذا وصلك هذا البريد، فإن الإعدادات تعمل بشكل صحيح.
            
            شكراً لك!
            """
            
            msg.html = """
            <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right; padding: 20px;">
                <h2 style="color: #007bff;">مرحباً!</h2>
                <p>هذا اختبار لخدمة البريد الإلكتروني في نظام <strong>ES-Gift</strong>.</p>
                <p style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                    إذا وصلك هذا البريد، فإن الإعدادات تعمل بشكل صحيح ✅
                </p>
                <p>شكراً لك!</p>
                <hr>
                <small style="color: #666;">نظام ES-Gift - {current_time}</small>
            </div>
            """.format(current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            mail.send(msg)
            print("✅ تم إرسال البريد البسيط بنجاح!")
            
        except Exception as e:
            print(f"❌ فشل في إرسال البريد البسيط: {str(e)}")

if __name__ == "__main__":
    print("🧪 اختبار شامل لإرسال البريد الإلكتروني")
    print("=" * 60)
    
    # تحديث عنوان البريد للاختبار
    print("⚠️  تذكير: يرجى تحديث عنوان البريد الإلكتروني في الكود قبل التشغيل")
    print("📧 العنوان الحالي: test@example.com")
    print("")
    
    # اختبار البريد البسيط أولاً
    test_simple_email()
    
    print("\n" + "=" * 60 + "\n")
    
    # اختبار إرسال البريد مع ملف Excel
    test_send_real_email()
    
    print("\n" + "=" * 60)
    print("🏁 انتهى الاختبار")
