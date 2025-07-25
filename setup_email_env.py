#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مساعد إعداد ملف .env للبريد الإلكتروني
=====================================
"""

import os
import getpass

def create_secure_env_file():
    """إنشاء ملف .env آمن مع App Password"""
    
    print("🔧 مساعد إعداد البريد الإلكتروني - ES-Gift")
    print("=" * 50)
    
    # جمع المعلومات
    print("\n📧 أدخل معلومات البريد الإلكتروني:")
    
    email = input("عنوان البريد الإلكتروني (business@es-gift.com): ").strip()
    if not email:
        email = "business@es-gift.com"
    
    print(f"\n⚠️  هام: يجب أن تكون قد حصلت على App Password من Gmail")
    print("إذا لم تحصل عليها بعد، اتبع هذه الخطوات:")
    print("1. اذهب إلى: https://myaccount.google.com")
    print("2. Security > 2-Step Verification (فعّل إذا لم يكن مفعلاً)")
    print("3. Security > App passwords")
    print("4. اختر Mail > Other > اكتب 'ES-Gift'")
    print("5. انسخ كلمة المرور المولدة")
    
    app_password = getpass.getpass("\nApp Password (16 رقم/حرف): ").strip()
    
    if len(app_password) < 16:
        print("⚠️  تحذير: App Password عادة تكون 16 رقم/حرف")
        confirm = input("هل تريد المتابعة؟ (y/n): ")
        if confirm.lower() != 'y':
            print("❌ تم الإلغاء")
            return False
    
    # إنشاء محتوى ملف .env
    env_content = f"""# إعدادات التطبيق
SECRET_KEY=es-gift-super-secret-key-2025-for-oauth-sessions
DATABASE_URL=sqlite:///es_gift.db

# إعدادات البريد الإلكتروني
# تم إعداد هذا الملف بواسطة مساعد إعداد البريد الإلكتروني
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME={email}
MAIL_PASSWORD={app_password}
MAIL_DEFAULT_SENDER={email}

# إعدادات Google OAuth
GOOGLE_CLIENT_ID=712420880804-hi84lrcs4igfplrm7mgp647v19g8sggk.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://es-gift.com/auth/google/callback

# إعدادات الدفع
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret

# إعدادات API الخارجية
EXTERNAL_API_KEY=your-external-api-key
EXTERNAL_API_URL=https://api.example.com/products

# إعدادات أخرى
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
WHATSAPP_NUMBER=+966123456789
FLASK_ENV=development
DEBUG=True
"""
    
    # نسخ احتياطي من الملف الحالي
    if os.path.exists('.env'):
        backup_name = f'.env.backup.{int(__import__("time").time())}'
        os.rename('.env', backup_name)
        print(f"📁 تم إنشاء نسخة احتياطية: {backup_name}")
    
    # كتابة الملف الجديد
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("\n✅ تم إنشاء ملف .env جديد بنجاح!")
        
        # اختبار التحميل
        from dotenv import load_dotenv
        load_dotenv()
        
        if os.getenv('MAIL_USERNAME') == email:
            print("✅ تم تحميل الإعدادات بنجاح")
        else:
            print("❌ خطأ في تحميل الإعدادات")
            return False
        
        print("\n📋 الخطوات التالية:")
        print("1. شغل: python simple_email_test.py")
        print("2. إذا نجح، شغل: python test_email_send.py")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الملف: {e}")
        return False

if __name__ == "__main__":
    create_secure_env_file()
