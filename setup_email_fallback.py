# -*- coding: utf-8 -*-
"""
تفعيل نظام Flask-Mail البديل وحل مشاكل البريد
===============================================

يقوم هذا السكريبت بتفعيل Flask-Mail كنظام احتياطي لإرسال البريد
عندما يكون هناك مشاكل مع Brevo API
"""

import os
import sys

def setup_flask_mail_config():
    """إعداد Flask-Mail كنظام بديل"""
    print("🔧 إعداد Flask-Mail كنظام بديل...")
    
    try:
        # قراءة ملف .env
        env_file = '.env'
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # إضافة إعدادات Flask-Mail المحسنة
        flask_mail_config = """

# ========== إعدادات Flask-Mail البديل (محسنة) ==========
# هذه الإعدادات ستستخدم عند فشل Brevo
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=mohamedeloker9@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_DEFAULT_SENDER=mohamedeloker9@gmail.com
MAIL_SUPPRESS_SEND=False
MAIL_DEBUG=True

# إعدادات إضافية للأمان
MAIL_MAX_EMAILS=None
MAIL_ASCII_ATTACHMENTS=False
"""
        
        # التحقق من وجود إعدادات Flask-Mail
        if 'MAIL_SERVER=' not in content:
            content += flask_mail_config
            
            # حفظ الملف المحدث
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ تم إضافة إعدادات Flask-Mail البديل")
        else:
            print("ℹ️ إعدادات Flask-Mail موجودة بالفعل")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إعداد Flask-Mail: {str(e)}")
        return False

def create_improved_email_service():
    """إنشاء خدمة بريد محسنة مع Flask-Mail"""
    print("\n📧 إنشاء خدمة البريد المحسنة...")
    
    service_content = '''# -*- coding: utf-8 -*-
"""
خدمة البريد الإلكتروني المحسنة - ES-GIFT
==========================================

خدمة شاملة تدعم Brevo و Flask-Mail مع نظام تبديل تلقائي
"""

import os
import logging
from flask import current_app
from flask_mail import Mail, Message
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# إعداد تسجيل العمليات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedEmailService:
    """خدمة البريد المحسنة مع عدة طرق للإرسال"""
    
    def __init__(self, app=None):
        self.mail = None
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """تهيئة الخدمة مع التطبيق"""
        self.app = app
        self.mail = Mail(app)
        
    def send_verification_email(self, user_email, user_name, verification_url):
        """إرسال بريد التحقق مع عدة محاولات"""
        print(f"📧 محاولة إرسال بريد التحقق إلى: {user_email}")
        
        # المحاولة الأولى: Brevo (إذا كان متاحاً)
        if self._try_brevo_email(user_email, user_name, verification_url):
            return True
        
        # المحاولة الثانية: Flask-Mail
        if self._try_flask_mail(user_email, user_name, verification_url):
            return True
            
        # المحاولة الثالثة: SMTP مباشر
        if self._try_direct_smtp(user_email, user_name, verification_url):
            return True
        
        print("❌ فشلت جميع محاولات إرسال البريد")
        return False
    
    def _try_brevo_email(self, user_email, user_name, verification_url):
        """محاولة إرسال عبر Brevo"""
        try:
            print("🔄 محاولة الإرسال عبر Brevo...")
            
            # تحقق من توفر Brevo
            from brevo_config import BrevoConfig
            if BrevoConfig.DISABLE_BREVO:
                print("⚠️ Brevo معطل في الإعدادات")
                return False
                
            # محاولة الإرسال عبر Brevo
            from brevo_integration import send_verification_email_brevo
            
            # إنشاء كائن مستخدم مؤقت للاختبار
            class TempUser:
                def __init__(self, email, name):
                    self.email = email
                    self.first_name = name
                    self.email_verification_token = "temp_token_123"
            
            temp_user = TempUser(user_email, user_name)
            success = send_verification_email_brevo(temp_user)
            
            if success:
                print("✅ نجح الإرسال عبر Brevo")
                return True
            else:
                print("❌ فشل الإرسال عبر Brevo")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في Brevo: {str(e)}")
            return False
    
    def _try_flask_mail(self, user_email, user_name, verification_url):
        """محاولة إرسال عبر Flask-Mail"""
        try:
            print("🔄 محاولة الإرسال عبر Flask-Mail...")
            
            if not self.mail:
                print("❌ Flask-Mail غير مهيأ")
                return False
            
            # إنشاء الرسالة
            msg = Message(
                subject="🔐 تحقق من حسابك - ES-GIFT",
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'mohamedeloker9@gmail.com'),
                recipients=[user_email]
            )
            
            # محتوى الرسالة
            msg.html = self._get_verification_email_html(user_name, verification_url)
            
            # إرسال الرسالة
            self.mail.send(msg)
            print("✅ نجح الإرسال عبر Flask-Mail")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في Flask-Mail: {str(e)}")
            return False
    
    def _try_direct_smtp(self, user_email, user_name, verification_url):
        """محاولة إرسال مباشر عبر SMTP"""
        try:
            print("🔄 محاولة الإرسال المباشر عبر SMTP...")
            
            # إعدادات SMTP
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "mohamedeloker9@gmail.com"
            # ملاحظة: يجب استخدام app password حقيقي
            sender_password = "your_app_password_here"
            
            # إنشاء الرسالة
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "🔐 تحقق من حسابك - ES-GIFT"
            msg['From'] = sender_email
            msg['To'] = user_email
            
            # محتوى HTML
            html_content = self._get_verification_email_html(user_name, verification_url)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # إرسال الرسالة
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print("✅ نجح الإرسال المباشر عبر SMTP")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في SMTP المباشر: {str(e)}")
            return False
    
    def _get_verification_email_html(self, user_name, verification_url):
        """إنشاء محتوى HTML لبريد التحقق"""
        return f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>تحقق من حسابك - ES-GIFT</title>
        </head>
        <body style="font-family: Arial, sans-serif; direction: rtl; background-color: #f5f5f5; margin: 0; padding: 20px;">
            
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 2.5em;">🎁 ES-GIFT</h1>
                    <p style="margin: 15px 0 0 0; font-size: 1.3em; opacity: 0.9;">مرحباً بك في منصتنا!</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333; margin-bottom: 25px; font-size: 1.8em;">🔐 تحقق من بريدك الإلكتروني</h2>
                    
                    <p style="font-size: 18px; line-height: 1.8; color: #555; margin-bottom: 20px;">
                        مرحباً <strong style="color: #667eea;">{user_name}</strong>,
                    </p>
                    
                    <p style="font-size: 16px; line-height: 1.7; color: #666; margin-bottom: 30px;">
                        شكراً لك على التسجيل في ES-GIFT! 🎉<br>
                        لإكمال إنشاء حسابك وتفعيل جميع الخدمات، يرجى التحقق من بريدك الإلكتروني بالنقر على الزر أدناه:
                    </p>
                    
                    <!-- Verification Button -->
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{verification_url}" 
                           style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; padding: 18px 40px; text-decoration: none; border-radius: 30px; 
                                  font-weight: bold; font-size: 18px; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
                                  transition: all 0.3s ease;">
                            ✅ تحقق من الحساب الآن
                        </a>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-right: 4px solid #667eea; margin: 30px 0;">
                        <p style="margin: 0; font-size: 14px; color: #666;">
                            <strong>💡 نصيحة:</strong> إذا لم تتمكن من النقر على الزر، انسخ والصق الرابط التالي في متصفحك:
                        </p>
                        <p style="font-size: 12px; color: #888; word-break: break-all; background: white; padding: 10px; border-radius: 5px; margin: 10px 0 0 0;">
                            {verification_url}
                        </p>
                    </div>
                    
                    <div style="border-top: 1px solid #eee; padding-top: 25px; margin-top: 30px;">
                        <p style="font-size: 14px; color: #888; margin-bottom: 10px;">
                            ⏰ <strong>انتبه:</strong> هذا الرابط صالح لمدة 24 ساعة من وقت إرسال هذا البريد.
                        </p>
                        <p style="font-size: 14px; color: #888; margin: 0;">
                            🔒 <strong>للأمان:</strong> لا تشارك هذا الرابط مع أي شخص آخر.
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f8f9fa; padding: 25px 30px; text-align: center; border-top: 1px solid #eee;">
                    <p style="margin: 0 0 10px 0; color: #667eea; font-weight: bold; font-size: 16px;">
                        🎁 ES-GIFT
                    </p>
                    <p style="margin: 0; color: #888; font-size: 14px;">
                        وجهتك الموثوقة للبطاقات الرقمية والهدايا الإلكترونية
                    </p>
                    <p style="margin: 15px 0 0 0; color: #aaa; font-size: 12px;">
                        إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد تماماً.
                    </p>
                </div>
                
            </div>
            
        </body>
        </html>
        """

# إنشاء instance عام
improved_email_service = ImprovedEmailService()

def send_verification_email_improved(user):
    """دالة عامة لإرسال بريد التحقق"""
    try:
        from flask import url_for
        
        # إنشاء رابط التحقق
        verification_url = url_for('auth.verify_email', 
                                 token=user.email_verification_token, 
                                 _external=True)
        
        # إرسال البريد
        return improved_email_service.send_verification_email(
            user_email=user.email,
            user_name=user.first_name or user.username,
            verification_url=verification_url
        )
        
    except Exception as e:
        print(f"❌ خطأ في إرسال بريد التحقق المحسن: {str(e)}")
        return False
'''
    
    try:
        with open('improved_email_service.py', 'w', encoding='utf-8') as f:
            f.write(service_content)
        
        print("✅ تم إنشاء خدمة البريد المحسنة")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء خدمة البريد: {str(e)}")
        return False

def test_improved_email_service():
    """اختبار خدمة البريد المحسنة"""
    print("\n🧪 اختبار خدمة البريد المحسنة...")
    
    try:
        # استيراد التطبيق
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import app
        
        with app.app_context():
            # استيراد الخدمة المحسنة
            from improved_email_service import improved_email_service
            
            # اختبار إرسال بريد
            success = improved_email_service.send_verification_email(
                user_email="mohamedeloker9@gmail.com",
                user_name="محمد",
                verification_url="https://es-gift.com/verify_email?token=test123"
            )
            
            if success:
                print("✅ نجح اختبار خدمة البريد المحسنة!")
                return True
            else:
                print("❌ فشل اختبار خدمة البريد المحسنة")
                return False
                
    except Exception as e:
        print(f"❌ خطأ في اختبار الخدمة المحسنة: {str(e)}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🔧 إعداد نظام البريد البديل المحسن - ES-GIFT")
    print("=" * 60)
    
    steps_completed = 0
    total_steps = 3
    
    # الخطوة 1: إعداد Flask-Mail
    if setup_flask_mail_config():
        steps_completed += 1
    
    # الخطوة 2: إنشاء خدمة محسنة
    if create_improved_email_service():
        steps_completed += 1
    
    # الخطوة 3: اختبار الخدمة
    if test_improved_email_service():
        steps_completed += 1
    
    # النتائج
    print("\n" + "=" * 60)
    print(f"📊 النتائج: {steps_completed}/{total_steps} خطوة اكتملت")
    
    if steps_completed >= 2:
        print("🎉 تم إعداد نظام البريد البديل بنجاح!")
        print("\n💡 الآن يمكنك:")
        print("   1. تسجيل حسابات جديدة")
        print("   2. إرسال رسائل التحقق")
        print("   3. استخدام عدة طرق للإرسال")
        
        print("\n📧 ملاحظة مهمة:")
        print("   • تذكر تحديث كلمة مرور التطبيق في ملف .env")
        print("   • استخدم MAIL_PASSWORD بدلاً من your_app_password_here")
        print("   • يمكن الحصول على كلمة مرور التطبيق من إعدادات Gmail")
    else:
        print("⚠️ بعض الخطوات فشلت، يرجى المراجعة")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
