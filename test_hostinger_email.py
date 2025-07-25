#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار بريد Hostinger البسيط
===========================
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

def test_hostinger_smtp():
    """اختبار SMTP مع Hostinger"""
    
    print("📧 اختبار بريد Hostinger - ES-Gift")
    print("=" * 40)
    
    # تحميل إعدادات البيئة
    load_dotenv(override=True)
    
    # إعدادات Hostinger
    smtp_server = "smtp.hostinger.com"
    smtp_port = 587
    username = "business@es-gift.com"
    
    # طلب كلمة المرور إذا لم تكن محددة
    password = os.getenv('MAIL_PASSWORD')
    if not password or password == 'your-email-password-here':
        print("🔑 أدخل كلمة مرور بريد business@es-gift.com:")
        password = input("كلمة المرور: ").strip()
        
        if not password:
            print("❌ كلمة المرور مطلوبة!")
            return False
    
    try:
        print(f"\n🔗 الاتصال بـ: {smtp_server}:{smtp_port}")
        print(f"👤 المستخدم: {username}")
        
        # إنشاء اتصال SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        # تفعيل وضع debug (اختياري)
        # server.set_debuglevel(1)
        
        print("🔐 بدء التشفير TLS...")
        server.starttls()
        
        print("🔑 محاولة تسجيل الدخول...")
        server.login(username, password)
        
        print("✅ تم تسجيل الدخول بنجاح!")
        
        # إنشاء رسالة اختبار
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username
        msg['Subject'] = "اختبار SMTP - ES-Gift Hostinger"
        
        # محتوى الرسالة
        body = """
        مرحباً!
        
        هذا اختبار لخادم SMTP الخاص بـ Hostinger.
        
        إذا وصلتك هذه الرسالة، فإن إعدادات البريد تعمل بشكل صحيح.
        
        تحياتي،
        نظام ES-Gift
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        print("📨 إرسال رسالة اختبار...")
        text = msg.as_string()
        server.sendmail(username, username, text)
        
        print("✅ تم إرسال الرسالة بنجاح!")
        print(f"📬 تحقق من صندوق البريد: {username}")
        
        server.quit()
        
        # تحديث ملف .env بكلمة المرور الصحيحة
        if os.getenv('MAIL_PASSWORD') != password:
            update_env_password(password)
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ خطأ في المصادقة: {e}")
        print("💡 تأكد من:")
        print("   • صحة كلمة المرور")
        print("   • تفعيل SMTP في لوحة تحكم Hostinger")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ خطأ في الاتصال: {e}")
        print("💡 تحقق من:")
        print("   • اتصال الإنترنت")
        print("   • إعدادات Firewall")
        return False
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False

def update_env_password(password):
    """تحديث كلمة المرور في ملف .env"""
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # استبدال كلمة المرور
        import re
        content = re.sub(
            r'^MAIL_PASSWORD=.*$', 
            f'MAIL_PASSWORD={password}', 
            content, 
            flags=re.MULTILINE
        )
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ تم تحديث ملف .env بكلمة المرور الصحيحة")
        
    except Exception as e:
        print(f"⚠️ لم يتم تحديث ملف .env: {e}")

def show_hostinger_settings():
    """عرض إعدادات Hostinger الصحيحة"""
    
    print("\n📋 إعدادات SMTP لـ Hostinger:")
    print("=" * 35)
    print("خادم الإرسال: smtp.hostinger.com")
    print("المنفذ: 587 (TLS)")
    print("التشفير: TLS")
    print("المصادقة: مطلوبة")
    print("اسم المستخدم: business@es-gift.com")
    print("كلمة المرور: كلمة مرور البريد الإلكتروني")
    
    print("\n💡 ملاحظات:")
    print("• استخدم كلمة مرور البريد العادية (ليس App Password)")
    print("• تأكد من تفعيل SMTP في لوحة تحكم Hostinger")
    print("• يمكن أيضاً استخدام المنفذ 465 مع SSL")

if __name__ == "__main__":
    print("🧪 اختبار بريد Hostinger - ES-Gift")
    print("=" * 45)
    
    show_hostinger_settings()
    
    print("\n" + "=" * 45)
    
    if test_hostinger_smtp():
        print("\n🎉 اختبار البريد نجح!")
        print("📋 الخطوات التالية:")
        print("1. جرب: python test_email_send.py")
        print("2. اختبر من واجهة الإدارة")
    else:
        print("\n❌ فشل اختبار البريد")
        print("💡 راجع الإعدادات وحاول مرة أخرى")
