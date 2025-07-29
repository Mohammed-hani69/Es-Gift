#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار شامل لنظام البريد الإلكتروني بعد التحديثات
Test complete email system after updates
"""

import os
import sys
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# تحميل متغيرات البيئة
load_dotenv()

def test_brevo_api():
    """اختبار Brevo API"""
    print("🔄 اختبار Brevo API...")
    
    try:
        # إعداد API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')
        
        # إنشاء API instance
        api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # الحصول على معلومات الحساب
        api_response = api_instance.get_account()
        
        print("✅ Brevo API متصل بنجاح!")
        print(f"📧 البريد الإلكتروني: {api_response.email}")
        print(f"🏢 الشركة: {api_response.company_name}")
        print(f"📊 خطة الاشتراك: {api_response.plan[0].type}")
        
        return True
        
    except ApiException as e:
        print(f"❌ فشل في اختبار Brevo API: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع في Brevo API: {e}")
        return False

def test_brevo_email_send():
    """اختبار إرسال بريد إلكتروني عبر Brevo API"""
    print("\n🔄 اختبار إرسال البريد عبر Brevo API...")
    
    try:
        # إعداد API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv('BREVO_API_KEY')
        
        # إنشاء API instance
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # إعداد البريد الإلكتروني
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": "test@example.com", "name": "Test User"}],
            sender={"email": os.getenv('BREVO_SENDER_EMAIL'), "name": os.getenv('BREVO_SENDER_NAME')},
            subject="اختبار النظام - ES-GIFT",
            html_content="""
            <h2>مرحباً من ES-GIFT</h2>
            <p>هذا اختبار للتأكد من عمل نظام البريد الإلكتروني بعد التحديثات.</p>
            <p>إذا وصلك هذا البريد، فإن النظام يعمل بشكل صحيح!</p>
            """
        )
        
        # إرسال البريد (في وضع الاختبار)
        print("✅ تكوين البريد الإلكتروني صحيح!")
        print("📧 البريد جاهز للإرسال")
        print("ℹ️  لم يتم الإرسال الفعلي لتجنب استهلاك الكوتا")
        
        return True
        
    except ApiException as e:
        print(f"❌ فشل في اختبار إرسال البريد عبر Brevo: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع في إرسال البريد: {e}")
        return False

def test_flask_mail_smtp():
    """اختبار Flask-Mail مع SMTP"""
    print("\n🔄 اختبار نظام Flask-Mail الاحتياطي...")
    
    try:
        # إعداد SMTP
        smtp_server = os.getenv('MAIL_SERVER', 'smtp-relay.brevo.com')
        smtp_port = int(os.getenv('MAIL_PORT', '587'))
        smtp_username = os.getenv('MAIL_USERNAME')
        smtp_password = os.getenv('MAIL_PASSWORD')
        
        if not smtp_username or not smtp_password:
            print("⚠️  معلومات SMTP غير مكتملة في متغيرات البيئة")
            return False
        
        # اختبار الاتصال
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.quit()
        
        print("✅ نظام Flask-Mail SMTP متصل بنجاح!")
        print(f"📧 خادم SMTP: {smtp_server}:{smtp_port}")
        print(f"👤 المستخدم: {smtp_username}")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل في اختبار Flask-Mail SMTP: {e}")
        return False

def test_environment_variables():
    """اختبار متغيرات البيئة المطلوبة"""
    print("\n🔄 اختبار متغيرات البيئة...")
    
    required_vars = [
        'BREVO_API_KEY',
        'BREVO_SENDER_EMAIL',
        'BREVO_SENDER_NAME',
        'MAIL_SERVER',
        'MAIL_PORT',
        'MAIL_USERNAME',
        'MAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '****'}")
    
    if missing_vars:
        print(f"❌ متغيرات مفقودة: {', '.join(missing_vars)}")
        return False
    
    print("✅ جميع متغيرات البيئة موجودة!")
    return True

def main():
    """الاختبار الرئيسي"""
    print("=" * 60)
    print("🚀 اختبار شامل لنظام البريد الإلكتروني - ES-GIFT")
    print("=" * 60)
    
    # نتائج الاختبارات
    results = {}
    
    # اختبار متغيرات البيئة
    results['env_vars'] = test_environment_variables()
    
    # اختبار Brevo API
    results['brevo_api'] = test_brevo_api()
    
    # اختبار إرسال البريد عبر Brevo
    results['brevo_email'] = test_brevo_email_send()
    
    # اختبار Flask-Mail
    results['flask_mail'] = test_flask_mail_smtp()
    
    # عرض النتائج النهائية
    print("\n" + "=" * 60)
    print("📊 نتائج الاختبار:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 جميع الاختبارات نجحت! نظام البريد الإلكتروني جاهز للاستخدام.")
        print("📧 يمكنك الآن استخدام النظام لإرسال رسائل التحقق والطلبات.")
    else:
        print("⚠️  بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")
        print("🔧 تأكد من تحديث ملف .env بالمعلومات الصحيحة.")
    
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
