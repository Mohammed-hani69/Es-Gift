# -*- coding: utf-8 -*-
"""
خدمة بريد الطلبات - ES-GIFT
===========================
"""

# from clean_unified_email_service import unified_email_service
# الخدمة البديلة المؤقتة
class UnifiedEmailService:
    def send_order_confirmation(self, user_email, user_name, order_data):
        print(f"Email would be sent to {user_email} for order confirmation")
        return True
    
    def send_product_codes(self, user_email, products_with_codes):
        print(f"Product codes would be sent to {user_email}")
        return True

unified_email_service = UnifiedEmailService()
from product_code_email_service import ProductCodeEmailService

# إنشاء instance من خدمة أكواد المنتجات
product_email_service = ProductCodeEmailService()

def init_email_service(app):
    """تهيئة خدمة البريد - للتوافق مع app.py"""
    # هذه الدالة للتوافق فقط، الخدمة الموحدة لا تحتاج تهيئة خاصة
    pass

def send_order_confirmation_email(user_email, user_name, order_data):
    """إرسال تأكيد الطلب"""
    return unified_email_service.send_order_confirmation(user_email, user_name, order_data)

def send_product_codes_email(user_email, user_name, order_data, product_codes):
    """إرسال أكواد المنتجات"""
    # استخدام خدمة أكواد المنتجات المخصصة
    return product_email_service.send_product_codes_email(order_data, product_codes)

# للتوافق مع الكود القديم
class ProductCodeEmailService:
    """كلاس للتوافق مع الكود القديم"""
    
    def __init__(self):
        self.service = product_email_service
    
    def send_product_codes_email(self, order_data, product_codes):
        """إرسال أكواد المنتجات"""
        return self.service.send_product_codes_email(order_data, product_codes)
