# -*- coding: utf-8 -*-
"""
اختبار Gmail SMTP - ES-GIFT
============================

اختبار سريع لـ Gmail SMTP مع كلمة مرور التطبيق
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_smtp():
    """اختبار Gmail SMTP"""
    print("📧 اختبار Gmail SMTP...")
    print("=" * 50)
    
    # ملاحظة: يجب استبدال هذه بكلمة مرور التطبيق الحقيقية
    # احصل عليها من: https://myaccount.google.com/apppasswords
    app_password = "YOUR_16_DIGIT_APP_PASSWORD_HERE"
    
    if app_password == "YOUR_16_DIGIT_APP_PASSWORD_HERE":
        print("⚠️ يجب تحديث كلمة مرور التطبيق أولاً!")
        print("\n📝 خطوات الحصول على كلمة مرور التطبيق:")
        print("   1. اذهب إلى https://myaccount.google.com")
        print("   2. Security → 2-Step Verification (فعّل إذا لم يكن مفعلاً)")
        print("   3. App passwords → Generate new app password")
        print("   4. اختر 'Mail' و 'Other (custom name)' → ES-GIFT")
        print("   5. انسخ كلمة المرور المكونة من 16 رقم/حرف")
        print("   6. ضعها في هذا الملف مكان YOUR_16_DIGIT_APP_PASSWORD_HERE")
        print("\n🔄 ثم شغّل الاختبار مرة أخرى")
        return False
    
    # إعدادات Gmail SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "mohamedeloker9@gmail.com"
    
    print(f"🔗 الخادم: {smtp_server}:{smtp_port}")
    print(f"📧 المرسل: {sender_email}")
    print(f"🔑 كلمة المرور: {'*' * len(app_password)}")
    
    try:
        # إنشاء الرسالة
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🎉 اختبار Gmail SMTP - ES-GIFT"
        msg['From'] = sender_email
        msg['To'] = sender_email
        
        # محتوى HTML
        html_content = """
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <title>اختبار Gmail SMTP</title>
        </head>
        <body style="font-family: Arial, sans-serif; direction: rtl; padding: 20px; background: #f5f5f5;">
            
            <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 2em;">✅ نجح الاختبار!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 1.1em;">Gmail SMTP يعمل بشكل مثالي</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <h2 style="color: #333; margin-bottom: 20px;">🎁 ES-GIFT</h2>
                    
                    <div style="background: #e7f3ff; padding: 20px; border-radius: 10px; border-right: 4px solid #007bff; margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; color: #007bff;">✅ تم تكوين البريد بنجاح</h3>
                        <p style="margin: 0; color: #555;">
                            الآن يمكن إرسال:<br>
                            • رسائل التحقق للمستخدمين الجدد<br>
                            • تأكيد الطلبات<br>
                            • أكواد المنتجات<br>
                            • إشعارات النظام
                        </p>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 10px; border-right: 4px solid #ffc107;">
                        <p style="margin: 0; color: #856404; font-size: 14px;">
                            <strong>⚠️ تذكير:</strong> احتفظ بكلمة مرور التطبيق في مكان آمن ولا تشاركها مع أحد.
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        🎁 ES-GIFT - منصتك للبطاقات الرقمية
                    </p>
                </div>
                
            </div>
            
        </body>
        </html>
        """
        
        # إضافة المحتوى
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        print("\n🔄 جاري الاتصال بـ Gmail...")
        
        # إرسال الرسالة
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("🔐 تفعيل TLS...")
            server.starttls()
            
            print("🔑 تسجيل الدخول...")
            server.login(sender_email, app_password)
            
            print("📤 إرسال الرسالة...")
            server.send_message(msg)
        
        print("\n🎉 نجح الاختبار بشكل مثالي!")
        print("✅ Gmail SMTP يعمل وجاهز لإرسال الرسائل")
        print("📧 تحقق من بريدك الإلكتروني لرؤية رسالة الاختبار")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ خطأ في المصادقة: {e}")
        print("\n🔧 الحلول المحتملة:")
        print("   1. تأكد من صحة كلمة مرور التطبيق (16 رقم/حرف)")
        print("   2. تأكد من تفعيل التحقق بخطوتين في Google")
        print("   3. جرب إنشاء كلمة مرور تطبيق جديدة")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ خطأ في SMTP: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")
        return False

def update_env_file():
    """تحديث ملف .env مع إعدادات Gmail الصحيحة"""
    print("\n🔧 تحديث ملف .env...")
    
    try:
        # قراءة الملف
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # تحديث إعدادات Gmail
        if 'MAIL_PASSWORD=your_app_password_here' in content:
            print("⚠️ تذكر تحديث MAIL_PASSWORD في ملف .env")
            print("📝 ضع كلمة مرور التطبيق مكان 'your_app_password_here'")
        else:
            print("✅ إعدادات Gmail موجودة في .env")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تحديث .env: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🧪 اختبار Gmail SMTP لـ ES-GIFT")
    print("=" * 50)
    
    # اختبار Gmail
    if test_gmail_smtp():
        print("\n🎊 مبروك! البريد الإلكتروني يعمل الآن")
        print("\n💡 الخطوات التالية:")
        print("   1. ✅ تحديث ملف .env بكلمة مرور التطبيق")
        print("   2. ✅ إعادة تشغيل التطبيق")
        print("   3. ✅ اختبار تسجيل مستخدم جديد")
        print("   4. ✅ التحقق من وصول رسائل التحقق")
    else:
        print("\n🔧 يحتاج تحديث كلمة مرور التطبيق")
    
    # تحديث ملف .env
    update_env_file()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
