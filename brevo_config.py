#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعدادات Brevo (SendinBlue) API
===============================

هذا الملف يحتوي على جميع إعدادات API الخاصة بـ Brevo
لإرسال الإيميلات والرسائل النصية

ملاحظة: يجب تغيير القيم الافتراضية بالقيم الحقيقية
"""

import os
from datetime import datetime

# تعطيل Brevo مؤقتاً لحل مشاكل API Key
DISABLE_BREVO = False

class BrevoConfig:
    """إعدادات Brevo API"""
    
    # ========== معلومات API الأساسية ==========
    # احصل على API Key من: https://app.brevo.com/settings/keys/api
    # ضع المفتاح الحقيقي هنا أو في متغير البيئة BREVO_API_KEY
    API_KEY = os.getenv('BREVO_API_KEY', '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')
    
    # Base URL لـ Brevo API
    BASE_URL = 'https://api.brevo.com/v3'
    
    # ========== معلومات المرسل الافتراضي ==========
    # ضع بريدك الإلكتروني المتحقق منه في Brevo هنا
    DEFAULT_SENDER = {
        'name': 'ES-GIFT',
        'email': os.getenv('BREVO_SENDER_EMAIL', 'mohamedeloker9@gmail.com')
    }
    
    # ========== إعدادات القوالب ==========
    # معرفات القوالب في Brevo (يتم إنشاؤها في لوحة التحكم)
    TEMPLATES = {
        'email_verification': os.getenv('BREVO_TEMPLATE_VERIFICATION', 1),  # معرف قالب التحقق
        'order_confirmation': os.getenv('BREVO_TEMPLATE_ORDER', 2),        # معرف قالب تأكيد الطلب
        'invoice_email': os.getenv('BREVO_TEMPLATE_INVOICE', 3),           # معرف قالب الفاتورة
        'welcome_email': os.getenv('BREVO_TEMPLATE_WELCOME', 4),           # معرف قالب الترحيب
        'password_reset': os.getenv('BREVO_TEMPLATE_PASSWORD', 5),         # معرف قالب إعادة تعيين كلمة المرور
        'product_codes': os.getenv('BREVO_TEMPLATE_CODES', 6),             # معرف قالب أكواد المنتجات
    }
    
    # ========== إعدادات القوائم البريدية ==========
    # معرفات القوائم البريدية في Brevo
    CONTACT_LISTS = {
        'main_customers': os.getenv('BREVO_LIST_CUSTOMERS', 1),     # قائمة العملاء الرئيسية
        'vip_customers': os.getenv('BREVO_LIST_VIP', 2),           # قائمة العملاء المميزين
        'newsletter': os.getenv('BREVO_LIST_NEWSLETTER', 3),        # قائمة النشرة الإخبارية
        'resellers': os.getenv('BREVO_LIST_RESELLERS', 4),         # قائمة الموزعين
    }
    
    # ========== إعدادات الإرسال ==========
    MAX_RETRIES = 3                    # عدد محاولات الإرسال عند الفشل
    RETRY_DELAY = 2                    # التأخير بين المحاولات (بالثواني)
    
    # معدل الإرسال (عدد الرسائل في الدقيقة حسب خطة Brevo)
    RATE_LIMIT = {
        'free': 300,      # 300 رسالة في اليوم للخطة المجانية
        'starter': 20000, # 20,000 رسالة في الشهر
        'business': 60000, # 60,000 رسالة في الشهر
        'enterprise': None # بدون حد
    }
    
    # خطة Brevo الحالية
    CURRENT_PLAN = os.getenv('BREVO_PLAN', 'free')
    
    # ========== إعدادات التتبع ==========
    TRACKING = {
        'open_tracking': True,      # تتبع فتح الرسائل
        'click_tracking': True,     # تتبع النقر على الروابط
        'unsubscribe_tracking': True # تتبع إلغاء الاشتراك
    }
    
    # ========== إعدادات الأمان ==========
    # تشفير البيانات الحساسة
    ENCRYPT_SENSITIVE_DATA = True
    
    # تسجيل العمليات
    LOG_EMAIL_ACTIVITIES = True
    LOG_LEVEL = os.getenv('BREVO_LOG_LEVEL', 'INFO')
    
    # ========== إعدادات الاختبار ==========
    # في وضع الاختبار، لن يتم إرسال رسائل حقيقية
    TEST_MODE = os.getenv('BREVO_TEST_MODE', 'False').lower() == 'true'
    
    # بريد إلكتروني للاختبار (سيتم إرسال جميع الرسائل إليه في وضع الاختبار)
    TEST_EMAIL = os.getenv('BREVO_TEST_EMAIL', 'test@es-gift.com')
    
    # تعطيل Brevo مؤقتاً عند وجود مشاكل في API
    DISABLE_BREVO = os.getenv('DISABLE_BREVO', 'False').lower() == 'true'
    
    # ========== إعدادات SMTP ==========
    SMTP_CONFIG = {
        'server': 'smtp-relay.brevo.com',
        'port': 587,
        'username': '932dac001@smtp-brevo.com',
        'password': 'O6RxAm3kJYp0BzE2',
        'use_tls': True,
        'use_ssl': False
    }
    
    # ========== إعدادات التخصيص ==========
    # ألوان العلامة التجارية
    BRAND_COLORS = {
        'primary': '#FF0033',
        'secondary': '#1a1a1a',
        'accent': '#667eea',
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545'
    }
    
    # معلومات الشركة
    COMPANY_INFO = {
        'name': 'ES-GIFT',
        'name_ar': 'إس جيفت',
        'website': 'https://es-gift.com',
        'support_email': 'support@es-gift.com',
        'phone': '+966XXXXXXXXX',
        'address': 'المملكة العربية السعودية',
        'logo_url': 'https://es-gift.com/static/images/logo.png'
    }
    
    # ========== إعدادات المنطقة الزمنية واللغة ==========
    TIMEZONE = 'Asia/Riyadh'
    DEFAULT_LANGUAGE = 'ar'
    SUPPORTED_LANGUAGES = ['ar', 'en']
    
    # ========== دوال مساعدة ==========
    @classmethod
    def get_api_headers(cls):
        """إرجاع headers الـ API المطلوبة"""
        return {
            'accept': 'application/json',
            'content-type': 'application/json',
            'api-key': cls.API_KEY
        }
    
    @classmethod
    def get_sender_info(cls, custom_sender=None):
        """إرجاع معلومات المرسل"""
        if custom_sender:
            return custom_sender
        return cls.DEFAULT_SENDER
    
    @classmethod
    def is_valid_config(cls):
        """التحقق من صحة الإعدادات"""
        if not cls.API_KEY or cls.API_KEY == 'xkeysib-YOUR_API_KEY_HERE-REPLACE_THIS':
            return False, "API Key غير محدد أو يحتوي على القيمة الافتراضية"
        
        if not cls.DEFAULT_SENDER['email'] or '@' not in cls.DEFAULT_SENDER['email']:
            return False, "بريد المرسل الافتراضي غير صحيح"
        
        return True, "الإعدادات صحيحة"
    
    @classmethod
    def get_rate_limit(cls):
        """إرجاع حد الإرسال للخطة الحالية"""
        return cls.RATE_LIMIT.get(cls.CURRENT_PLAN, cls.RATE_LIMIT['free'])
    
    @classmethod
    def log_activity(cls, activity_type, details):
        """تسجيل النشاط إذا كان مفعلاً"""
        if cls.LOG_EMAIL_ACTIVITIES:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Brevo {activity_type}: {details}")


# ========== متغيرات سريعة للوصول ==========
BREVO_API_KEY = BrevoConfig.API_KEY
BREVO_SENDER = BrevoConfig.DEFAULT_SENDER
BREVO_TEST_MODE = BrevoConfig.TEST_MODE

# ========== إرشادات الاستخدام ==========
"""
لاستخدام إعدادات Brevo:

1. احصل على API Key من https://app.brevo.com/settings/keys/api
2. غير قيمة BREVO_API_KEY في ملف .env أو هنا مباشرة
3. قم بإنشاء القوالب في لوحة تحكم Brevo واحصل على معرفاتها
4. حدث معرفات القوالب في TEMPLATES
5. أنشئ القوائم البريدية وحدث معرفاتها في CONTACT_LISTS

مثال على ملف .env:
BREVO_API_KEY=xkeysib-your-real-api-key-here
BREVO_SENDER_EMAIL=noreply@yourdomain.com
BREVO_TEST_MODE=False
BREVO_PLAN=starter

للحصول على معرف القالب:
1. اذهب إلى Templates في لوحة تحكم Brevo
2. انشئ قالب جديد أو استخدم موجود
3. معرف القالب يظهر في الرابط: /templates/edit/[TEMPLATE_ID]
"""
