import secrets
import hashlib
from datetime import datetime, timedelta
from flask import current_app, url_for
from brevo_email_service import send_verification_email as brevo_send_verification, send_simple_email
import os


class EmailVerificationService:
    """خدمة التحقق من البريد الإلكتروني"""
    
    @staticmethod
    def generate_verification_token():
        """إنشاء رمز تحقق آمن"""
        token = secrets.token_urlsafe(32)
        return hashlib.sha256(token.encode()).hexdigest()[:32]
    
    @staticmethod
    def send_verification_email(user):
        """إرسال بريد التحقق من الحساب باستخدام Brevo"""
        try:
            # استخدام خدمة Brevo المتكاملة
            from brevo_integration import send_verification_email_brevo
            
            success = send_verification_email_brevo(user)
            
            if success:
                print(f"✅ تم إرسال بريد التحقق إلى: {user.email} باستخدام Brevo")
                return True
            else:
                print(f"❌ فشل إرسال بريد التحقق باستخدام Brevo")
                # العودة للطريقة التقليدية
                return EmailVerificationService._send_verification_email_fallback(user)
            
        except Exception as e:
            print(f"خطأ في إرسال بريد التحقق: {str(e)}")
            return EmailVerificationService._send_verification_email_fallback(user)
    
    @staticmethod
    def _send_verification_email_fallback(user):
        """إرسال بريد التحقق بالطريقة التقليدية (كبديل)"""
        try:
            # إنشاء رمز التحقق
            verification_token = EmailVerificationService.generate_verification_token()
            
            # حفظ رمز التحقق في قاعدة البيانات
            from models import db
            user.email_verification_token = verification_token
            user.email_verification_sent_at = datetime.utcnow()
            db.session.commit()
            
            # إنشاء رابط التحقق
            verification_url = url_for('main.verify_email', 
                                     token=verification_token, 
                                     _external=True)
            
            # محتوى البريد الإلكتروني
            email_html = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>✉️ تحقق من حسابك - ES-GIFT</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        min-height: 100vh;
                        direction: rtl;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 20px;
                        overflow: hidden;
                        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 40px 30px;
                        text-align: center;
                        color: white;
                    }}
                    .logo {{
                        font-size: 2.5em;
                        margin-bottom: 10px;
                    }}
                    .header-title {{
                        font-size: 1.8em;
                        margin: 0;
                        font-weight: bold;
                    }}
                    .header-subtitle {{
                        font-size: 1.1em;
                        margin: 10px 0 0 0;
                        opacity: 0.9;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .welcome-msg {{
                        font-size: 1.4em;
                        color: #333;
                        margin-bottom: 20px;
                        text-align: center;
                    }}
                    .message {{
                        font-size: 1.1em;
                        line-height: 1.8;
                        color: #555;
                        margin-bottom: 30px;
                        text-align: center;
                    }}
                    .verify-btn {{
                        display: inline-block;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 15px 40px;
                        text-decoration: none;
                        border-radius: 50px;
                        font-size: 1.2em;
                        font-weight: bold;
                        text-align: center;
                        transition: all 0.3s ease;
                        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                    }}
                    .verify-btn:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
                    }}
                    .button-container {{
                        text-align: center;
                        margin: 30px 0;
                    }}
                    .alternative-text {{
                        font-size: 0.9em;
                        color: #777;
                        margin-top: 30px;
                        padding: 20px;
                        background: #f8f9fa;
                        border-radius: 10px;
                        text-align: center;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 30px;
                        text-align: center;
                        color: #666;
                        font-size: 0.9em;
                    }}
                    .security-note {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        padding: 15px;
                        border-radius: 10px;
                        margin: 20px 0;
                        color: #856404;
                    }}
                    .features {{
                        display: flex;
                        justify-content: space-around;
                        margin: 30px 0;
                        flex-wrap: wrap;
                    }}
                    .feature {{
                        text-align: center;
                        margin: 10px;
                        flex: 1;
                        min-width: 150px;
                    }}
                    .feature-icon {{
                        font-size: 2em;
                        margin-bottom: 10px;
                    }}
                    .feature-text {{
                        font-size: 0.9em;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <div class="logo">🎁</div>
                        <h1 class="header-title">ES-GIFT</h1>
                        <p class="header-subtitle">أهلاً بك في عائلتنا!</p>
                    </div>
                    
                    <div class="content">
                        <h2 class="welcome-msg">مرحباً {user.full_name or 'عزيزي العميل'}! 👋</h2>
                        
                        <div class="message">
                            شكراً لانضمامك إلى ES-GIFT! نحن سعداء جداً لوجودك معنا.<br>
                            لإكمال تسجيل حسابك والبدء في استخدام خدماتنا الرائعة، يرجى تأكيد بريدك الإلكتروني بالنقر على الزر أدناه:
                        </div>
                        
                        <div class="button-container">
                            <a href="{verification_url}" class="verify-btn">
                                ✅ تأكيد البريد الإلكتروني
                            </a>
                        </div>
                        
                        <div class="features">
                            <div class="feature">
                                <div class="feature-icon">🎫</div>
                                <div class="feature-text">بطاقات هدايا متنوعة</div>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">💸</div>
                                <div class="feature-text">أسعار مميزة</div>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">⚡</div>
                                <div class="feature-text">تسليم فوري</div>
                            </div>
                        </div>
                        
                        <div class="security-note">
                            <strong>ملاحظة أمنية:</strong> هذا الرابط صالح لمدة 24 ساعة فقط. إذا لم تقم بالتسجيل، يرجى تجاهل هذا البريد.
                        </div>
                        
                        <div class="alternative-text">
                            إذا لم يعمل الزر أعلاه، يمكنك نسخ الرابط التالي ولصقه في متصفحك:<br>
                            <a href="{verification_url}" style="color: #667eea; word-break: break-all;">{verification_url}</a>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>شكراً لاختيارك ES-GIFT - وجهتك الأولى للبطاقات الرقمية</p>
                        <p>إذا كان لديك أي استفسار، لا تتردد في التواصل معنا</p>
                        <p style="margin-top: 20px; font-size: 0.8em; color: #999;">
                            هذا البريد تم إرساله تلقائياً، يرجى عدم الرد عليه مباشرة
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # إرسال البريد الإلكتروني باستخدام Brevo
            subject = "✉️ تأكيد حسابك في ES-GIFT - مرحباً بك!"
            
            # محاولة استخدام قالب Brevo أولاً
            success, message = brevo_send_verification(
                user_email=user.email,
                user_name=user.full_name or user.username or 'عزيزي العميل',
                verification_url=verification_url
            )
            
            if success:
                print(f"تم إرسال بريد التحقق إلى: {user.email} باستخدام Brevo")
                return True
            else:
                print(f"فشل إرسال بريد التحقق باستخدام Brevo: {message}")
                # كبديل، استخدام الطريقة التقليدية
                fallback_success, fallback_message = send_simple_email(
                    to=user.email,
                    subject=subject,
                    html_content=email_html
                )
                
                if fallback_success:
                    print(f"تم إرسال بريد التحقق إلى: {user.email} باستخدام الطريقة البديلة")
                    return True
                else:
                    print(f"فشل في إرسال بريد التحقق إلى: {user.email}")
                    return False
            
        except Exception as e:
            print(f"خطأ في إرسال بريد التحقق: {str(e)}")
            return False
    
    @staticmethod
    def verify_token(token):
        """التحقق من صحة رمز التحقق"""
        try:
            from models import User
            
            # البحث عن المستخدم بالرمز
            user = User.query.filter_by(email_verification_token=token).first()
            
            if not user:
                return False, "رمز التحقق غير صالح"
            
            # التحقق من انتهاء صلاحية الرمز (24 ساعة)
            if user.email_verification_sent_at:
                time_diff = datetime.utcnow() - user.email_verification_sent_at
                if time_diff > timedelta(hours=24):
                    return False, "انتهت صلاحية رمز التحقق. يرجى طلب رمز جديد"
            
            return True, user
            
        except Exception as e:
            print(f"خطأ في التحقق من الرمز: {str(e)}")
            return False, "حدث خطأ في التحقق من الرمز"
    
    @staticmethod
    def resend_verification_email(user):
        """إعادة إرسال بريد التحقق"""
        try:
            # التحقق من عدم التحقق من الحساب مسبقاً
            if user.is_verified:
                return False, "تم التحقق من هذا الحساب مسبقاً"
            
            # التحقق من عدم إرسال بريد خلال آخر 5 دقائق
            if user.email_verification_sent_at:
                time_diff = datetime.utcnow() - user.email_verification_sent_at
                if time_diff < timedelta(minutes=5):
                    remaining_time = 5 - int(time_diff.total_seconds() / 60)
                    return False, f"يرجى الانتظار {remaining_time} دقيقة قبل طلب رمز جديد"
            
            # إرسال بريد التحقق
            success = EmailVerificationService.send_verification_email(user)
            
            if success:
                return True, "تم إرسال بريد التحقق بنجاح"
            else:
                return False, "حدث خطأ في إرسال بريد التحقق"
                
        except Exception as e:
            print(f"خطأ في إعادة إرسال بريد التحقق: {str(e)}")
            return False, "حدث خطأ في إعادة إرسال بريد التحقق"
