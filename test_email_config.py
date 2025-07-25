#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إعدادات البريد الإلكتروني
===============================
"""

import os
from flask import Flask
from flask_mail import Mail, Message
from config import Config

def test_email_configuration():
    """اختبار إعدادات البريد الإلكتروني"""
    
    print("🔍 فحص إعدادات البريد الإلكتروني...")
    print("=" * 50)
    
    # إنشاء تطبيق Flask مؤقت للاختبار
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # طباعة الإعدادات الحالية
    print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"MAIL_USERNAME: {'****' if app.config.get('MAIL_USERNAME') else 'غير محدد'}")
    print(f"MAIL_PASSWORD: {'****' if app.config.get('MAIL_PASSWORD') else 'غير محدد'}")
    print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER', 'غير محدد')}")
    
    print("\n" + "=" * 50)
    
    # فحص متغيرات البيئة
    print("🌍 متغيرات البيئة:")
    print(f"MAIL_USERNAME من البيئة: {'موجود' if os.getenv('MAIL_USERNAME') else 'غير موجود'}")
    print(f"MAIL_PASSWORD من البيئة: {'موجود' if os.getenv('MAIL_PASSWORD') else 'غير موجود'}")
    
    # التحقق من وجود إعدادات البريد
    if not app.config.get('MAIL_USERNAME'):
        print("\n❌ خطأ: MAIL_USERNAME غير محدد!")
        print("💡 حل المشكلة:")
        print("   1. أنشئ ملف .env في المجلد الرئيسي")
        print("   2. أضف المتغيرات التالية:")
        print("      MAIL_USERNAME=your-email@gmail.com")
        print("      MAIL_PASSWORD=your-app-specific-password")
        return False
    
    if not app.config.get('MAIL_PASSWORD'):
        print("\n❌ خطأ: MAIL_PASSWORD غير محدد!")
        return False
    
    # تهيئة Flask-Mail
    try:
        mail = Mail(app)
        print("\n✅ تم تهيئة Flask-Mail بنجاح")
    except Exception as e:
        print(f"\n❌ خطأ في تهيئة Flask-Mail: {e}")
        return False
    
    return True

def create_env_file_example():
    """إنشاء ملف .env مثال"""
    
    env_content = """# إعدادات البريد الإلكتروني
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True

# إعدادات Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://es-gift.com/auth/google/callback

# إعدادات أخرى
SECRET_KEY=es-gift-super-secret-key-2025-for-oauth-sessions
DATABASE_URL=sqlite:///es_gift.db
FLASK_ENV=development
DEBUG=True
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ تم إنشاء ملف .env مثال")
        print("📝 يرجى تحديث الملف بالقيم الصحيحة")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء ملف .env: {e}")
        return False

def test_gmail_settings():
    """فحص إعدادات Gmail"""
    
    print("\n📧 فحص إعدادات Gmail:")
    print("=" * 30)
    
    print("للحصول على App Password من Gmail:")
    print("1. اذهب إلى myaccount.google.com")
    print("2. اختر 'Security' من القائمة اليسرى")
    print("3. تأكد من تفعيل 2-Step Verification")
    print("4. اذهب إلى 'App passwords'")
    print("5. اختر 'Mail' كتطبيق و 'Other' كجهاز")
    print("6. أدخل اسم التطبيق (مثل: ES-Gift)")
    print("7. انسخ كلمة المرور المولدة واستخدمها في MAIL_PASSWORD")

def check_email_service_integration():
    """فحص تكامل خدمة البريد الإلكتروني"""
    
    print("\n🔧 فحص تكامل خدمة البريد الإلكتروني:")
    print("=" * 40)
    
    try:
        from email_service import email_service, init_email_service
        print("✅ تم استيراد email_service بنجاح")
        
        # فحص ما إذا كانت الخدمة مهيأة في التطبيق الرئيسي
        print("❓ هل تم تهيئة email_service في app.py؟")
        
        # قراءة ملف app.py للتحقق
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
            
        if 'init_email_service' in app_content:
            print("✅ تم العثور على init_email_service في app.py")
        else:
            print("❌ لم يتم العثور على init_email_service في app.py")
            print("💡 يجب إضافة السطر التالي في app.py:")
            print("   from email_service import init_email_service")
            print("   init_email_service(app)")
            
    except ImportError as e:
        print(f"❌ خطأ في استيراد email_service: {e}")

if __name__ == "__main__":
    print("🧪 اختبار إعدادات البريد الإلكتروني لـ ES-Gift")
    print("=" * 60)
    
    # فحص الإعدادات
    if test_email_configuration():
        print("\n✅ إعدادات البريد الإلكتروني صحيحة")
    else:
        print("\n❌ هناك مشاكل في إعدادات البريد الإلكتروني")
        
        # إنشاء ملف .env مثال
        print("\n📁 هل تريد إنشاء ملف .env مثال؟ (y/n): ", end="")
        choice = input().lower()
        if choice == 'y':
            create_env_file_example()
    
    # فحص إعدادات Gmail
    test_gmail_settings()
    
    # فحص تكامل الخدمة
    check_email_service_integration()
    
    print("\n" + "=" * 60)
    print("🏁 انتهى الاختبار")
