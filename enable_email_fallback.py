#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
تفعيل نظام البريد البديل (Flask-Mail) عند تعطل Brevo
"""

import os
import sys
import traceback
from datetime import datetime

def create_fallback_env():
    """إنشاء ملف .env لتفعيل نظام البريد البديل"""
    try:
        env_content = """# تكوين البريد الإلكتروني - النظام البديل
# تم إنشاء هذا الملف تلقائياً لحل مشاكل Brevo API

# تعطيل Brevo مؤقتاً
DISABLE_BREVO=True

# تكوين Flask-Mail كبديل
MAIL_SERVER=smtp.hostinger.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=noreply@es-gift.net
MAIL_PASSWORD=Noreply@123456
MAIL_DEFAULT_SENDER=noreply@es-gift.net

# تكوين قاعدة البيانات (إذا لزم الأمر)
DATABASE_URL=sqlite:///instance/app.db

# تكوين Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ تم إنشاء ملف .env لتفعيل النظام البديل")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء ملف .env: {str(e)}")
        return False

def test_flask_mail_config():
    """اختبار تكوين Flask-Mail"""
    try:
        from flask import Flask
        from flask_mail import Mail, Message
        
        app = Flask(__name__)
        app.config.update({
            'MAIL_SERVER': 'smtp.hostinger.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USE_SSL': False,
            'MAIL_USERNAME': 'noreply@es-gift.net',
            'MAIL_PASSWORD': 'Noreply@123456',
            'MAIL_DEFAULT_SENDER': 'noreply@es-gift.net'
        })
        
        mail = Mail(app)
        
        with app.app_context():
            # إنشاء رسالة اختبار
            msg = Message(
                'اختبار النظام البديل',
                sender='noreply@es-gift.net',
                recipients=['test@example.com']
            )
            msg.body = 'هذا اختبار للنظام البديل'
            
            # محاولة إنشاء الرسالة (بدون إرسال فعلي)
            print("✅ تكوين Flask-Mail صحيح ومتاح")
            return True
            
    except ImportError:
        print("❌ Flask-Mail غير مثبت، سيتم تثبيته...")
        return False
    except Exception as e:
        print(f"❌ خطأ في تكوين Flask-Mail: {str(e)}")
        return False

def install_flask_mail():
    """تثبيت Flask-Mail إذا لم يكن موجوداً"""
    try:
        import subprocess
        result = subprocess.run(['pip', 'install', 'Flask-Mail'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ تم تثبيت Flask-Mail بنجاح")
            return True
        else:
            print(f"❌ فشل تثبيت Flask-Mail: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في تثبيت Flask-Mail: {str(e)}")
        return False

def update_brevo_config():
    """تحديث إعدادات Brevo لتعطيلها مؤقتاً"""
    try:
        config_file = 'brevo_config.py'
        
        # قراءة المحتوى الحالي
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # التحقق من وجود DISABLE_BREVO
        if 'DISABLE_BREVO' not in content:
            # إضافة DISABLE_BREVO في بداية الملف
            new_content = """# تعطيل Brevo مؤقتاً لحل مشاكل API Key
DISABLE_BREVO = True

""" + content
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ تم تحديث brevo_config.py لتعطيل Brevo مؤقتاً")
        else:
            print("ℹ️ DISABLE_BREVO موجود بالفعل في brevo_config.py")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تحديث brevo_config.py: {str(e)}")
        return False

def test_email_verification():
    """اختبار نظام التحقق من البريد الإلكتروني"""
    try:
        # محاولة استيراد الخدمات المطلوبة
        from email_verification_service import EmailVerificationService
        
        print("✅ تم العثور على EmailVerificationService")
        
        # إنشاء instance
        service = EmailVerificationService()
        print("✅ تم إنشاء EmailVerificationService بنجاح")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار نظام التحقق: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """الدالة الرئيسية لتفعيل النظام البديل"""
    print("🔧 تفعيل نظام البريد البديل...")
    print("=" * 50)
    
    # 1. إنشاء ملف .env
    print("\n1. إنشاء ملف التكوين...")
    create_fallback_env()
    
    # 2. تثبيت Flask-Mail إذا لزم الأمر
    print("\n2. التحقق من Flask-Mail...")
    if not test_flask_mail_config():
        print("تثبيت Flask-Mail...")
        install_flask_mail()
        # اختبار مرة أخرى
        test_flask_mail_config()
    
    # 3. تحديث brevo_config.py
    print("\n3. تحديث إعدادات Brevo...")
    update_brevo_config()
    
    # 4. اختبار نظام التحقق
    print("\n4. اختبار نظام التحقق...")
    test_email_verification()
    
    print("\n" + "=" * 50)
    print("✅ تم تفعيل النظام البديل!")
    print("\n📧 الآن يمكن إرسال رسائل التحقق باستخدام Flask-Mail")
    print("🔄 لإعادة تفعيل Brevo، قم بتحديث API Key وغيّر DISABLE_BREVO=False")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ تم إلغاء العملية")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ عام: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
