#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إنشاء فواتير حديثة وجذابة مع إرسال البريد الإلكتروني
"""

# استيراد الخدمة الإنجليزية المتميزة الجديدة مع تصميم أحمر ولوجو ES-GIFT
from premium_english_invoice_service import PremiumEnglishInvoiceService

# استخدام الخدمة الإنجليزية المتميزة كخدمة افتراضية
ModernInvoiceService = PremiumEnglishInvoiceService

def _send_invoice_email_fallback(invoice, email_html, pdf_full_path):
    """إرسال الفاتورة باستخدام Flask-Mail كبديل"""
    try:
        from flask_mail import Message, Mail
        from flask import current_app
        
        mail = current_app.extensions.get('mail')
        if not mail:
            print("خدمة البريد الإلكتروني غير مكونة")
            return False
        
        msg = Message(
            subject=f"🎁 ES-GIFT Invoice - {invoice.invoice_number}",
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[invoice.customer_email]
        )
        
        msg.html = email_html
        
        # إضافة الفاتورة كمرفق
        with open(pdf_full_path, 'rb') as fp:
            msg.attach(
                filename=f"ES-GIFT_Invoice_{invoice.invoice_number}.pdf",
                content_type='application/pdf',
                data=fp.read()
            )
        
        mail.send(msg)
        print(f"تم إرسال الفاتورة بنجاح إلى: {invoice.customer_email} باستخدام Flask-Mail")
        return True
        
    except Exception as e:
        print(f"خطأ في إرسال البريد الإلكتروني باستخدام Flask-Mail: {e}")
        return False

# إنشاء alias للتوافق مع الكود الحالي
InvoiceService = ModernInvoiceService
