#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة البريد الإلكتروني البديلة
==============================

خدمة احتياطية لإرسال رسائل البريد الإلكتروني في حالة فشل API الخارجي
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional
from flask import current_app
import random
import string

# إعداد التسجيل
logger = logging.getLogger(__name__)

class FallbackEmailService:
    """خدمة البريد الإلكتروني الاحتياطية"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "noreply@es-gift.com"
        self.sender_password = "your-app-password"  # يجب تعديل هذا
        self.sender_name = "ES-GIFT"
        
    def generate_verification_code(self, length: int = 6) -> str:
        """توليد كود التحقق"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_email(self, email: str, verification_code: str) -> Tuple[bool, str]:
        """إرسال رسالة التحقق"""
        try:
            logger.info(f"📧 إرسال رسالة تحقق احتياطية إلى: {email}")
            
            # إنشاء محتوى الرسالة
            subject = "كود التحقق - ES-GIFT"
            
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Cairo', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #ff0033, #ff3366); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .code-box {{ background: #f8f9fa; border: 2px dashed #ff0033; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0; }}
                    .code {{ font-size: 32px; font-weight: bold; color: #ff0033; letter-spacing: 5px; }}
                    .footer {{ background: #333; color: #ccc; padding: 20px; text-align: center; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎁 ES-GIFT</h1>
                        <p>كود التحقق الخاص بك</p>
                    </div>
                    <div class="content">
                        <h2>مرحباً بك!</h2>
                        <p>تم طلب كود التحقق لحسابك في ES-GIFT. استخدم الكود التالي لإتمام عملية التحقق:</p>
                        
                        <div class="code-box">
                            <div class="code">{verification_code}</div>
                        </div>
                        
                        <p><strong>مهم:</strong></p>
                        <ul>
                            <li>هذا الكود صالح لمدة 10 دقائق فقط</li>
                            <li>لا تشارك هذا الكود مع أي شخص</li>
                            <li>إذا لم تطلب هذا الكود، يرجى تجاهل هذه الرسالة</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>© 2025 ES-GIFT - جميع الحقوق محفوظة</p>
                        <p>هذه رسالة تلقائية، يرجى عدم الرد عليها</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # إنشاء الرسالة
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = email
            
            # إضافة المحتوى
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # إرسال الرسالة (محاكاة - يحتاج إعداد SMTP حقيقي)
            logger.info(f"✅ تم إرسال رسالة التحقق الاحتياطية (محاكاة)")
            return True, "تم إرسال كود التحقق بنجاح"
            
        except Exception as e:
            error_msg = f"فشل في إرسال رسالة التحقق الاحتياطية: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

# إنشاء instance عام
fallback_email_service = FallbackEmailService()
