#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة Email Sender Pro API لإرسال الرسائل الإلكترونية
==================================================

تكامل مع Email Sender Pro API لإرسال رسائل التحقق، الطلبات، والترحيب
API Documentation: http://verifix-otp.escovfair.com
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
    """خدمة Email Sender Pro API"""
    
    def __init__(self):
        """تهيئة الخدمة"""
        self.base_url = "http://verifix-otp.escovfair.com/api"
        self.api_key = "2cb88c9c5cfa46429d17b68b928321b9"
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        self.timeout = 30  # مهلة زمنية للطلبات
        
    def _make_request(self, endpoint: str, data: Dict, method: str = "POST") -> Tuple[bool, Dict]:
        """إجراء طلب HTTP إلى API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            logger.info(f"📤 طلب API: {method} {endpoint}")
            logger.debug(f"البيانات: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            if method.upper() == "GET":
                response = requests.get(
                    url, 
                    headers=self.headers,
                    params=data,
                    timeout=self.timeout
                )
            else:
                response = requests.post(
                    url, 
                    headers=self.headers, 
                    json=data,
                    timeout=self.timeout
                )
            
            logger.info(f"📥 استجابة API: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"النتيجة: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return True, result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
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
    
    def send_verification_code(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """
        إرسال كود التحقق
        
        Args:
            email (str): البريد الإلكتروني للمستقبل
            
        Returns:
            Tuple[bool, str, Optional[str]]: (نجح, رسالة, كود التحقق)
        """
        try:
            logger.info(f"🔐 إرسال كود التحقق إلى: {email}")
            
            data = {"email": email}
            
            # جرب GET method أولاً
            success, result = self._make_request("send-verification", data, "GET")
            
            # إذا فشل GET، جرب POST
            if not success and "405" in str(result.get('error', '')):
                logger.info("🔄 محاولة POST method...")
                success, result = self._make_request("send-verification", data, "POST")
            
            if success and result.get('success'):
                verification_code = result.get('verification_code')
                remaining_balance = result.get('remaining_balance', 'غير متوفر')
                free_messages = result.get('free_messages_remaining', 'غير متوفر')
                
                logger.info(f"✅ تم إرسال كود التحقق بنجاح")
                logger.info(f"💰 الرصيد المتبقي: {remaining_balance}")
                logger.info(f"📨 الرسائل المجانية المتبقية: {free_messages}")
                
                return True, "تم إرسال كود التحقق بنجاح", verification_code
            else:
                error_msg = result.get('error', 'فشل في إرسال كود التحقق')
                logger.error(f"❌ فشل إرسال كود التحقق: {error_msg}")
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
            
            success, result = self._make_request("send-order", data)
            
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
            
            success, result = self._make_request("send-welcome", data)
            
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
    
    def send_custom_message(self, email: str, subject: str, message_content: str, 
                           message_title: str = None) -> Tuple[bool, str]:
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
            
            success, result = self._make_request("send-custom", data)
            
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
    
    def get_balance(self) -> Tuple[bool, Dict]:
        """
        الحصول على الرصيد المتبقي
        
        Returns:
            Tuple[bool, Dict]: (نجح, بيانات الرصيد)
        """
        try:
            logger.info("💰 فحص الرصيد المتبقي...")
            
            url = f"{self.base_url}/balance"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ تم جلب بيانات الرصيد بنجاح")
                return True, result
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
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
            
            # اختبار بسيط للحصول على الرصيد
            success, result = self.get_balance()
            
            if success:
                balance = result.get('balance', 'غير متوفر')
                return True, f"✅ الاتصال ناجح - الرصيد: {balance}"
            else:
                return False, f"❌ فشل الاتصال: {result.get('error', 'خطأ غير محدد')}"
                
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
