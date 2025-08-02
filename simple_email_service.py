#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة التحقق البسيطة من البريد الإلكتروني
===========================================

خدمة بديلة تخزن كود التحقق في قاعدة البيانات وتحاكي إرسال البريد الإلكتروني
"""

import random
import string
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional
from flask import current_app
from models import db, User

# إعداد التسجيل
logger = logging.getLogger(__name__)

class SimpleEmailVerificationService:
    """خدمة التحقق البسيطة من البريد الإلكتروني"""
    
    def __init__(self):
        self.code_expiry_minutes = 15  # مدة انتهاء صلاحية الكود
        
    def generate_verification_code(self) -> str:
        """توليد كود تحقق من 6 أرقام"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_verification_code(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """
        إرسال كود التحقق (محاكاة)
        
        Args:
            email (str): البريد الإلكتروني
            
        Returns:
            Tuple[bool, str, Optional[str]]: (نجح, رسالة, كود التحقق)
        """
        try:
            logger.info(f"📧 إرسال كود تحقق بسيط إلى: {email}")
            
            # توليد كود التحقق
            verification_code = self.generate_verification_code()
            
            # البحث عن المستخدم
            user = User.query.filter_by(email=email).first()
            
            if user:
                # تحديث بيانات التحقق
                user.email_verification_token = verification_code
                user.email_verification_sent_at = datetime.utcnow()
                
                # حفظ في قاعدة البيانات
                db.session.commit()
                
                logger.info(f"✅ تم حفظ كود التحقق في قاعدة البيانات: {verification_code}")
                logger.info(f"📝 للاختبار: يمكنك استخدام الكود: {verification_code}")
                
                return True, "تم إرسال كود التحقق بنجاح", verification_code
            else:
                logger.error(f"❌ المستخدم غير موجود: {email}")
                return False, "البريد الإلكتروني غير مسجل", None
                
        except Exception as e:
            error_msg = f"خطأ في إرسال كود التحقق: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg, None
    
    def verify_code(self, email: str, code: str) -> Tuple[bool, str]:
        """
        التحقق من صحة الكود
        
        Args:
            email (str): البريد الإلكتروني
            code (str): كود التحقق
            
        Returns:
            Tuple[bool, str]: (نجح, رسالة)
        """
        try:
            logger.info(f"🔐 التحقق من كود: {code} للإيميل: {email}")
            
            # البحث عن المستخدم
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return False, "البريد الإلكتروني غير مسجل"
            
            if not user.email_verification_token:
                return False, "لا يوجد كود تحقق مرسل"
            
            # التحقق من انتهاء صلاحية الكود
            if user.email_verification_sent_at:
                expiry_time = user.email_verification_sent_at + timedelta(minutes=self.code_expiry_minutes)
                if datetime.utcnow() > expiry_time:
                    return False, "انتهت صلاحية كود التحقق"
            
            # التحقق من صحة الكود
            if user.email_verification_token == code:
                # تفعيل الحساب
                user.is_verified = True
                user.email_verification_token = None
                user.email_verification_sent_at = None
                
                db.session.commit()
                
                logger.info(f"✅ تم التحقق بنجاح من الإيميل: {email}")
                return True, "تم التحقق من البريد الإلكتروني بنجاح"
            else:
                logger.warning(f"⚠️ كود خاطئ: {code} (المتوقع: {user.email_verification_token})")
                return False, "كود التحقق غير صحيح"
                
        except Exception as e:
            error_msg = f"خطأ في التحقق من الكود: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

# إنشاء instance عام
simple_email_service = SimpleEmailVerificationService()
