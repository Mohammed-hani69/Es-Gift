#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة Brevo (SendinBlue) لإرسال الإيميلات
=========================================

هذا الملف يحتوي على جميع وظائف إرسال الإيميلات باستخدام Brevo API
بديل عن Flask-Mail لمزيد من الموثوقية والميزات المتقدمة
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from flask import current_app

from brevo_config import BrevoConfig

# إعداد التسجيل
logger = logging.getLogger(__name__)

@dataclass
class EmailRecipient:
    """بيانات المستقبل"""
    email: str
    name: Optional[str] = None
    attributes: Optional[Dict] = None

@dataclass
class EmailAttachment:
    """بيانات المرفق"""
    content: str  # محتوى الملف مُرمز بـ base64
    name: str     # اسم الملف
    type: Optional[str] = None  # نوع الملف (مثل: application/pdf)

class BrevoEmailService:
    """خدمة إرسال الإيميلات باستخدام Brevo"""
    
    def __init__(self):
        self.config = BrevoConfig
        self.base_url = self.config.BASE_URL
        self.headers = self.config.get_api_headers()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # التحقق من صحة الإعدادات
        is_valid, message = self.config.is_valid_config()
        if not is_valid:
            logger.error(f"Brevo configuration error: {message}")
            raise ValueError(f"خطأ في إعدادات Brevo: {message}")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Tuple[bool, Union[Dict, str]]:
        """إجراء طلب HTTP مع إعادة المحاولة"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=data)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data)
                elif method.upper() == 'PUT':
                    response = self.session.put(url, json=data)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url)
                else:
                    raise ValueError(f"HTTP method غير مدعوم: {method}")
                
                # تسجيل الطلب
                self.config.log_activity('API_REQUEST', f"{method} {endpoint} - Status: {response.status_code}")
                
                if response.status_code in [200, 201, 202]:
                    return True, response.json() if response.content else {}
                elif response.status_code == 429:  # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded, waiting {self.config.RETRY_DELAY} seconds...")
                    time.sleep(self.config.RETRY_DELAY)
                    continue
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return False, error_msg
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY)
                    continue
                return False, f"فشل في الاتصال بـ Brevo: {str(e)}"
        
        return False, "تم تجاوز عدد المحاولات المسموح"
    
    def send_email(self, 
                   to: Union[str, List[str], EmailRecipient, List[EmailRecipient]],
                   subject: str,
                   html_content: str = None,
                   text_content: str = None,
                   sender: Dict = None,
                   attachments: List[EmailAttachment] = None,
                   template_id: int = None,
                   template_params: Dict = None,
                   tags: List[str] = None,
                   headers: Dict = None) -> Tuple[bool, str]:
        """
        إرسال إيميل باستخدام Brevo
        
        Args:
            to: المستقبل/المستقبلون
            subject: موضوع الرسالة
            html_content: محتوى HTML
            text_content: محتوى نصي
            sender: بيانات المرسل
            attachments: المرفقات
            template_id: معرف القالب
            template_params: متغيرات القالب
            tags: علامات للتصنيف
            headers: headers إضافية
        
        Returns:
            Tuple[bool, str]: (نجح الإرسال، رسالة/معرف الرسالة)
        """
        try:
            # إعداد بيانات الطلب
            email_data = {
                "sender": sender or self.config.get_sender_info(),
                "subject": subject,
                "to": self._format_recipients(to)
            }
            
            # إضافة المحتوى
            if template_id:
                email_data["templateId"] = template_id
                if template_params:
                    email_data["params"] = template_params
            else:
                if html_content:
                    email_data["htmlContent"] = html_content
                if text_content:
                    email_data["textContent"] = text_content
            
            # إضافة المرفقات
            if attachments:
                email_data["attachment"] = [
                    {
                        "content": att.content,
                        "name": att.name,
                        **({"type": att.type} if att.type else {})
                    }
                    for att in attachments
                ]
            
            # إضافة العلامات
            if tags:
                email_data["tags"] = tags
            
            # إضافة headers إضافية
            if headers:
                email_data["headers"] = headers
            
            # إضافة إعدادات التتبع
            email_data.update({
                "trackOpens": self.config.TRACKING['open_tracking'],
                "trackClicks": self.config.TRACKING['click_tracking']
            })
            
            # في وضع الاختبار، إرسال لبريد الاختبار
            if self.config.TEST_MODE:
                email_data["to"] = [{
                    "email": self.config.TEST_EMAIL,
                    "name": "Test Recipient"
                }]
                self.config.log_activity('TEST_MODE', f"Email redirected to {self.config.TEST_EMAIL}")
            
            # إرسال الطلب
            success, result = self._make_request('POST', 'smtp/email', email_data)
            
            if success:
                message_id = result.get('messageId', 'unknown')
                self.config.log_activity('EMAIL_SENT', f"Message ID: {message_id}")
                return True, message_id
            else:
                return False, result
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الإيميل: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _format_recipients(self, recipients: Union[str, List[str], EmailRecipient, List[EmailRecipient]]) -> List[Dict]:
        """تنسيق قائمة المستقبلين"""
        if isinstance(recipients, str):
            return [{"email": recipients}]
        
        if isinstance(recipients, EmailRecipient):
            recipient_data = {"email": recipients.email}
            if recipients.name:
                recipient_data["name"] = recipients.name
            return [recipient_data]
        
        if isinstance(recipients, list):
            formatted = []
            for recipient in recipients:
                if isinstance(recipient, str):
                    formatted.append({"email": recipient})
                elif isinstance(recipient, EmailRecipient):
                    recipient_data = {"email": recipient.email}
                    if recipient.name:
                        recipient_data["name"] = recipient.name
                    formatted.append(recipient_data)
                elif isinstance(recipient, dict):
                    formatted.append(recipient)
            return formatted
        
        raise ValueError("تنسيق المستقبلين غير صحيح")
    
    def send_transactional_email(self, 
                                template_id: int,
                                to: Union[str, EmailRecipient],
                                params: Dict = None,
                                sender: Dict = None) -> Tuple[bool, str]:
        """إرسال إيميل تعاملي باستخدام قالب"""
        return self.send_email(
            to=to,
            subject="",  # سيتم أخذه من القالب
            template_id=template_id,
            template_params=params,
            sender=sender
        )
    
    def add_contact_to_list(self, email: str, list_id: int, attributes: Dict = None) -> Tuple[bool, str]:
        """إضافة جهة اتصال لقائمة بريدية"""
        try:
            contact_data = {
                "email": email,
                "listIds": [list_id]
            }
            
            if attributes:
                contact_data["attributes"] = attributes
            
            success, result = self._make_request('POST', 'contacts', contact_data)
            
            if success:
                self.config.log_activity('CONTACT_ADDED', f"Email: {email}, List: {list_id}")
                return True, "تم إضافة الاتصال بنجاح"
            else:
                return False, result
                
        except Exception as e:
            error_msg = f"خطأ في إضافة الاتصال: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_email_events(self, message_id: str) -> Tuple[bool, Union[List[Dict], str]]:
        """الحصول على أحداث إيميل معين"""
        try:
            success, result = self._make_request('GET', f'smtp/statistics/events', {
                'messageId': message_id
            })
            
            if success:
                return True, result.get('events', [])
            else:
                return False, result
                
        except Exception as e:
            error_msg = f"خطأ في الحصول على أحداث الإيميل: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_account_info(self) -> Tuple[bool, Union[Dict, str]]:
        """الحصول على معلومات الحساب"""
        try:
            success, result = self._make_request('GET', 'account')
            
            if success:
                self.config.log_activity('ACCOUNT_INFO', "Retrieved successfully")
                return True, result
            else:
                return False, result
                
        except Exception as e:
            error_msg = f"خطأ في الحصول على معلومات الحساب: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def test_connection(self) -> Tuple[bool, str]:
        """اختبار الاتصال مع Brevo"""
        success, result = self.get_account_info()
        
        if success:
            # التعامل مع النتيجة سواء كانت قاموس أو قائمة
            if isinstance(result, dict):
                account_email = result.get('email', 'غير محدد')
                plan_info = result.get('plan', {})
                plan = plan_info.get('type', 'غير محدد') if isinstance(plan_info, dict) else 'غير محدد'
            elif isinstance(result, list) and len(result) > 0:
                # إذا كانت النتيجة قائمة، استخدم العنصر الأول
                first_item = result[0] if isinstance(result[0], dict) else {}
                account_email = first_item.get('email', 'غير محدد')
                plan_info = first_item.get('plan', {})
                plan = plan_info.get('type', 'غير محدد') if isinstance(plan_info, dict) else 'غير محدد'
            else:
                account_email = 'غير محدد'
                plan = 'غير محدد'
            
            return True, f"الاتصال ناجح - الحساب: {account_email}, الخطة: {plan}"
        else:
            return False, f"فشل الاتصال: {result}"


# إنشاء مثيل الخدمة
brevo_service = BrevoEmailService()

# ========== دوال مساعدة للاستخدام السريع ==========

def send_simple_email(to: str, subject: str, html_content: str, text_content: str = None) -> Tuple[bool, str]:
    """إرسال إيميل بسيط"""
    return brevo_service.send_email(
        to=to,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

def send_template_email(to: str, template_id: int, params: Dict = None) -> Tuple[bool, str]:
    """إرسال إيميل باستخدام قالب"""
    return brevo_service.send_transactional_email(
        template_id=template_id,
        to=to,
        params=params
    )

def send_verification_email(user_email: str, user_name: str, verification_url: str) -> Tuple[bool, str]:
    """إرسال إيميل التحقق"""
    template_id = BrevoConfig.TEMPLATES['email_verification']
    params = {
        'user_name': user_name,
        'verification_url': verification_url,
        'company_name': BrevoConfig.COMPANY_INFO['name_ar']
    }
    
    return send_template_email(user_email, template_id, params)

def send_invoice_email(user_email: str, user_name: str, invoice_data: Dict, pdf_content: str = None) -> Tuple[bool, str]:
    """إرسال إيميل الفاتورة"""
    template_id = BrevoConfig.TEMPLATES['invoice_email']
    params = {
        'user_name': user_name,
        'invoice_number': invoice_data.get('invoice_number'),
        'total_amount': invoice_data.get('total_amount'),
        'currency': invoice_data.get('currency'),
        'company_name': BrevoConfig.COMPANY_INFO['name_ar']
    }
    
    attachments = []
    if pdf_content:
        attachments.append(EmailAttachment(
            content=pdf_content,
            name=f"invoice_{invoice_data.get('invoice_number')}.pdf",
            type="application/pdf"
        ))
    
    return brevo_service.send_email(
        to=user_email,
        subject="",  # سيتم أخذه من القالب
        template_id=template_id,
        template_params=params,
        attachments=attachments
    )

def send_order_confirmation_email(user_email: str, user_name: str, order_data: Dict) -> Tuple[bool, str]:
    """إرسال إيميل تأكيد الطلب"""
    template_id = BrevoConfig.TEMPLATES['order_confirmation']
    params = {
        'user_name': user_name,
        'order_number': order_data.get('order_number'),
        'product_name': order_data.get('product_name'),
        'total_amount': order_data.get('total_amount'),
        'currency': order_data.get('currency'),
        'company_name': BrevoConfig.COMPANY_INFO['name_ar']
    }
    
    return send_template_email(user_email, template_id, params)

def test_brevo_connection() -> Tuple[bool, str]:
    """اختبار الاتصال مع Brevo"""
    return brevo_service.test_connection()

# ========== دوال للتوافق مع النظام الحالي ==========

def send_email(to_email: str, subject: str, body: str, attachments: List[Dict] = None) -> bool:
    """
    دالة للتوافق مع النظام الحالي
    تحويل من Flask-Mail إلى Brevo
    """
    try:
        # تحويل المرفقات إلى تنسيق Brevo
        brevo_attachments = []
        if attachments:
            for att in attachments:
                if isinstance(att, dict) and 'content' in att and 'filename' in att:
                    brevo_attachments.append(EmailAttachment(
                        content=att['content'],
                        name=att['filename'],
                        type=att.get('content_type')
                    ))
        
        success, result = brevo_service.send_email(
            to=to_email,
            subject=subject,
            html_content=body,
            attachments=brevo_attachments if brevo_attachments else None
        )
        
        if success:
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email to {to_email}: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error in send_email compatibility function: {str(e)}")
        return False
