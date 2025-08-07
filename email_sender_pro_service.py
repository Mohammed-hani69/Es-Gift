#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة Email Sender Pro API لإرسال الرسائل الإلكترونية
==================================================

تكامل مع Email Sender Pro API لإرسال رسائل التحقق، الطلبات، والترحيب
API Documentation: https://verifix-otp.com
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
from flask import current_app

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSenderProService:
    """خدمة Email Sender Pro API مع دعم الإعدادات البديلة"""
    
    def __init__(self):
        """تهيئة الخدمة مع إعدادات بديلة"""
        # API الأساسي
        self.base_url = "https://verifix-otp.com"
        self.api_key = "c7eb68558d0b400f94f077bb414a1d2b"
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": "ES-Gift/1.0"
        }
        self.timeout = 30  # مهلة زمنية أطول
        self.retry_count = 2  # عدد مرات المحاولة
        
        # إعدادات الإرسال البديل (SMTP)
        self.fallback_smtp = None
        self._init_fallback_smtp()
    
    def _init_fallback_smtp(self):
        """تهيئة خدمة SMTP البديلة مع الإعدادات المطلوبة"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.header import Header
            
            # إعدادات SMTP البديلة (Gmail)
            self.fallback_config = {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender_email': 'esgiftscard@gmail.com',
                'sender_password': 'xopq ikac efpj rdif',
                'sender_name': 'ES-GIFT'
            }
            
            logger.info("🔄 تم تهيئة خدمة SMTP البديلة (Gmail)")
            
        except Exception as e:
            logger.warning(f"⚠️ لم يتم تهيئة خدمة SMTP البديلة: {e}")
            self.fallback_config = None
        
    def _make_request(self, endpoint: str, data: Dict, method: str = "POST") -> Tuple[bool, Dict]:
        """إجراء طلب HTTP إلى API"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            logger.info(f"📤 طلب API: {method} {url}")
            logger.info(f"🔑 API Key: {self.api_key[:10]}...")
            logger.debug(f"البيانات: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # جميع طلبات API تستخدم POST method فقط
            response = requests.post(
                url, 
                headers=self.headers, 
                json=data,
                timeout=self.timeout,
                verify=True  # تأكيد SSL
            )
            
            logger.info(f"📥 استجابة API: {response.status_code}")
            logger.debug(f"📄 Response Headers: {dict(response.headers)}")
            
            # طباعة جزء من النص للتشخيص
            response_preview = response.text[:200] if response.text else "فارغ"
            logger.debug(f"📝 Response Preview: {response_preview}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.debug(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return True, result
                except json.JSONDecodeError:
                    logger.error("❌ الاستجابة ليست JSON صالحة")
                    return False, {"error": f"استجابة غير صالحة: {response.text[:100]}"}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(f"❌ خطأ API: {error_msg}")
                return False, {"error": error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = "انتهت مهلة الاتصال - لم يستجب الخادم خلال 30 ثانية"
            logger.error(f"❌ {error_msg}")
            return False, {"error": error_msg}
            
        except requests.exceptions.ConnectionError:
            error_msg = "خطأ في الاتصال - تعذر الاتصال بخادم API"
            logger.error(f"❌ {error_msg}")
            return False, {"error": error_msg}
            
        except Exception as e:
            error_msg = f"خطأ غير متوقع: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, {"error": error_msg}
    
    def _send_with_fallback(self, email: str, subject: str, html_content: str) -> Tuple[bool, str]:
        """إرسال باستخدام خدمة SMTP البديلة (Gmail)"""
        try:
            if not self.fallback_config:
                return False, "خدمة SMTP البديلة غير متاحة"
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.header import Header
            
            logger.info(f"🔄 استخدام الإعدادات البديلة (Gmail) لإرسال إلى: {email}")
            
            # إنشاء الرسالة
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = f"{self.fallback_config['sender_name']} <{self.fallback_config['sender_email']}>"
            msg['To'] = email
            
            # إضافة المحتوى HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # الاتصال وإرسال الرسالة
            with smtplib.SMTP(self.fallback_config['smtp_server'], self.fallback_config['smtp_port']) as server:
                server.starttls()
                server.login(self.fallback_config['sender_email'], self.fallback_config['sender_password'])
                server.send_message(msg)
            
            logger.info(f"✅ تم الإرسال بنجاح عبر Gmail البديل")
            return True, "تم الإرسال عبر Gmail البديل بنجاح"
            
        except Exception as e:
            error_msg = f"خطأ في الإرسال البديل (Gmail): {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def send_verification_code(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """
        إرسال كود التحقق مع دعم الإعدادات البديلة
        
        Args:
            email (str): البريد الإلكتروني للمستقبل
            
        Returns:
            Tuple[bool, str, Optional[str]]: (نجح, رسالة, كود التحقق)
        """
        try:
            logger.info(f"🔐 إرسال كود التحقق إلى: {email}")
            
            data = {"email": email}
            
            # محاولة إرسال عبر API أولاً
            success, result = self._make_request("/api/send-verification", data, "POST")
            
            if success and result.get('success'):
                verification_code = result.get('verification_code')
                remaining_balance = result.get('remaining_balance', 'غير متوفر')
                free_messages = result.get('free_messages_remaining', 'غير متوفر')
                
                logger.info(f"✅ تم إرسال كود التحقق بنجاح عبر API")
                logger.info(f"💰 الرصيد المتبقي: {remaining_balance}")
                logger.info(f"📨 الرسائل المجانية المتبقية: {free_messages}")
                
                return True, "تم إرسال كود التحقق بنجاح عبر API", verification_code
            else:
                # إذا فشل API، استخدم الإعدادات البديلة
                logger.warning(f"❌ فشل API، محاولة الإرسال البديل...")
                
                # توليد كود تحقق محلياً
                import random
                import string
                verification_code = ''.join(random.choices(string.digits, k=6))
                
                # إنشاء محتوى HTML للكود
                subject = f"🔐 كود التحقق - ES-GIFT"
                html_content = f"""
                <!DOCTYPE html>
                <html dir="rtl" lang="ar">
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: 'Cairo', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                        .header {{ background: #DC143C; color: white; padding: 30px; text-align: center; }}
                        .content {{ padding: 30px; }}
                        .code-box {{ background: #f8f9fa; border: 2px dashed #DC143C; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0; }}
                        .code {{ font-size: 32px; font-weight: bold; color: #DC143C; letter-spacing: 5px; }}
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
                
                # محاولة الإرسال البديل
                fallback_success, fallback_message = self._send_with_fallback(email, subject, html_content)
                
                if fallback_success:
                    return True, f"تم إرسال كود التحقق عبر النظام البديل", verification_code
                else:
                    error_msg = f"فشل في كلا النظامين - API: {result.get('error', 'خطأ غير محدد')}, البديل: {fallback_message}"
                    logger.error(f"❌ {error_msg}")
                    return False, error_msg, None
                
        except Exception as e:
            error_msg = f"خطأ في إرسال كود التحقق: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg, None
    
    def send_order_details(self, email: str, order_number: str, customer_name: str, 
                          total_amount: str, order_date: str = None, 
                          order_status: str = "تم التأكيد") -> Tuple[bool, str]:
        """
        إرسال تفاصيل الطلب
        
        Args:
            email (str): البريد الإلكتروني للعميل
            order_number (str): رقم الطلب
            customer_name (str): اسم العميل
            total_amount (str): المبلغ الإجمالي
            order_date (str): تاريخ الطلب (افتراضي: اليوم)
            order_status (str): حالة الطلب (افتراضي: تم التأكيد)
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"📦 إرسال تفاصيل الطلب {order_number} إلى: {email}")
            
            data = {
                "email": email,
                "order_number": order_number,
                "customer_name": customer_name,
                "total_amount": total_amount,
                "order_date": order_date or datetime.now().strftime('%Y-%m-%d'),
                "order_status": order_status
            }
            
            success, result = self._make_request("/api/send-order", data)
            
            if success and result.get('success'):
                logger.info(f"✅ تم إرسال تفاصيل الطلب بنجاح")
                return True, "تم إرسال تفاصيل الطلب بنجاح"
            else:
                error_msg = result.get('error', 'فشل في إرسال تفاصيل الطلب')
                logger.error(f"❌ فشل إرسال تفاصيل الطلب: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"خطأ في إرسال تفاصيل الطلب: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def send_welcome_message(self, email: str, customer_name: str) -> Tuple[bool, str]:
        """
        إرسال رسالة ترحيبية
        
        Args:
            email (str): البريد الإلكتروني للعميل الجديد
            customer_name (str): اسم العميل
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"🎉 إرسال رسالة ترحيبية إلى: {email}")
            
            data = {
                "email": email,
                "customer_name": customer_name
            }
            
            success, result = self._make_request("/api/send-welcome", data)
            
            if success and result.get('success'):
                logger.info(f"✅ تم إرسال الرسالة الترحيبية بنجاح")
                return True, "تم إرسال الرسالة الترحيبية بنجاح"
            else:
                error_msg = result.get('error', 'فشل في إرسال الرسالة الترحيبية')
                logger.error(f"❌ فشل إرسال الرسالة الترحيبية: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الرسالة الترحيبية: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def send_custom_email(self, email: str, subject: str, message_content: str, 
                         message_title: str = None) -> Tuple[bool, str]:
        """
        إرسال رسالة مخصصة (alias لـ send_custom_message)
        
        Args:
            email (str): البريد الإلكتروني للمستقبل
            subject (str): موضوع الرسالة
            message_content (str): محتوى الرسالة
            message_title (str): عنوان الرسالة (افتراضي: نفس الموضوع)
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        return self.send_custom_message(email, subject, message_content, message_title)
    
    def send_custom_email(self, email: str, subject: str, message_content: str, 
                         message_title: str = None) -> Tuple[bool, str]:
        """إرسال رسالة مخصصة"""
        return self.send_custom_message(email, subject, message_content, message_title)
    
    def send_custom_message(self, email: str, subject: str, message_content: str, 
                           message_title: str = None) -> Tuple[bool, str]:
        """
        إرسال رسالة مخصصة عبر API أو الإعدادات البديلة
        
        Args:
            email (str): البريد الإلكتروني
            subject (str): الموضوع
            message_content (str): المحتوى
            message_title (str): العنوان الاختياري
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"📧 إرسال رسالة مخصصة إلى: {email}")
            
            # محاولة إرسال عبر API أولاً
            data = {
                "email": email,
                "subject": subject,
                "message": message_content,
                "title": message_title or "ES-GIFT"
            }
            
            success, response = self._make_request("/api/send-custom", data)
            
            if success:
                logger.info(f"✅ تم إرسال الرسالة المخصصة بنجاح عبر API")
                return True, "تم إرسال الرسالة بنجاح"
            else:
                logger.warning(f"⚠️ فشل إرسال API، محاولة الإعدادات البديلة...")
                
                # إنشاء محتوى HTML جميل
                html_content = f"""
                <!DOCTYPE html>
                <html dir="rtl" lang="ar">
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: 'Cairo', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                        .header {{ background: linear-gradient(135deg, #E31837, #ff3366); color: white; padding: 30px; text-align: center; }}
                        .content {{ padding: 30px; line-height: 1.6; }}
                        .footer {{ background: #333; color: #ccc; padding: 20px; text-align: center; font-size: 14px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎁 ES-GIFT</h1>
                            <p>{message_title or "رسالة مخصصة"}</p>
                        </div>
                        <div class="content">
                            {message_content.replace(chr(10), '<br>')}
                        </div>
                        <div class="footer">
                            <p>© 2025 ES-GIFT - جميع الحقوق محفوظة</p>
                            <p>📧 business@es-gift.com | 📱 +966123456789</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # محاولة الإرسال البديل
                fallback_success, fallback_message = self._send_with_fallback(email, subject, html_content)
                
                if fallback_success:
                    logger.info(f"✅ تم إرسال الرسالة عبر النظام البديل")
                    return True, "تم إرسال الرسالة عبر النظام البديل"
                else:
                    logger.error(f"❌ فشل في جميع طرق الإرسال")
                    return False, f"فشل الإرسال: API فشل، البديل فشل - {fallback_message}"
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الرسالة المخصصة: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        """
        إرسال رسالة مخصصة
        
        Args:
            email (str): البريد الإلكتروني للمستقبل
            subject (str): موضوع الرسالة
            message_content (str): محتوى الرسالة
            message_title (str): عنوان الرسالة (افتراضي: نفس الموضوع)
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"💌 إرسال رسالة مخصصة إلى: {email}")
            
            data = {
                "email": email,
                "subject": subject,
                "message_content": message_content,
                "message_title": message_title or subject
            }
            
            success, result = self._make_request("/api/send-custom", data)
            
            if success and result.get('success'):
                logger.info(f"✅ تم إرسال الرسالة المخصصة بنجاح")
                return True, "تم إرسال الرسالة المخصصة بنجاح"
            else:
                error_msg = result.get('error', 'فشل في إرسال الرسالة المخصصة')
                logger.error(f"❌ فشل إرسال الرسالة المخصصة: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الرسالة المخصصة: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def send_invoice_email(self, email: str, invoice_number: str, customer_name: str, 
                          total_amount: str, pdf_path: str = None) -> Tuple[bool, str]:
        """
        إرسال فاتورة عبر البريد الإلكتروني مع دعم الإعدادات البديلة
        
        Args:
            email (str): البريد الإلكتروني للعميل
            invoice_number (str): رقم الفاتورة
            customer_name (str): اسم العميل
            total_amount (str): المبلغ الإجمالي
            pdf_path (str): مسار ملف PDF (اختياري)
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"📄 إرسال فاتورة {invoice_number} إلى: {email}")
            
            # محاولة إرسال عبر API أولاً
            message_content = f"""
            عزيزي {customer_name},
            
            شكراً لاختياركم ES-GIFT. تجدون في هذه الرسالة تفاصيل فاتورتكم:
            
            📋 تفاصيل الفاتورة:
            • رقم الفاتورة: {invoice_number}
            • المبلغ الإجمالي: {total_amount}
            • تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d')}
            
            يمكنكم تحميل ملف PDF للفاتورة من لوحة التحكم الخاصة بكم.
            
            إذا كان لديكم أي استفسارات، لا تترددوا في التواصل معنا:
            📧 business@es-gift.com
            📱 +966123456789
            🌐 www.es-gift.com
            
            شكراً لثقتكم في ES-GIFT
            فريق خدمة العملاء
            """
            
            # إرسال الرسالة باستخدام دالة الرسائل المخصصة
            success, message = self.send_custom_message(
                email=email,
                subject=f"🎁 فاتورة ES-GIFT - {invoice_number}",
                message_content=message_content,
                message_title="فاتورة ES-GIFT"
            )
            
            if success:
                logger.info(f"✅ تم إرسال الفاتورة بنجاح عبر API")
                return True, "تم إرسال الفاتورة بنجاح عبر API"
            else:
                # إذا فشل API، استخدم الإعدادات البديلة
                logger.warning(f"❌ فشل API، محاولة الإرسال البديل للفاتورة...")
                
                # إنشاء محتوى HTML احترافي للفاتورة
                subject = f"🎁 فاتورة ES-GIFT - {invoice_number}"
                html_content = f"""
                <!DOCTYPE html>
                <html dir="rtl" lang="ar">
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: 'Cairo', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                        .header {{ background: #DC143C; color: white; padding: 30px; text-align: center; }}
                        .content {{ padding: 30px; }}
                        .invoice-box {{ background: #f8f9fa; border-right: 4px solid #DC143C; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                        .footer {{ background: #333; color: #ccc; padding: 20px; text-align: center; font-size: 14px; }}
                        .highlight {{ color: #DC143C; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎁 ES-GIFT</h1>
                            <p>فاتورة الخدمات الرقمية</p>
                        </div>
                        <div class="content">
                            <h2>عزيزي/عزيزتي {customer_name}</h2>
                            <p>شكراً لاختياركم ES-GIFT. نرسل إليكم تفاصيل فاتورتكم الإلكترونية:</p>
                            
                            <div class="invoice-box">
                                <h3 class="highlight">📋 تفاصيل الفاتورة</h3>
                                <p><strong>رقم الفاتورة:</strong> {invoice_number}</p>
                                <p><strong>المبلغ الإجمالي:</strong> <span class="highlight">{total_amount}</span></p>
                                <p><strong>تاريخ الإصدار:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                                <p><strong>حالة الدفع:</strong> <span style="color: green;">✅ مدفوعة</span></p>
                            </div>
                            
                            <p>يمكنكم تحميل نسخة PDF من الفاتورة من خلال لوحة التحكم الخاصة بكم.</p>
                            
                            <p style="color: #666; margin-top: 30px;">
                                <strong>للاستفسارات:</strong><br>
                                📧 business@es-gift.com<br>
                                📱 +966123456789<br>
                                🌐 www.es-gift.com
                            </p>
                        </div>
                        <div class="footer">
                            <p>© 2025 ES-GIFT - جميع الحقوق محفوظة</p>
                            <p>شكراً لثقتكم في خدماتنا الرقمية</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # محاولة الإرسال البديل
                fallback_success, fallback_message = self._send_with_fallback(email, subject, html_content)
                
                if fallback_success:
                    logger.info(f"✅ تم إرسال الفاتورة عبر النظام البديل")
                    return True, "تم إرسال الفاتورة عبر النظام البديل"
                else:
                    error_msg = f"فشل في إرسال الفاتورة عبر كلا النظامين - API: {message}, البديل: {fallback_message}"
                    logger.error(f"❌ {error_msg}")
                    return False, error_msg
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الفاتورة: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def get_api_balance(self) -> Tuple[bool, Dict]:
        """
        الحصول على رصيد API
        
        Returns:
            Tuple[bool, Dict]: (نجح, بيانات الرصيد)
        """
        try:
            logger.info("💰 جاري الاستعلام عن رصيد API...")
            
            success, result = self._make_request("/api/balance", {})
            
            if success and result.get('success'):
                balance_info = {
                    'remaining_balance': result.get('remaining_balance', 0),
                    'free_messages_remaining': result.get('free_messages_remaining', 0),
                    'total_sent': result.get('total_sent', 0)
                }
                logger.info(f"✅ تم الحصول على معلومات الرصيد: {balance_info}")
                return True, balance_info
            else:
                error_msg = result.get('error', 'فشل في الحصول على معلومات الرصيد')
                logger.error(f"❌ {error_msg}")
                return False, {"error": error_msg}
                
        except Exception as e:
            error_msg = f"خطأ في الاستعلام عن الرصيد: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, {"error": error_msg}
    
    def get_balance(self) -> Tuple[bool, Dict]:
        """
        الحصول على الرصيد المتبقي
        
        Returns:
            Tuple[bool, Dict]: (نجح, بيانات الرصيد)
        """
        try:
            logger.info("💰 فحص الرصيد المتبقي...")
            
            data = {}
            success, result = self._make_request("/api/balance", data)
            
            if success and result.get('success'):
                logger.info(f"✅ تم جلب بيانات الرصيد بنجاح")
                return True, result
            else:
                error_msg = result.get('error', 'فشل في جلب الرصيد')
                logger.error(f"❌ فشل جلب الرصيد: {error_msg}")
                return False, {"error": error_msg}
                
        except Exception as e:
            error_msg = f"خطأ في جلب الرصيد: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, {"error": error_msg}
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        اختبار الاتصال مع API
        
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info("🔌 اختبار الاتصال مع Email Sender Pro API...")
            
            # اختبار أساسي للموقع
            try:
                import urllib.request
                urllib.request.urlopen("https://verifix-otp.com", timeout=5)
                logger.info("✅ الموقع الأساسي متاح")
            except:
                logger.warning("⚠️ صعوبة في الوصول للموقع الأساسي")
            
            # اختبار بإرسال كود تحقق لإيميل تجريبي
            test_email = "test@example.com"
            success, message, code = self.send_verification_code(test_email)
            
            if success:
                return True, f"✅ الاتصال ناجح - تم إرسال كود التحقق: {code}"
            else:
                return False, f"❌ فشل الاتصال: {message}"
                
        except Exception as e:
            error_msg = f"خطأ في اختبار الاتصال: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg


# إنشاء مثيل الخدمة العامة
email_sender_service = EmailSenderProService()

# ========== دوال مساعدة للاستخدام السريع ==========

def send_verification_email(email: str) -> Tuple[bool, str, Optional[str]]:
    """
    دالة مساعدة لإرسال كود التحقق
    
    Args:
        email (str): البريد الإلكتروني
        
    Returns:
        Tuple[bool, str, Optional[str]]: (نجح, رسالة, كود التحقق)
    """
    return email_sender_service.send_verification_code(email)

def send_order_confirmation(email: str, order_number: str, customer_name: str, 
                           total_amount: str, order_date: str = None) -> Tuple[bool, str]:
    """
    دالة مساعدة لإرسال تأكيد الطلب
    
    Args:
        email (str): البريد الإلكتروني
        order_number (str): رقم الطلب
        customer_name (str): اسم العميل
        total_amount (str): المبلغ الإجمالي
        order_date (str): تاريخ الطلب
        
    Returns:
        Tuple[bool, str]: (نجح, رسالة)
    """
    return email_sender_service.send_order_details(
        email, order_number, customer_name, total_amount, order_date
    )

def send_welcome_email(email: str, customer_name: str) -> Tuple[bool, str]:
    """
    دالة مساعدة لإرسال رسالة ترحيبية
    
    Args:
        email (str): البريد الإلكتروني
        customer_name (str): اسم العميل
        
    Returns:
        Tuple[bool, str]: (نجح, رسالة)
    """
    return email_sender_service.send_welcome_message(email, customer_name)

def send_custom_email(email: str, subject: str, message_content: str, 
                     message_title: str = None) -> Tuple[bool, str]:
    """
    دالة مساعدة لإرسال رسالة مخصصة
    
    Args:
        email (str): البريد الإلكتروني
        subject (str): الموضوع
        message_content (str): المحتوى
        message_title (str): العنوان
        
    Returns:
        Tuple[bool, str]: (نجح, رسالة)
    """
    return email_sender_service.send_custom_message(
        email, subject, message_content, message_title
    )

def get_email_balance() -> Tuple[bool, Dict]:
    """
    دالة مساعدة للحصول على الرصيد
    
    Returns:
        Tuple[bool, Dict]: (نجح, بيانات الرصيد)
    """
    return email_sender_service.get_balance()

def test_email_api() -> Tuple[bool, str]:
    """
    دالة مساعدة لاختبار API
    
    Returns:
        Tuple[bool, str]: (نجح, رسالة)
    """
    return email_sender_service.test_connection()

# ========== دوال للتوافق مع النظام الحالي ==========

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    دالة عامة لإرسال البريد - للتوافق مع النظام الحالي
    
    Args:
        to_email (str): البريد الإلكتروني للمستقبل
        subject (str): موضوع الرسالة
        body (str): محتوى الرسالة
        
    Returns:
        bool: نجح الإرسال أم لا
    """
    try:
        success, message = send_custom_email(to_email, subject, body)
        if success:
            logger.info(f"✅ تم إرسال البريد بنجاح إلى: {to_email}")
            return True
        else:
            logger.error(f"❌ فشل إرسال البريد إلى {to_email}: {message}")
            return False
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال البريد: {str(e)}")
        return False

    def send_custom_email(self, email, subject, html_content, pdf_attachment_path=None):
        """إرسال إيميل مخصص مع إمكانية إرفاق ملف PDF"""
        try:
            logger.info(f"📤 إرسال إيميل مخصص إلى: {email}")
            
            # Try API first
            api_success = self.send_invoice_email(
                email=email,
                subject=subject,
                html_content=html_content,
                pdf_attachment_path=pdf_attachment_path
            )
            
            if api_success:
                return True
            
            # Fallback to SMTP if API fails
            logger.warning("🔄 API فشل، محاولة SMTP البديل...")
            return self._send_smtp_fallback(email, subject, html_content, pdf_attachment_path)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الإيميل المخصص: {e}")
            return False

    def _send_smtp_fallback(self, email, subject, html_content, pdf_attachment_path=None):
        """إرسال عبر SMTP كخيار بديل"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            
            logger.info("🔄 تم تهيئة خدمة SMTP البديلة")
            
            # إعداد SMTP Gmail البديل
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            smtp_user = "esgiftscard@gmail.com"
            smtp_pass = "xopq ikac efpj rdif"
            
            # إنشاء الرسالة
            msg = MIMEMultipart()
            msg['From'] = f"ES-GIFT"
            msg['To'] = email
            msg['Subject'] = subject
            
            # إضافة محتوى HTML
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # إضافة المرفق إن وجد
            if pdf_attachment_path and os.path.exists(pdf_attachment_path):
                with open(pdf_attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(pdf_attachment_path)}'
                    )
                    msg.attach(part)
                    logger.info(f"📎 تم إرفاق الملف: {pdf_attachment_path}")
            
            # إرسال الرسالة
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ تم إرسال الإيميل بنجاح عبر SMTP إلى: {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في SMTP البديل: {e}")
            return False

# تصدير الدوال والكلاسات المطلوبة
__all__ = [
    'EmailSenderProService',
    'email_sender_service',
    'send_verification_email',
    'send_order_confirmation', 
    'send_welcome_email',
    'send_custom_email',
    'get_email_balance',
    'test_email_api',
    'send_email'
]
