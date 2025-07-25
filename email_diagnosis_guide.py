#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
دليل تشخيص وحل مشاكل البريد الإلكتروني - ES-Gift
================================================

هذا الملف يقدم دليل شامل لتشخيص وحل مشاكل إرسال البريد الإلكتروني
مع ملفات Excel في نظام ES-Gift.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

def check_environment_setup():
    """فحص إعداد البيئة"""
    print("🔧 فحص إعداد البيئة...")
    print("=" * 50)
    
    # تحميل متغيرات البيئة
    load_dotenv()
    
    # فحص المتغيرات المطلوبة
    required_vars = {
        'MAIL_USERNAME': 'عنوان البريد الإلكتروني المرسل',
        'MAIL_PASSWORD': 'كلمة مرور التطبيق من Gmail',
        'MAIL_SERVER': 'خادم البريد (smtp.gmail.com)',
        'MAIL_PORT': 'منفذ البريد (587)',
        'MAIL_USE_TLS': 'تشفير TLS (True)'
    }
    
    all_good = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == 'MAIL_PASSWORD':
                print(f"✅ {var}: [محمي - كلمة مرور موجودة]")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: غير موجود - {description}")
            all_good = False
    
    return all_good

def check_unicode_issues():
    """فحص مشاكل Unicode في المتغيرات"""
    print("\n🔍 فحص مشاكل Unicode...")
    print("=" * 30)
    
    load_dotenv()
    
    mail_username = os.getenv('MAIL_USERNAME', '')
    mail_password = os.getenv('MAIL_PASSWORD', '')
    
    # فحص الأحرف غير المرغوب فيها
    problematic_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
    
    issues_found = False
    
    if mail_username:
        for char in problematic_chars:
            if char in mail_username:
                print(f"❌ تم العثور على رمز Unicode مشكوك فيه في MAIL_USERNAME: {repr(char)}")
                issues_found = True
        
        # فحص المساحات الزائدة
        if mail_username != mail_username.strip():
            print("❌ توجد مساحات زائدة في MAIL_USERNAME")
            issues_found = True
    
    if not issues_found:
        print("✅ لا توجد مشاكل Unicode ظاهرة")
    
    return not issues_found

def gmail_app_password_guide():
    """دليل إنشاء كلمة مرور التطبيق لـ Gmail"""
    print("\n📧 دليل إنشاء كلمة مرور التطبيق لـ Gmail:")
    print("=" * 50)
    
    steps = [
        "1. افتح Google Account: https://myaccount.google.com",
        "2. انقر على 'Security' من القائمة الجانبية",
        "3. تأكد من تفعيل '2-Step Verification' أولاً",
        "4. ابحث عن 'App passwords' أو 'كلمات مرور التطبيقات'",
        "5. انقر على 'App passwords'",
        "6. اختر 'Mail' كنوع التطبيق",
        "7. اختر 'Other (Custom name)' للجهاز",
        "8. اكتب 'ES-Gift System' كاسم",
        "9. انقر 'Generate' لإنشاء كلمة المرور",
        "10. انسخ كلمة المرور المكونة من 16 رقم",
        "11. استخدم هذه الكلمة في MAIL_PASSWORD في ملف .env"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print("\n⚠️  مهم:")
    print("   - لا تستخدم كلمة مرور حسابك العادية")
    print("   - استخدم فقط كلمة مرور التطبيق المولدة")
    print("   - كلمة مرور التطبيق تكون مثل: abcd efgh ijkl mnop")

def common_issues_solutions():
    """حلول للمشاكل الشائعة"""
    print("\n🛠️  حلول للمشاكل الشائعة:")
    print("=" * 35)
    
    issues = {
        "UnicodeEncodeError": [
            "تنظيف ملف .env من الأحرف غير المرئية",
            "التأكد من عدم وجود مساحات زائدة",
            "استخدام محرر نص بسيط لتحرير .env"
        ],
        "Authentication Failed": [
            "التأكد من تفعيل 2-Step Verification",
            "استخدام App Password وليس كلمة المرور العادية",
            "التأكد من صحة البريد الإلكتروني"
        ],
        "Connection Timeout": [
            "فحص اتصال الإنترنت",
            "التأكد من إعدادات Firewall",
            "استخدام TLS على المنفذ 587"
        ],
        "Working outside of request context": [
            "استخدام app.test_request_context() في الاختبارات",
            "إصلاح context processors في app.py"
        ]
    }
    
    for issue, solutions in issues.items():
        print(f"\n❌ {issue}:")
        for solution in solutions:
            print(f"   ✅ {solution}")

def create_test_email_script():
    """إنشاء سكريبت اختبار بسيط"""
    print("\n📝 إنشاء سكريبت اختبار بسيط...")
    
    test_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار بسيط لإرسال البريد الإلكتروني
==================================
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

def test_smtp_connection():
    """اختبار اتصال SMTP مباشر"""
    load_dotenv()
    
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    if not username or not password:
        print("❌ متغيرات البيئة غير محددة")
        return False
    
    try:
        # إنشاء اتصال SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print(f"🔑 محاولة تسجيل الدخول بـ: {username}")
        server.login(username, password)
        
        # إنشاء رسالة بسيطة
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username  # إرسال لنفس البريد
        msg['Subject'] = "اختبار SMTP - ES-Gift"
        
        body = "هذا اختبار بسيط لاتصال SMTP"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # إرسال الرسالة
        server.send_message(msg)
        server.quit()
        
        print("✅ تم إرسال البريد بنجاح!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return False

if __name__ == "__main__":
    test_smtp_connection()
'''
    
    with open('simple_email_test.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ تم إنشاء simple_email_test.py")
    print("   يمكنك تشغيله بـ: python simple_email_test.py")

def main():
    """الدالة الرئيسية"""
    print("🧪 دليل تشخيص مشاكل البريد الإلكتروني - ES-Gift")
    print("=" * 60)
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # فحص إعداد البيئة
    env_ok = check_environment_setup()
    
    # فحص مشاكل Unicode
    unicode_ok = check_unicode_issues()
    
    # عرض دليل Gmail
    gmail_app_password_guide()
    
    # عرض حلول المشاكل الشائعة
    common_issues_solutions()
    
    # إنشاء سكريبت اختبار
    create_test_email_script()
    
    print("\n" + "=" * 60)
    if env_ok and unicode_ok:
        print("✅ الإعدادات تبدو صحيحة - جرب تشغيل الاختبار")
    else:
        print("❌ يجب إصلاح المشاكل المذكورة أعلاه أولاً")
    
    print("\n📋 الخطوات التالية:")
    print("1. تأكد من إنشاء App Password صحيح من Gmail")
    print("2. حدث ملف .env بكلمة المرور الصحيحة")
    print("3. شغل: python simple_email_test.py")
    print("4. إذا نجح، شغل: python test_email_send.py")

if __name__ == "__main__":
    main()
