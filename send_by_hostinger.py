#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إرسال الرسائل عبر Hostinger SMTP
=====================================

نظام بديل لإرسال الرسائل الإلكترونية باستخدام خادم Hostinger SMTP
"""

import smtplib
import ssl
import logging
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Tuple, Optional
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HostingerEmailService:
    """خدمة إرسال الرسائل عبر Hostinger SMTP"""
    
    def __init__(self):
        """تهيئة الخدمة"""
        self.smtp_server = "smtp.hostinger.com"
        self.smtp_port = 465
        self.sender_email = "business@es-gift.com"
        self.sender_password = "Abdo@2002@"
        self.sender_name = "ES-Gift"
        
    def _create_smtp_connection(self) -> Tuple[bool, object]:
        """إنشاء اتصال SMTP آمن"""
        try:
            # إنشاء SSL context آمن
            context = ssl.create_default_context()
            
            # إنشاء اتصال SMTP مع SSL
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            
            # تسجيل الدخول
            server.login(self.sender_email, self.sender_password)
            
            logger.info(f"✅ تم الاتصال بخادم Hostinger SMTP بنجاح")
            return True, server
            
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال بخادم SMTP: {str(e)}")
            return False, None
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> Tuple[bool, str]:
        """إرسال رسالة إلكترونية"""
        try:
            logger.info(f"📧 إرسال رسالة إلى: {to_email}")
            logger.info(f"📋 الموضوع: {subject}")
            
            # إنشاء اتصال SMTP
            success, server = self._create_smtp_connection()
            if not success:
                return False, "فشل في الاتصال بخادم البريد الإلكتروني"
            
            try:
                # إنشاء الرسالة مع تشفير UTF-8
                message = MIMEMultipart("alternative", charset='utf-8')
                message["Subject"] = Header(subject, 'utf-8')
                message["From"] = Header(f"{self.sender_name} <{self.sender_email}>", 'utf-8')
                message["To"] = to_email
                message["Content-Type"] = "text/html; charset=UTF-8"
                
                # إضافة النص العادي إذا وُجد
                if text_content:
                    text_part = MIMEText(text_content, "plain", "utf-8")
                    message.attach(text_part)
                
                # إضافة HTML
                html_part = MIMEText(html_content, "html", "utf-8")
                message.attach(html_part)
                
                # إرسال الرسالة مع تشفير UTF-8
                try:
                    text = message.as_string()
                    # التأكد من أن النص في تنسيق bytes صحيح
                    if isinstance(text, str):
                        text_bytes = text.encode('utf-8')
                    else:
                        text_bytes = text
                    server.sendmail(self.sender_email, to_email, text_bytes)
                except UnicodeEncodeError as ue:
                    # معالجة خاصة لأخطاء التشفير
                    logger.warning(f"⚠️ خطأ تشفير، محاولة إرسال كنص عادي: {ue}")
                    # محاولة إرسال بدون تشفير إضافي
                    server.sendmail(self.sender_email, to_email, message.as_string())
                
                logger.info(f"✅ تم إرسال الرسالة بنجاح إلى: {to_email}")
                return True, "تم إرسال الرسالة بنجاح"
                
            finally:
                # إغلاق الاتصال
                server.quit()
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الرسالة: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def generate_verification_code(self, length: int = 6) -> str:
        """توليد كود التحقق"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_email(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """
        إرسال كود التحقق
        
        Args:
            email (str): البريد الإلكتروني للمستقبل
            
        Returns:
            Tuple[bool, str, Optional[str]]: (نجح, رسالة, كود التحقق)
        """
        try:
            logger.info(f"🔐 إرسال كود التحقق إلى: {email}")
            
            # توليد كود التحقق
            verification_code = self.generate_verification_code()
            
            # إنشاء محتوى HTML للرسالة
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>كود التحقق - ES-Gift</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background-color: #f4f4f4;
                        direction: rtl;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #ff0033, #cc0029);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 28px;
                    }}
                    .content {{
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .verification-code {{
                        background: #f8f9fa;
                        border: 2px dashed #ff0033;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 20px 0;
                        font-size: 32px;
                        font-weight: bold;
                        color: #ff0033;
                        letter-spacing: 5px;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                    }}
                    .note {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #856404;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🎁 ES-Gift</h1>
                        <p>نظام إدارة الهدايا الرقمية</p>
                    </div>
                    
                    <div class="content">
                        <h2>كود التحقق من البريد الإلكتروني</h2>
                        <p>مرحباً بك في ES-Gift!</p>
                        <p>استخدم الكود التالي للتحقق من بريدك الإلكتروني:</p>
                        
                        <div class="verification-code">
                            {verification_code}
                        </div>
                        
                        <div class="note">
                            <strong>⚠️ مهم:</strong>
                            <ul style="text-align: right; margin: 10px 0;">
                                <li>هذا الكود صالح لمدة 15 دقيقة فقط</li>
                                <li>لا تشارك هذا الكود مع أي شخص آخر</li>
                                <li>إذا لم تطلب هذا الكود، يرجى تجاهل هذه الرسالة</li>
                            </ul>
                        </div>
                        
                        <p>إذا واجهت أي مشاكل، لا تتردد في التواصل معنا!</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 ES-Gift - جميع الحقوق محفوظة</p>
                        <p>هذه رسالة تلقائية، يرجى عدم الرد عليها</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # النص العادي كبديل
            text_content = f"""
كود التحقق - ES-Gift

مرحباً بك في ES-Gift!

كود التحقق الخاص بك هو: {verification_code}

هذا الكود صالح لمدة 15 دقيقة فقط.
لا تشارك هذا الكود مع أي شخص آخر.

© 2025 ES-Gift - جميع الحقوق محفوظة
            """
            
            # إرسال الرسالة
            success, message = self._send_email(
                to_email=email,
                subject="كود التحقق - ES-Gift",
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"✅ تم إرسال كود التحقق بنجاح: {verification_code}")
                return True, "تم إرسال كود التحقق بنجاح", verification_code
            else:
                return False, message, None
                
        except Exception as e:
            error_msg = f"خطأ في إرسال كود التحقق: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg, None
    
    def send_order_confirmation(self, email: str, order_number: str, customer_name: str, 
                               total_amount: str, order_date: str = None, 
                               order_status: str = "تم التأكيد") -> Tuple[bool, str]:
        """
        إرسال تأكيد الطلب
        
        Args:
            email (str): البريد الإلكتروني للعميل
            order_number (str): رقم الطلب
            customer_name (str): اسم العميل
            total_amount (str): المبلغ الإجمالي
            order_date (str): تاريخ الطلب
            order_status (str): حالة الطلب
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"📦 إرسال تأكيد الطلب {order_number} إلى: {email}")
            
            if not order_date:
                order_date = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # إنشاء محتوى HTML للرسالة
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>تأكيد الطلب - ES-Gift</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background-color: #f4f4f4;
                        direction: rtl;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #ff0033, #cc0029);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .order-info {{
                        background: #f8f9fa;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    .order-row {{
                        display: flex;
                        justify-content: space-between;
                        padding: 10px 0;
                        border-bottom: 1px solid #dee2e6;
                    }}
                    .order-row:last-child {{
                        border-bottom: none;
                    }}
                    .total-amount {{
                        background: #ff0033;
                        color: white;
                        padding: 15px;
                        border-radius: 5px;
                        text-align: center;
                        font-size: 18px;
                        font-weight: bold;
                        margin: 20px 0;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🎁 ES-Gift</h1>
                        <h2>تأكيد الطلب</h2>
                    </div>
                    
                    <div class="content">
                        <h3>مرحباً {customer_name}،</h3>
                        <p>شكراً لك لاختيار ES-Gift! تم استلام طلبك بنجاح.</p>
                        
                        <div class="order-info">
                            <div class="order-row">
                                <strong>رقم الطلب:</strong>
                                <span>{order_number}</span>
                            </div>
                            <div class="order-row">
                                <strong>تاريخ الطلب:</strong>
                                <span>{order_date}</span>
                            </div>
                            <div class="order-row">
                                <strong>حالة الطلب:</strong>
                                <span style="color: #28a745; font-weight: bold;">{order_status}</span>
                            </div>
                        </div>
                        
                        <div class="total-amount">
                            المبلغ الإجمالي: {total_amount}
                        </div>
                        
                        <p>سيتم إرسال تفاصيل المنتجات والأكواد في رسالة منفصلة بمجرد معالجة طلبك.</p>
                        
                        <p>إذا كان لديك أي استفسارات، لا تتردد في التواصل معنا!</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 ES-Gift - جميع الحقوق محفوظة</p>
                        <p>للدعم الفني: support@es-gift.com</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # إرسال الرسالة
            success, message = self._send_email(
                to_email=email,
                subject=f"تأكيد الطلب #{order_number} - ES-Gift",
                html_content=html_content
            )
            
            if success:
                logger.info(f"✅ تم إرسال تأكيد الطلب بنجاح")
                return True, "تم إرسال تأكيد الطلب بنجاح"
            else:
                return False, message
                
        except Exception as e:
            error_msg = f"خطأ في إرسال تأكيد الطلب: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def send_welcome_email(self, email: str, customer_name: str) -> Tuple[bool, str]:
        """
        إرسال رسالة ترحيبية
        
        Args:
            email (str): البريد الإلكتروني للعميل
            customer_name (str): اسم العميل
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"👋 إرسال رسالة ترحيبية إلى: {email}")
            
            # إنشاء محتوى HTML للرسالة
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>مرحباً بك في ES-Gift</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background-color: #f4f4f4;
                        direction: rtl;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #ff0033, #cc0029);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .features {{
                        background: #f8f9fa;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    .feature-item {{
                        padding: 10px 0;
                        border-bottom: 1px solid #dee2e6;
                    }}
                    .feature-item:last-child {{
                        border-bottom: none;
                    }}
                    .cta-button {{
                        display: inline-block;
                        background: #ff0033;
                        color: white;
                        padding: 15px 30px;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;
                        margin: 20px 0;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🎁 مرحباً بك في ES-Gift</h1>
                        <p>منصة الهدايا الرقمية الأولى</p>
                    </div>
                    
                    <div class="content">
                        <h2>أهلاً وسهلاً {customer_name}!</h2>
                        <p>نحن سعداء لانضمامك إلى عائلة ES-Gift. الآن يمكنك الاستمتاع بأفضل خدمات الهدايا الرقمية.</p>
                        
                        <div class="features">
                            <h3>ما يمكنك فعله الآن:</h3>
                            <div class="feature-item">
                                🎮 شراء بطاقات الألعاب المختلفة
                            </div>
                            <div class="feature-item">
                                💳 بطاقات الهدايا لجميع المتاجر الشهيرة
                            </div>
                            <div class="feature-item">
                                💰 أسعار تنافسية وعروض حصرية
                            </div>
                            <div class="feature-item">
                                🚀 تسليم فوري للأكواد والبطاقات
                            </div>
                            <div class="feature-item">
                                🛡️ حماية كاملة وضمان للمنتجات
                            </div>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="https://es-gift.com" class="cta-button">ابدأ التسوق الآن</a>
                        </div>
                        
                        <p>إذا كان لديك أي أسئلة، فريق الدعم متاح 24/7 لمساعدتك!</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 ES-Gift - جميع الحقوق محفوظة</p>
                        <p>للدعم الفني: support@es-gift.com</p>
                        <p>واتساب: +201145425207</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # إرسال الرسالة
            success, message = self._send_email(
                to_email=email,
                subject="مرحباً بك في ES-Gift - منصة الهدايا الرقمية",
                html_content=html_content
            )
            
            if success:
                logger.info(f"✅ تم إرسال الرسالة الترحيبية بنجاح")
                return True, "تم إرسال الرسالة الترحيبية بنجاح"
            else:
                return False, message
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الرسالة الترحيبية: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def send_custom_email(self, email: str, subject: str, message_content: str, 
                         message_title: str = None) -> Tuple[bool, str]:
        """
        إرسال رسالة مخصصة
        
        Args:
            email (str): البريد الإلكتروني للمستقبل
            subject (str): موضوع الرسالة
            message_content (str): محتوى الرسالة
            message_title (str): عنوان الرسالة (اختياري)
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"📝 إرسال رسالة مخصصة إلى: {email}")
            
            # إنشاء محتوى HTML للرسالة
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{subject}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background-color: #f4f4f4;
                        direction: rtl;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #ff0033, #cc0029);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .message-content {{
                        background: #f8f9fa;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 20px 0;
                        border-right: 4px solid #ff0033;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🎁 ES-Gift</h1>
                        {f'<h2>{message_title}</h2>' if message_title else ''}
                    </div>
                    
                    <div class="content">
                        <div class="message-content">
                            {message_content}
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 ES-Gift - جميع الحقوق محفوظة</p>
                        <p>للدعم الفني: support@es-gift.com</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # إرسال الرسالة
            success, message = self._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content
            )
            
            if success:
                logger.info(f"✅ تم إرسال الرسالة المخصصة بنجاح")
                return True, "تم إرسال الرسالة المخصصة بنجاح"
            else:
                return False, message
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الرسالة المخصصة: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def test_connection(self) -> Tuple[bool, str]:
        """اختبار الاتصال بخادم SMTP"""
        try:
            logger.info("🔍 اختبار الاتصال بخادم Hostinger SMTP...")
            
            success, server = self._create_smtp_connection()
            if success:
                server.quit()
                logger.info("✅ تم اختبار الاتصال بنجاح")
                return True, "تم الاتصال بخادم البريد الإلكتروني بنجاح"
            else:
                return False, "فشل في الاتصال بخادم البريد الإلكتروني"
                
        except Exception as e:
            error_msg = f"خطأ في اختبار الاتصال: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

# إنشاء مثيل الخدمة العامة
hostinger_email_service = HostingerEmailService()

# ========== دوال مساعدة للاستخدام السريع ==========

def send_verification_email(email: str) -> Tuple[bool, str, Optional[str]]:
    """إرسال كود التحقق"""
    return hostinger_email_service.send_verification_email(email)

def send_order_confirmation(email: str, order_number: str, customer_name: str, 
                           total_amount: str, order_date: str = None) -> Tuple[bool, str]:
    """إرسال تأكيد الطلب"""
    return hostinger_email_service.send_order_confirmation(
        email, order_number, customer_name, total_amount, order_date
    )

def send_welcome_email(email: str, customer_name: str) -> Tuple[bool, str]:
    """إرسال رسالة ترحيبية"""
    return hostinger_email_service.send_welcome_email(email, customer_name)

def send_custom_email(email: str, subject: str, message_content: str, 
                     message_title: str = None) -> Tuple[bool, str]:
    """إرسال رسالة مخصصة"""
    return hostinger_email_service.send_custom_email(
        email, subject, message_content, message_title
    )

def send_email(to_email: str, subject: str, body: str) -> bool:
    """دالة عامة لإرسال البريد الإلكتروني للتوافق مع النظام الحالي"""
    try:
        success, _ = hostinger_email_service.send_custom_email(
            email=to_email,
            subject=subject,
            message_content=body
        )
        return success
    except Exception as e:
        logger.error(f"❌ خطأ في send_email: {str(e)}")
        return False

def test_email_connection() -> Tuple[bool, str]:
    """اختبار الاتصال بخادم البريد الإلكتروني"""
    return hostinger_email_service.test_connection()

# تصدير الدوال والكلاسات المطلوبة
__all__ = [
    'HostingerEmailService',
    'hostinger_email_service',
    'send_verification_email',
    'send_order_confirmation', 
    'send_welcome_email',
    'send_custom_email',
    'send_email',
    'test_email_connection'
]
