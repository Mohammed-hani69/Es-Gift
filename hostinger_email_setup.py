#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد بريد Hostinger لـ ES-Gift
==============================
"""

import os
import re

def setup_hostinger_email():
    """إعداد بريد Hostinger في ملف .env"""
    
    print("📧 إعداد بريد Hostinger لـ ES-Gift")
    print("=" * 40)
    
    # معلومات بريد Hostinger
    print("📋 معلومات البريد:")
    print("البريد: business@es-gift.com")
    print("الخادم: SMTP Hostinger")
    
    # طلب كلمة المرور
    print("\n🔑 أدخل كلمة مرور البريد الإلكتروني:")
    password = input("كلمة المرور: ").strip()
    
    if not password:
        print("❌ كلمة المرور مطلوبة!")
        return False
    
    # إعدادات Hostinger SMTP
    email_settings = {
        'MAIL_SERVER': 'smtp.hostinger.com',
        'MAIL_PORT': '587',
        'MAIL_USE_TLS': 'True',
        'MAIL_USERNAME': 'business@es-gift.com',
        'MAIL_PASSWORD': password,
        'MAIL_DEFAULT_SENDER': 'business@es-gift.com'
    }
    
    # قراءة ملف .env الحالي
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = ""
    
    # تحديث أو إضافة إعدادات البريد
    for key, value in email_settings.items():
        if re.search(f'^{key}=', content, re.MULTILINE):
            content = re.sub(f'^{key}=.*$', f'{key}={value}', content, flags=re.MULTILINE)
        else:
            content += f"\n{key}={value}"
    
    # إضافة تعليق توضيحي
    comment = "\n# إعدادات بريد Hostinger - business@es-gift.com\n"
    if "# إعدادات بريد Hostinger" not in content:
        content = comment + content
    
    # حفظ الملف
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content.strip() + '\n')
        
        print("\n✅ تم تحديث إعدادات البريد بنجاح!")
        print("\n📋 الإعدادات المطبقة:")
        for key, value in email_settings.items():
            if 'PASSWORD' in key:
                print(f"   {key}: {'*' * len(value)}")
            else:
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ في حفظ الإعدادات: {e}")
        return False

def get_hostinger_smtp_settings():
    """عرض إعدادات SMTP الصحيحة لـ Hostinger"""
    
    print("\n📧 إعدادات SMTP لـ Hostinger:")
    print("=" * 35)
    
    settings = [
        ("خادم الإرسال (SMTP)", "smtp.hostinger.com"),
        ("المنفذ", "587 (TLS) أو 465 (SSL)"),
        ("التشفير", "TLS أو SSL"),
        ("المصادقة", "مطلوبة"),
        ("اسم المستخدم", "business@es-gift.com"),
        ("كلمة المرور", "كلمة مرور البريد الإلكتروني")
    ]
    
    for setting, value in settings:
        print(f"   {setting}: {value}")
    
    print("\n💡 ملاحظات:")
    print("   • استخدم نفس كلمة مرور البريد الإلكتروني")
    print("   • تأكد من تفعيل SMTP في لوحة تحكم Hostinger")
    print("   • المنفذ 587 مع TLS هو الأكثر شيوعاً")

def test_hostinger_connection():
    """اختبار الاتصال مع خادم Hostinger"""
    
    print("\n🧪 اختبار الاتصال مع خادم Hostinger...")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from dotenv import load_dotenv
        
        # تحميل الإعدادات
        load_dotenv(override=True)
        
        smtp_server = os.getenv('MAIL_SERVER', 'smtp.hostinger.com')
        smtp_port = int(os.getenv('MAIL_PORT', '587'))
        username = os.getenv('MAIL_USERNAME')
        password = os.getenv('MAIL_PASSWORD')
        
        if not username or not password:
            print("❌ إعدادات البريد غير مكتملة")
            return False
        
        print(f"🔗 الاتصال بـ: {smtp_server}:{smtp_port}")
        print(f"👤 المستخدم: {username}")
        
        # محاولة الاتصال
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        
        # إرسال بريد تجريبي
        msg = MIMEText("اختبار بريد Hostinger - ES-Gift", 'plain', 'utf-8')
        msg['Subject'] = "اختبار SMTP - ES-Gift"
        msg['From'] = username
        msg['To'] = username  # إرسال لنفس البريد
        
        server.send_message(msg)
        server.quit()
        
        print("✅ تم الاتصال والإرسال بنجاح!")
        print("📬 تحقق من صندوق البريد الوارد")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل الاتصال: {str(e)}")
        
        # نصائح لحل المشاكل
        print("\n💡 نصائح لحل المشكلة:")
        print("   1. تأكد من صحة كلمة المرور")
        print("   2. تأكد من تفعيل SMTP في Hostinger")
        print("   3. جرب المنفذ 465 مع SSL")
        print("   4. تحقق من إعدادات Firewall")
        
        return False

def create_hostinger_env_template():
    """إنشاء قالب .env لـ Hostinger"""
    
    template = """# إعدادات بريد Hostinger - ES-Gift
# =======================================

# إعدادات التطبيق الأساسية
SECRET_KEY=es-gift-super-secret-key-2025-for-oauth-sessions
DATABASE_URL=sqlite:///es_gift.db
FLASK_ENV=development
DEBUG=True

# إعدادات بريد Hostinger
MAIL_SERVER=smtp.hostinger.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=business@es-gift.com
MAIL_PASSWORD=your-email-password-here
MAIL_DEFAULT_SENDER=business@es-gift.com

# إعدادات Google OAuth
GOOGLE_CLIENT_ID=712420880804-hi84lrcs4igfplrm7mgp647v19g8sggk.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://es-gift.com/auth/google/callback

# إعدادات أخرى
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
WHATSAPP_NUMBER=+966123456789

# إعدادات الدفع
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret

# إعدادات API الخارجية
EXTERNAL_API_KEY=your-external-api-key
EXTERNAL_API_URL=https://api.example.com/products
"""
    
    print("\n📄 قالب ملف .env لـ Hostinger:")
    print("=" * 35)
    print("✅ تم إنشاء قالب جاهز للاستخدام")
    
    return template

def main():
    """الدالة الرئيسية"""
    
    print("🚀 مساعد إعداد بريد Hostinger - ES-Gift")
    print("=" * 50)
    
    print("📋 الخيارات المتاحة:")
    print("1. إعداد بريد Hostinger")
    print("2. عرض إعدادات SMTP")
    print("3. اختبار الاتصال")
    print("4. إنشاء قالب .env")
    print("0. خروج")
    
    while True:
        choice = input("\n🔹 اختر خيار (0-4): ").strip()
        
        if choice == '1':
            if setup_hostinger_email():
                print("\n🎉 تم الإعداد بنجاح!")
                test_choice = input("هل تريد اختبار الاتصال الآن؟ (y/n): ")
                if test_choice.lower() == 'y':
                    test_hostinger_connection()
        
        elif choice == '2':
            get_hostinger_smtp_settings()
        
        elif choice == '3':
            test_hostinger_connection()
        
        elif choice == '4':
            template = create_hostinger_env_template()
            save_choice = input("هل تريد حفظ القالب في ملف؟ (y/n): ")
            if save_choice.lower() == 'y':
                with open('.env.hostinger.template', 'w', encoding='utf-8') as f:
                    f.write(template)
                print("✅ تم حفظ القالب في .env.hostinger.template")
        
        elif choice == '0':
            print("👋 وداعاً!")
            break
        
        else:
            print("❌ خيار غير صحيح")

if __name__ == "__main__":
    main()
