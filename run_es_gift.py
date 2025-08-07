#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تشغيل سريع لتطبيق ES-GIFT مع النظام المحسن
==========================================
"""

import os
import sys
from flask import Flask

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_app():
    """إنشاء تطبيق Flask للاختبار"""
    app = Flask(__name__)
    
    # إعدادات أساسية
    app.config['SECRET_KEY'] = 'es-gift-test-key-2025'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/es_gift.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app

def test_email_services():
    """اختبار خدمات البريد الإلكتروني"""
    print("🚀 اختبار خدمات البريد الإلكتروني المحسنة")
    print("="*60)
    
    try:
        # اختبار Hostinger مع الإعدادات البديلة
        print("📧 اختبار Hostinger SMTP...")
        from send_by_hostinger import hostinger_email_service
        
        # تجربة الاتصال
        success, message = hostinger_email_service.test_connection()
        print(f"اختبار الاتصال: {'✅ نجح' if success else '❌ فشل'} - {message}")
        
        if not success:
            print("🔄 محاولة التبديل إلى الإعدادات البديلة...")
            hostinger_email_service._switch_to_fallback()
            success, message = hostinger_email_service.test_connection()
            print(f"اختبار الإعدادات البديلة: {'✅ نجح' if success else '❌ فشل'} - {message}")
        
        # اختبار Email Sender Pro
        print("\n🔌 اختبار Email Sender Pro...")
        from email_sender_pro_service import email_sender_service
        
        success, message = email_sender_service.test_connection()
        print(f"اختبار API: {'✅ نجح' if success else '❌ فشل'} - {message}")
        
        # اختبار الرصيد
        success, balance = email_sender_service.get_balance()
        if success:
            print(f"💰 رصيد API: {balance}")
        
        print("\n✅ اختبار الخدمات مكتمل!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        return False

def run_flask_app():
    """تشغيل تطبيق Flask"""
    try:
        print("🌐 تشغيل تطبيق ES-GIFT...")
        
        # تحقق من وجود app.py
        if os.path.exists('app.py'):
            print("📁 تم العثور على app.py")
            
            # تشغيل التطبيق
            os.system('python app.py')
        else:
            print("❌ لم يتم العثور على app.py")
            
            # إنشاء تطبيق اختبار بسيط
            app = create_test_app()
            
            @app.route('/')
            def index():
                return '''
                <h1>🎁 ES-GIFT - النظام المحسن</h1>
                <h2>✅ النظام يعمل بنجاح!</h2>
                <ul>
                    <li>📧 نظام البريد الإلكتروني محسن</li>
                    <li>🔄 دعم الإعدادات البديلة</li>
                    <li>📄 نظام الفواتير محسن</li>
                    <li>🎨 تصميم الفواتير محسن مع اللوجو</li>
                </ul>
                <p>الإعدادات البديلة: hanizezo72@gmail.com</p>
                '''
            
            @app.route('/test-email')
            def test_email():
                return '''
                <h2>اختبار النظام</h2>
                <p>يمكنك اختبار النظام باستخدام:</p>
                <pre>python test_email_systems.py</pre>
                '''
            
            print("🚀 تشغيل تطبيق الاختبار...")
            app.run(debug=True, host='0.0.0.0', port=5000)
            
    except Exception as e:
        print(f"❌ خطأ في تشغيل التطبيق: {e}")

def run_gunicorn():
    """تشغيل التطبيق باستخدام Gunicorn"""
    print("🚀 تشغيل التطبيق باستخدام Gunicorn...")
    print("🔄 بدء تشغيل الخادم...")
    
    try:
        # التحقق من وجود wsgi.py
        if not os.path.exists('wsgi.py'):
            print("❌ ملف wsgi.py غير موجود")
            return False
        
        # تشغيل Gunicorn
        cmd = 'gunicorn -w 4 -b 127.0.0.1:8000 wsgi:application'
        print(f"📋 تشغيل الأمر: {cmd}")
        os.system(cmd)
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل Gunicorn: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🎁 ES-GIFT - نظام محسن مع إعدادات بديلة")
    print("="*50)
    print("📧 الإعدادات البديلة:")
    print("   Email: hanizezo72@gmail.com")
    print("   Password: jxtr qylc lzkj ehpb")
    print("   SMTP: smtp.gmail.com:587")
    print("="*50)
    
    choice = input("""
اختر العملية:
1️⃣ - اختبار خدمات البريد الإلكتروني
2️⃣ - تشغيل تطبيق Flask (تطوير)
3️⃣ - اختبار التطبيق
4️⃣ - فحص النشر
5️⃣ - تشغيل مع Gunicorn (إنتاج)
6️⃣ - خروج

الاختيار: """)
    
    if choice == '1':
        test_email_services()
    elif choice == '2':
        run_flask_app()
    elif choice == '3':
        print("🧪 تشغيل اختبار التطبيق...")
        os.system('python test_app.py')
    elif choice == '4':
        print("🔍 فحص النشر...")
        os.system('python check_deployment.py')
    elif choice == '5':
        run_gunicorn()
    elif choice == '6':
        print("👋 وداعاً!")
    else:
        print("❌ اختيار غير صحيح")

if __name__ == "__main__":
    main()
