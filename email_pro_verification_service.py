#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة التحقق من البريد الإلكتروني باستخدام Email Sender Pro
========================================================

هذه الخدمة تدير كامل عملية التحقق من البريد الإلكتروني للمستخدمين الجدد
باستخدام Email Sender Pro API مع نظام أكواد التحقق من 6 خانات ونظام احتياطي
"""

import random
import string
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from flask import current_app, session
from email_sender_pro_service import send_verification_email, send_welcome_email
from email_fallback_service import fallback_email_service
from simple_email_service import simple_email_service

# إعداد التسجيل
logger = logging.getLogger(__name__)

class EmailProVerificationService:
    """خدمة التحقق من البريد الإلكتروني باستخدام Email Sender Pro"""
    
    def __init__(self):
        """تهيئة الخدمة"""
        self.verification_codes = {}  # مخزن أكواد التحقق المؤقت
        self.code_expiry_minutes = 15  # مدة انتهاء صلاحية الكود (15 دقيقة)
        self.max_attempts = 3  # عدد المحاولات القصوى لإدخال الكود
        
    def generate_verification_code(self) -> str:
        """توليد كود تحقق من 6 أرقام"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_verification_code(self, email: str, user_name: str) -> Tuple[bool, str, Optional[str]]:
        """
        إرسال كود التحقق للمستخدم مع نظام احتياطي
        
        Args:
            email (str): البريد الإلكتروني للمستخدم
            user_name (str): اسم المستخدم
            
        Returns:
            Tuple[bool, str, Optional[str]]: (نجح, رسالة, كود التحقق)
        """
        try:
            logger.info(f"🔐 بدء إرسال كود التحقق إلى: {email}")
            
            # محاولة إرسال كود التحقق عبر Email Sender Pro API
            success, message, verification_code = send_verification_email(email)
            
            # إذا فشلت الخدمة الرئيسية، استخدم النظام الاحتياطي
            if not success:
                logger.warning(f"⚠️ فشلت الخدمة الرئيسية، جاري استخدام النظام الاحتياطي...")
                
                # توليد كود تحقق جديد
                verification_code = self.generate_verification_code()
                
                # إرسال عبر النظام الاحتياطي الأول (SMTP)
                fallback_success, fallback_message = fallback_email_service.send_verification_email(
                    email, verification_code
                )
                
                if fallback_success:
                    success = True
                    message = "تم إرسال كود التحقق بنجاح (النظام الاحتياطي - SMTP)"
                    logger.info(f"✅ تم إرسال كود التحقق عبر النظام الاحتياطي الأول")
                else:
                    # استخدام النظام الاحتياطي الثاني (قاعدة البيانات)
                    logger.warning(f"⚠️ فشل النظام الاحتياطي الأول، جاري استخدام النظام البسيط...")
                    
                    simple_success, simple_message, simple_code = simple_email_service.send_verification_code(email)
                    
                    if simple_success:
                        success = True
                        message = "تم إرسال كود التحقق بنجاح (النظام البسيط)"
                        verification_code = simple_code
                        logger.info(f"✅ تم إرسال كود التحقق عبر النظام البسيط: {verification_code}")
                    else:
                        logger.error(f"❌ فشلت جميع الأنظمة: {simple_message}")
                        return False, "فشل في إرسال كود التحقق. يرجى المحاولة لاحقاً", None
            
            if success and verification_code:
                # حفظ كود التحقق مع معلومات المستخدم
                expiry_time = datetime.now() + timedelta(minutes=self.code_expiry_minutes)
                self.verification_codes[email] = {
                    'code': verification_code,
                    'user_name': user_name,
                    'expiry': expiry_time,
                    'attempts': 0,
                    'created_at': datetime.now()
                }
                
                # حفظ في الجلسة أيضاً
                session['verification_email'] = email
                session['verification_pending'] = True
                
                logger.info(f"✅ تم إرسال كود التحقق بنجاح: {verification_code}")
                logger.info(f"⏰ صالح حتى: {expiry_time}")
                
                return True, "تم إرسال كود التحقق بنجاح إلى بريدك الإلكتروني", verification_code
            else:
                logger.error(f"❌ فشل إرسال كود التحقق: {message}")
                return False, f"فشل في إرسال كود التحقق: {message}", None
                
        except Exception as e:
            error_msg = f"خطأ في إرسال كود التحقق: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg, None
    
    def verify_code(self, email: str, entered_code: str) -> Tuple[bool, str]:
        """
        التحقق من كود التحقق المدخل مع دعم الأنظمة المتعددة
        
        Args:
            email (str): البريد الإلكتروني
            entered_code (str): الكود المدخل من المستخدم
            
        Returns:
            Tuple[bool, str]: (صحيح, رسالة)
        """
        try:
            logger.info(f"🔍 التحقق من كود التحقق للبريد: {email}")
            
            # أولاً: محاولة التحقق من خلال النظام البسيط (قاعدة البيانات)
            simple_success, simple_message = simple_email_service.verify_code(email, entered_code)
            
            if simple_success:
                logger.info(f"✅ تم التحقق بنجاح عبر النظام البسيط")
                session.pop('verification_pending', None)
                session['email_verified'] = True
                session['verified_email'] = email
                return True, simple_message
            
            # ثانياً: التحقق من خلال النظام المحلي (في الذاكرة)
            if email not in self.verification_codes:
                logger.warning(f"⚠️ لا يوجد كود تحقق لهذا البريد: {email}")
                return False, "لم يتم العثور على كود تحقق لهذا البريد الإلكتروني"
            
            verification_data = self.verification_codes[email]
            
            # التحقق من انتهاء صلاحية الكود
            if datetime.now() > verification_data['expiry']:
                logger.warning(f"⏰ انتهت صلاحية كود التحقق للبريد: {email}")
                # حذف الكود المنتهي الصلاحية
                del self.verification_codes[email]
                return False, "انتهت صلاحية كود التحقق، يرجى طلب كود جديد"
            
            # التحقق من عدد المحاولات
            if verification_data['attempts'] >= self.max_attempts:
                logger.warning(f"🚫 تم تجاوز عدد المحاولات المسموح للبريد: {email}")
                # حذف الكود بعد تجاوز المحاولات
                del self.verification_codes[email]
                return False, "تم تجاوز عدد المحاولات المسموح، يرجى طلب كود جديد"
            
            # زيادة عدد المحاولات
            verification_data['attempts'] += 1
            
            # التحقق من صحة الكود
            if entered_code == verification_data['code']:
                logger.info(f"✅ تم التحقق بنجاح من الكود للبريد: {email}")
                
                # حذف كود التحقق بعد النجاح
                user_name = verification_data['user_name']
                del self.verification_codes[email]
                
                # تحديث الجلسة
                session.pop('verification_pending', None)
                session['email_verified'] = True
                session['verified_email'] = email
                
                # إرسال رسالة ترحيبية
                try:
                    self.send_welcome_message(email, user_name)
                except Exception as e:
                    logger.warning(f"⚠️ فشل إرسال الرسالة الترحيبية: {str(e)}")
                
                return True, "تم التحقق من البريد الإلكتروني بنجاح"
            else:
                remaining_attempts = self.max_attempts - verification_data['attempts']
                logger.warning(f"❌ كود خاطئ للبريد {email}، المحاولات المتبقية: {remaining_attempts}")
                
                if remaining_attempts > 0:
                    return False, f"كود التحقق غير صحيح، لديك {remaining_attempts} محاولة متبقية"
                else:
                    # حذف الكود بعد نفاد المحاولات
                    del self.verification_codes[email]
                    return False, "كود التحقق غير صحيح، تم نفاد المحاولات المسموح بها"
                
        except Exception as e:
            error_msg = f"خطأ في التحقق من الكود: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def resend_verification_code(self, email: str) -> Tuple[bool, str]:
        """
        إعادة إرسال كود التحقق
        
        Args:
            email (str): البريد الإلكتروني
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"🔄 إعادة إرسال كود التحقق للبريد: {email}")
            
            # التحقق من وجود كود سابق
            if email in self.verification_codes:
                user_name = self.verification_codes[email]['user_name']
                # حذف الكود القديم
                del self.verification_codes[email]
            else:
                # إذا لم يكن هناك كود سابق، استخدم اسم افتراضي
                user_name = "عزيزي المستخدم"
            
            # إرسال كود جديد
            success, message, verification_code = self.send_verification_code(email, user_name)
            
            if success:
                logger.info(f"✅ تم إعادة إرسال كود التحقق بنجاح")
                return True, "تم إعادة إرسال كود التحقق بنجاح"
            else:
                return False, message
                
        except Exception as e:
            error_msg = f"خطأ في إعادة إرسال كود التحقق: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def send_welcome_message(self, email: str, user_name: str) -> Tuple[bool, str]:
        """
        إرسال رسالة ترحيبية للمستخدم الجديد
        
        Args:
            email (str): البريد الإلكتروني
            user_name (str): اسم المستخدم
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"🎉 إرسال رسالة ترحيبية للمستخدم: {user_name} ({email})")
            
            success, message = send_welcome_email(email, user_name)
            
            if success:
                logger.info(f"✅ تم إرسال الرسالة الترحيبية بنجاح")
                return True, "تم إرسال الرسالة الترحيبية بنجاح"
            else:
                logger.warning(f"⚠️ فشل إرسال الرسالة الترحيبية: {message}")
                return False, message
                
        except Exception as e:
            error_msg = f"خطأ في إرسال الرسالة الترحيبية: {str(e)}"
            logger.warning(f"⚠️ {error_msg}")
            return False, error_msg
    
    def is_email_verification_pending(self, email: str) -> bool:
        """التحقق من وجود كود تحقق معلق للبريد الإلكتروني"""
        return email in self.verification_codes
    
    def get_verification_info(self, email: str) -> Optional[Dict]:
        """الحصول على معلومات التحقق للبريد الإلكتروني"""
        if email in self.verification_codes:
            data = self.verification_codes[email].copy()
            # تحويل التاريخ إلى نص قابل للقراءة
            data['expiry_str'] = data['expiry'].strftime('%H:%M:%S')
            data['time_remaining'] = max(0, int((data['expiry'] - datetime.now()).total_seconds()))
            return data
        return None
    
    def cleanup_expired_codes(self):
        """تنظيف أكواد التحقق المنتهية الصلاحية"""
        try:
            current_time = datetime.now()
            expired_emails = [
                email for email, data in self.verification_codes.items()
                if current_time > data['expiry']
            ]
            
            for email in expired_emails:
                logger.info(f"🧹 حذف كود التحقق المنتهي الصلاحية للبريد: {email}")
                del self.verification_codes[email]
                
            if expired_emails:
                logger.info(f"✅ تم تنظيف {len(expired_emails)} كود منتهي الصلاحية")
                
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف الأكواد المنتهية: {str(e)}")


# إنشاء مثيل الخدمة العامة
email_verification_service = EmailProVerificationService()

# ========== دوال مساعدة للاستخدام السريع ==========

def send_user_verification_code(email: str, user_name: str) -> Tuple[bool, str, Optional[str]]:
    """
    دالة مساعدة لإرسال كود التحقق للمستخدم
    
    Args:
        email (str): البريد الإلكتروني
        user_name (str): اسم المستخدم
        
    Returns:
        Tuple[bool, str, Optional[str]]: (نجح, رسالة, كود التحقق)
    """
    return email_verification_service.send_verification_code(email, user_name)

def verify_user_code(email: str, code: str) -> Tuple[bool, str]:
    """
    دالة مساعدة للتحقق من كود المستخدم
    
    Args:
        email (str): البريد الإلكتروني
        code (str): الكود المدخل
        
    Returns:
        Tuple[bool, str]: (صحيح, رسالة)
    """
    return email_verification_service.verify_code(email, code)

def resend_user_verification_code(email: str) -> Tuple[bool, str]:
    """
    دالة مساعدة لإعادة إرسال كود التحقق
    
    Args:
        email (str): البريد الإلكتروني
        
    Returns:
        Tuple[bool, str]: (نجح, رسالة)
    """
    return email_verification_service.resend_verification_code(email)

def is_verification_pending(email: str) -> bool:
    """التحقق من وجود تحقق معلق"""
    return email_verification_service.is_email_verification_pending(email)

def get_user_verification_info(email: str) -> Optional[Dict]:
    """الحصول على معلومات التحقق"""
    return email_verification_service.get_verification_info(email)

def send_user_welcome_message(email: str, user_name: str) -> Tuple[bool, str]:
    """إرسال رسالة ترحيبية"""
    return email_verification_service.send_welcome_message(email, user_name)

# تصدير الدوال والكلاسات المطلوبة
__all__ = [
    'EmailProVerificationService',
    'email_verification_service',
    'send_user_verification_code',
    'verify_user_code',
    'resend_user_verification_code',
    'is_verification_pending',
    'get_user_verification_info',
    'send_user_welcome_message'
]
