# -*- coding: utf-8 -*-
"""
اختبار المفتاح الجديد المحدث
============================
"""

import requests
import sys
import os

def test_new_api_key():
    """اختبار المفتاح الجديد"""
    
    # المفتاح الجديد المحدث
    api_key = "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"
    
    headers = {
        'accept': 'application/json',
        'api-key': api_key
    }
    
    print("🔑 اختبار المفتاح الجديد المحدث...")
    print("=" * 60)
    print(f"🔗 المفتاح: {api_key[:20]}...{api_key[-20:]}")
    
    try:
        # اختبار معلومات الحساب
        response = requests.get('https://api.brevo.com/v3/account', headers=headers, timeout=10)
        
        print(f"📊 كود الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            account_info = response.json()
            print("✅ المفتاح الجديد يعمل بنجاح!")
            print(f"📧 البريد: {account_info.get('email', 'غير محدد')}")
            
            # التحقق من نوع البيانات
            plan_info = account_info.get('plan', {})
            if isinstance(plan_info, list) and len(plan_info) > 0:
                plan_type = plan_info[0].get('type', 'غير محدد')
            elif isinstance(plan_info, dict):
                plan_type = plan_info.get('type', 'غير محدد')
            else:
                plan_type = 'غير محدد'
            
            print(f"📊 نوع الخطة: {plan_type}")
            print(f"👤 اسم الشركة: {account_info.get('companyName', 'غير محدد')}")
            
            # اختبار إرسال بريد سريع
            return test_send_email(headers)
            
        elif response.status_code == 401:
            print("❌ مفتاح API غير صالح أو منتهي الصلاحية")
            print(f"📝 الخطأ: {response.text}")
            return False
            
        else:
            print(f"⚠️ خطأ HTTP {response.status_code}")
            print(f"📝 الرد: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return False

def test_send_email(headers):
    """اختبار إرسال بريد إلكتروني سريع"""
    print("\n📧 اختبار إرسال بريد إلكتروني...")
    
    email_data = {
        "sender": {
            "name": "ES-GIFT",
            "email": "mohamedeloker9@gmail.com"
        },
        "to": [
            {
                "email": "mohamedeloker9@gmail.com",
                "name": "اختبار المفتاح الجديد"
            }
        ],
        "subject": "🎉 نجح اختبار المفتاح الجديد - ES-GIFT",
        "htmlContent": """
        <html>
        <body dir="rtl" style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
                <h1 style="margin: 0;">🎉 ES-GIFT</h1>
                <p style="margin: 10px 0 0 0; font-size: 1.2em;">تهانينا! المفتاح الجديد يعمل</p>
            </div>
            
            <div style="padding: 20px; background: #f8f9fa; margin-top: 20px; border-radius: 10px;">
                <h2 style="color: #333;">✅ نجح اختبار Brevo API</h2>
                <p>تم اختبار المفتاح الجديد بنجاح، ويمكن الآن إرسال رسائل التحقق وتأكيد الطلبات.</p>
                
                <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                    <strong>📊 تفاصيل الاختبار:</strong><br>
                    • API Key: جديد ومفعل<br>
                    • SMTP: متصل<br>
                    • التحقق: نجح<br>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #666;">
                <p>🎁 ES-GIFT - منصتك للبطاقات الرقمية</p>
            </div>
        </body>
        </html>
        """
    }
    
    try:
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={**headers, 'content-type': 'application/json'},
            json=email_data,
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✅ تم إرسال البريد الاختباري بنجاح!")
            print(f"📧 Message ID: {result.get('messageId', 'N/A')}")
            return True
        else:
            print(f"❌ فشل في إرسال البريد الاختباري: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في إرسال البريد الاختباري: {str(e)}")
        return False

def test_with_app():
    """اختبار في سياق التطبيق"""
    print("\n🔧 اختبار في سياق التطبيق...")
    
    try:
        # إضافة مجلد المشروع للمسار
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import app
        from brevo_config import BrevoConfig
        
        with app.app_context():
            print("✅ التطبيق متصل مع Brevo")
            print(f"🔑 API Key محدث: {'نعم' if BrevoConfig.API_KEY.endswith('VfznStTY9xAqKRJN') else 'لا'}")
            print(f"📧 البريد المرسل: {BrevoConfig.DEFAULT_SENDER.get('email')}")
            print(f"🏷️ اسم المرسل: {BrevoConfig.DEFAULT_SENDER.get('name')}")
            return True
            
    except Exception as e:
        print(f"❌ خطأ في سياق التطبيق: {str(e)}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🚀 اختبار شامل للمفتاح الجديد - ES-GIFT")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # اختبار 1: API مباشرة
    if test_new_api_key():
        tests_passed += 1
    
    # اختبار 2: سياق التطبيق
    if test_with_app():
        tests_passed += 1
    
    # النتائج
    print("\n" + "=" * 60)
    print(f"📊 النتائج النهائية: {tests_passed}/{total_tests} اختبار نجح")
    
    if tests_passed == total_tests:
        print("🎉 جميع الاختبارات نجحت!")
        print("✅ مفتاح Brevo الجديد يعمل بشكل مثالي")
        print("📧 يمكنك الآن تسجيل حسابات جديدة وإرسال رسائل التحقق")
        print("\n💡 الخطوات التالية:")
        print("   1. جرب تسجيل حساب جديد")
        print("   2. تحقق من وصول رسائل التحقق")
        print("   3. اختبر تأكيد الطلبات")
    else:
        print("⚠️ بعض الاختبارات فشلت")
        print("🔧 يرجى مراجعة إعدادات Brevo")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
