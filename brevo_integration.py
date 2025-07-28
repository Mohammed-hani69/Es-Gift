#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تكامل شامل مع Brevo لجميع خدمات البريد الإلكتروني
=================================================

هذا الملف يوحد جميع خدمات البريد الإلكتروني لاستخدام Brevo
ويحل محل Flask-Mail في جميع الخدمات
"""

import os
import logging
from typing import Dict, List, Tuple
from flask import current_app
from brevo_email_service import (
    send_simple_email, 
    send_template_email, 
    send_verification_email,
    send_invoice_email,
    send_order_confirmation_email,
    test_brevo_connection,
    brevo_service
)

# إعداد التسجيل
logger = logging.getLogger(__name__)

class BrevoIntegration:
    """كلاس التكامل الشامل مع Brevo"""
    
    def __init__(self):
        self.initialized = False
        self.test_connection()
    
    def test_connection(self):
        """اختبار الاتصال مع Brevo"""
        try:
            success, message = test_brevo_connection()
            if success:
                logger.info(f"✅ اتصال Brevo ناجح: {message}")
                self.initialized = True
                return success, message
            else:
                logger.error(f"❌ فشل اتصال Brevo: {message}")
                self.initialized = False
                return success, message
        except Exception as e:
            logger.error(f"خطأ في اختبار اتصال Brevo: {str(e)}")
            self.initialized = False
            return False, str(e)
    
    # ========== خدمات البريد الأساسية ==========
    
    def send_email(self, to_email: str, subject: str, body: str, attachments: List = None) -> bool:
        """
        دالة إرسال بريد أساسية - بديل لـ Flask-Mail
        تستخدم في utils.py و email_service.py
        """
        try:
            if not self.initialized:
                logger.warning("Brevo غير مهيأ، محاولة إعادة الاتصال...")
                self.test_connection()
                if not self.initialized:
                    return False
            
            # تحويل المرفقات إذا وجدت
            brevo_attachments = []
            if attachments:
                for attachment in attachments:
                    if isinstance(attachment, dict):
                        brevo_attachments.append(attachment)
            
            success, result = send_simple_email(
                to=to_email,
                subject=subject,
                html_content=body,
                text_content=self._html_to_text(body)
            )
            
            if success:
                logger.info(f"✅ تم إرسال البريد بنجاح إلى {to_email} عبر Brevo")
                return True
            else:
                logger.error(f"❌ فشل إرسال البريد عبر Brevo: {result}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إرسال البريد عبر Brevo: {str(e)}")
            return False
    
    # ========== خدمات التحقق من البريد ==========
    
    def send_verification_email_integrated(self, user) -> bool:
        """
        إرسال بريد التحقق - يحل محل EmailVerificationService
        """
        try:
            if not self.initialized:
                return False
            
            # إنشاء رمز التحقق (نفس الطريقة المستخدمة في EmailVerificationService)
            from email_verification_service import EmailVerificationService
            
            # إنشاء رمز جديد
            verification_token = EmailVerificationService.generate_verification_token()
            
            # حفظ الرمز
            from models import db
            user.email_verification_token = verification_token
            user.email_verification_sent_at = datetime.utcnow()
            db.session.commit()
            
            # إنشاء رابط التحقق
            from flask import url_for
            verification_url = url_for('main.verify_email', 
                                     token=verification_token, 
                                     _external=True)
            
            # إرسال البريد باستخدام Brevo
            success, result = send_verification_email(
                user_email=user.email,
                user_name=user.full_name or user.username or 'عزيزي العميل',
                verification_url=verification_url
            )
            
            if success:
                logger.info(f"✅ تم إرسال بريد التحقق لـ {user.email} عبر Brevo")
                return True
            else:
                logger.error(f"❌ فشل إرسال بريد التحقق عبر Brevo: {result}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إرسال بريد التحقق: {str(e)}")
            return False
    
    # ========== خدمات الطلبات والفواتير ==========
    
    def send_order_email_integrated(self, order) -> Tuple[bool, str]:
        """
        إرسال بريد تأكيد الطلب - يحل محل دالة send_order_email في utils.py
        """
        try:
            if not self.initialized:
                return False, "Brevo غير مهيأ"
            
            order_data = {
                'order_number': str(order.order_number),
                'product_name': order.product.name if order.product else 'منتج رقمي',
                'total_amount': f"{float(order.total_amount):.2f}",
                'currency': order.currency or 'SAR'
            }
            
            success, result = send_order_confirmation_email(
                user_email=order.user.email,
                user_name=order.user.full_name or order.user.username,
                order_data=order_data
            )
            
            if success:
                logger.info(f"✅ تم إرسال بريد تأكيد الطلب #{order.order_number} عبر Brevo")
                return True, "تم إرسال بريد تأكيد الطلب بنجاح"
            else:
                logger.error(f"❌ فشل إرسال بريد الطلب عبر Brevo: {result}")
                return False, f"فشل الإرسال: {result}"
                
        except Exception as e:
            logger.error(f"خطأ في إرسال بريد الطلب: {str(e)}")
            return False, f"خطأ: {str(e)}"
    
    def send_invoice_email_integrated(self, invoice, pdf_content: str = None) -> Tuple[bool, str]:
        """
        إرسال بريد الفاتورة - يحل محل دالة إرسال الفاتورة
        """
        try:
            if not self.initialized:
                return False, "Brevo غير مهيأ"
            
            invoice_data = {
                'invoice_number': invoice.invoice_number,
                'customer_name': invoice.customer_name,
                'total_amount': f"{float(invoice.total_amount):.2f}",
                'currency': invoice.currency,
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d')
            }
            
            success, result = send_invoice_email(
                user_email=invoice.customer_email,
                user_name=invoice.customer_name,
                invoice_data=invoice_data,
                pdf_content=pdf_content
            )
            
            if success:
                logger.info(f"✅ تم إرسال فاتورة #{invoice.invoice_number} عبر Brevo")
                return True, "تم إرسال الفاتورة بنجاح"
            else:
                logger.error(f"❌ فشل إرسال الفاتورة عبر Brevo: {result}")
                return False, f"فشل الإرسال: {result}"
                
        except Exception as e:
            logger.error(f"خطأ في إرسال الفاتورة: {str(e)}")
            return False, f"خطأ: {str(e)}"
    
    # ========== خدمات أكواد المنتجات ==========
    
    def send_product_codes_email_integrated(self, order_data: Dict, product_codes: List, excel_file=None) -> Tuple[bool, str]:
        """
        إرسال أكواد المنتجات - يحل محل ProductCodeEmailService
        """
        try:
            if not self.initialized:
                return False, "Brevo غير مهيأ"
            
            # إنشاء محتوى HTML للبريد
            html_content = self._create_product_codes_html(order_data, product_codes)
            
            # إرسال البريد
            success, result = send_simple_email(
                to=order_data.get('customer_email'),
                subject=f"أكواد منتجاتك - طلب رقم {order_data.get('order_number')}",
                html_content=html_content,
                text_content=f"تم تحضير طلبك #{order_data.get('order_number')} - أكواد المنتجات:"
            )
            
            if success:
                logger.info(f"✅ تم إرسال أكواد المنتجات للطلب #{order_data.get('order_number')} عبر Brevo")
                return True, "تم إرسال أكواد المنتجات بنجاح"
            else:
                logger.error(f"❌ فشل إرسال أكواد المنتجات عبر Brevo: {result}")
                return False, f"فشل الإرسال: {result}"
                
        except Exception as e:
            logger.error(f"خطأ في إرسال أكواد المنتجات: {str(e)}")
            return False, f"خطأ: {str(e)}"
    
    # ========== دوال مساعدة ==========
    
    def _html_to_text(self, html_content: str) -> str:
        """تحويل HTML إلى نص عادي"""
        try:
            import re
            # إزالة علامات HTML
            text = re.sub('<[^<]+?>', '', html_content)
            # تنظيف المسافات
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except:
            return "محتوى البريد الإلكتروني"
    
    def _create_product_codes_html(self, order_data: Dict, product_codes: List) -> str:
        """إنشاء محتوى HTML لأكواد المنتجات"""
        codes_html = ""
        for i, code in enumerate(product_codes, 1):
            codes_html += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{i}</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-family: monospace; font-weight: bold; color: #007bff;">{code}</td>
            </tr>
            """
        
        return f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>أكواد منتجاتك - ES-GIFT</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; margin: 0; padding: 20px; background: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #FF0033 0%, #FF3366 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 2em;">🎁 ES-GIFT</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">أكواد منتجاتك جاهزة!</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <h2 style="color: #333; margin-bottom: 20px;">مرحباً {order_data.get('customer_name', 'عزيزي العميل')}! 👋</h2>
                    
                    <p style="font-size: 16px; line-height: 1.6; color: #666; margin-bottom: 25px;">
                        تم تحضير طلبك بنجاح! إليك أكواد منتجاتك:
                    </p>
                    
                    <!-- Order Info -->
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h3 style="color: #1565c0; margin-top: 0;">📋 معلومات الطلب:</h3>
                        <p><strong>رقم الطلب:</strong> {order_data.get('order_number')}</p>
                        <p><strong>المنتج:</strong> {order_data.get('product_name', 'منتج رقمي')}</p>
                        <p><strong>الكمية:</strong> {len(product_codes)} كود</p>
                        <p><strong>التاريخ:</strong> {order_data.get('order_date', 'اليوم')}</p>
                    </div>
                    
                    <!-- Product Codes -->
                    <div style="margin: 25px 0;">
                        <h3 style="color: #333;">🔑 أكواد المنتجات:</h3>
                        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                            <thead>
                                <tr style="background: #f8f9fa;">
                                    <th style="padding: 12px; border: 1px solid #ddd; color: #333;">#</th>
                                    <th style="padding: 12px; border: 1px solid #ddd; color: #333;">الكود</th>
                                </tr>
                            </thead>
                            <tbody>
                                {codes_html}
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Important Notes -->
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin: 25px 0;">
                        <h4 style="color: #856404; margin-top: 0;">⚠️ ملاحظات مهمة:</h4>
                        <ul style="color: #856404; margin: 10px 0;">
                            <li>احتفظ بهذه الأكواد في مكان آمن</li>
                            <li>لا تشارك الأكواد مع أي شخص آخر</li>
                            <li>في حالة وجود مشكلة، تواصل معنا فوراً</li>
                            <li>صالحية الأكواد حسب شروط المزود</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="color: #666;">إذا كان لديك أي استفسار، لا تتردد في التواصل معنا</p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666;">
                    <p style="margin: 0;">شكراً لثقتك في ES-GIFT - وجهتك الأولى للبطاقات الرقمية</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px;">© 2024 ES-GIFT. جميع الحقوق محفوظة.</p>
                </div>
            </div>
        </body>
        </html>
        """

# ========== إنشاء مثيل التكامل ==========
brevo_integration = BrevoIntegration()

# ========== دوال التوافق العامة ==========

def send_email_brevo(to_email: str, subject: str, body: str, attachments: List = None) -> bool:
    """دالة عامة لإرسال البريد عبر Brevo - بديل utils.send_email"""
    return brevo_integration.send_email(to_email, subject, body, attachments)

def send_verification_email_brevo(user) -> bool:
    """دالة إرسال بريد التحقق عبر Brevo - بديل EmailVerificationService"""
    return brevo_integration.send_verification_email_integrated(user)

def send_order_email_brevo(order) -> Tuple[bool, str]:
    """دالة إرسال بريد الطلب عبر Brevo - بديل utils.send_order_email"""
    return brevo_integration.send_order_email_integrated(order)

def send_invoice_email_brevo(invoice, pdf_content: str = None) -> Tuple[bool, str]:
    """دالة إرسال الفاتورة عبر Brevo"""
    return brevo_integration.send_invoice_email_integrated(invoice, pdf_content)

def send_product_codes_email_brevo(order_data: Dict, product_codes: List, excel_file=None) -> Tuple[bool, str]:
    """دالة إرسال أكواد المنتجات عبر Brevo"""
    return brevo_integration.send_product_codes_email_integrated(order_data, product_codes, excel_file)

def test_brevo_integration() -> Tuple[bool, str]:
    """اختبار التكامل مع Brevo"""
    return brevo_integration.test_connection()

# ========== متغيرات الإعداد السريع ==========
from datetime import datetime

# تصدير المتغيرات المطلوبة
__all__ = [
    'brevo_integration',
    'send_email_brevo',
    'send_verification_email_brevo', 
    'send_order_email_brevo',
    'send_invoice_email_brevo',
    'send_product_codes_email_brevo',
    'test_brevo_integration'
]
