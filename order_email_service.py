# -*- coding: utf-8 -*-
"""
خدمة بريد الطلبات - ES-GIFT
===========================
"""

from product_code_email_service import ProductCodeEmailService

# إنشاء instance من خدمة أكواد المنتجات الرئيسية
product_email_service = ProductCodeEmailService()

# إنشاء instance للتوافق مع routes.py - هذا هو المطلوب
email_service = product_email_service

def init_email_service(app):
    """تهيئة خدمة البريد - للتوافق مع app.py"""
    # هذه الدالة للتوافق فقط، الخدمة الموحدة لا تحتاج تهيئة خاصة
    pass

def send_order_confirmation_email(user_email, user_name, order_data):
    """إرسال تأكيد الطلب"""
    print(f"Order confirmation for {user_email}")
    return True

def send_product_codes_email(user_email, user_name, order_data, product_codes):
    """إرسال أكواد المنتجات"""
    # استخدام خدمة أكواد المنتجات المخصصة
    return product_email_service.send_product_codes_email(order_data, product_codes)
