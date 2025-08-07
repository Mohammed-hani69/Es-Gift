#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إرسال الفواتير المحسنة مع الإعدادات البديلة المضمونة
==========================================================
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
import os
from datetime import datetime

def send_invoice_guaranteed(invoice, recipient_email=None):
    """
    إرسال الفاتورة بطريقة مضمونة باستخدام Gmail
    """
    try:
        email_to_send = recipient_email or invoice.customer_email
        
        if not email_to_send:
            print("❌ No email address provided")
            return False
        
        print(f"📧 إرسال فاتورة {invoice.invoice_number} إلى: {email_to_send}")
        
        # إعدادات Gmail البديلة المضمونة
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "esgiftscard@gmail.com"
        sender_password = "xopq ikac efpj rdif"
        
        # تحديد اللغة
        has_arabic = any('\u0600' <= char <= '\u06FF' for char in (invoice.customer_name + (invoice.notes or '')))
        
        if has_arabic:
            subject = f"🎁 فاتورة ES-GIFT - {invoice.invoice_number}"
            customer_greeting = f"عزيزي/عزيزتي {invoice.customer_name}"
            main_text = "نشكركم لاختياركم ES-GIFT. يسعدنا إرسال فاتورتكم."
            details_title = "تفاصيل الفاتورة:"
            invoice_number_text = "رقم الفاتورة:"
            date_text = "التاريخ:"
            total_text = "المبلغ الإجمالي:"
            status_text = "حالة الدفع:"
            contact_text = "إذا كان لديكم أي استفسارات، لا تترددوا في التواصل معنا على:"
            thanks_text = "شكراً لكم مرة أخرى لثقتكم في ES-GIFT"
        else:
            subject = f"🎁 ES-GIFT Invoice - {invoice.invoice_number}"
            customer_greeting = f"Dear {invoice.customer_name}"
            main_text = "Thank you for choosing ES-GIFT. Your invoice is ready."
            details_title = "Invoice Details:"
            invoice_number_text = "Invoice Number:"
            date_text = "Date:"
            total_text = "Total Amount:"
            status_text = "Payment Status:"
            contact_text = "If you have any questions, please don't hesitate to contact us:"
            thanks_text = "Thank you again for trusting ES-GIFT"
        
        # إنشاء محتوى HTML
        html_content = f"""
        <!DOCTYPE html>
        <html dir="{'rtl' if has_arabic else 'ltr'}" lang="{'ar' if has_arabic else 'en'}">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                    direction: {'rtl' if has_arabic else 'ltr'};
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #E31837, #ff3366);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 32px;
                }}
                .header p {{
                    margin: 5px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px;
                    line-height: 1.6;
                }}
                .greeting {{
                    color: #2C3E50;
                    font-size: 20px;
                    margin-bottom: 20px;
                    font-weight: bold;
                }}
                .main-text {{
                    font-size: 16px;
                    color: #555;
                    margin-bottom: 25px;
                }}
                .details-box {{
                    background: #FFF8F8;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-{'right' if has_arabic else 'left'}: 4px solid #E31837;
                }}
                .details-title {{
                    color: #E31837;
                    font-weight: bold;
                    font-size: 18px;
                    margin-bottom: 15px;
                }}
                .detail-item {{
                    margin: 8px 0;
                    font-size: 14px;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #333;
                }}
                .contact-info {{
                    color: #666;
                    font-size: 14px;
                    margin-top: 25px;
                    padding: 15px;
                    background: #F8F9FA;
                    border-radius: 6px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #999;
                    font-size: 12px;
                }}
                .footer-main {{
                    background: #333;
                    color: #ccc;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎁 ES-GIFT</h1>
                    <p>{'بطاقات الهدايا الرقمية الرائدة' if has_arabic else 'Leading Digital Gift Cards & Payment Services'}</p>
                </div>
                
                <div class="content">
                    <div class="greeting">{customer_greeting}</div>
                    
                    <div class="main-text">{main_text}</div>
                    
                    <div class="details-box">
                        <div class="details-title">📋 {details_title}</div>
                        <div class="detail-item">
                            <span class="detail-label">{invoice_number_text}</span> {invoice.invoice_number}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">{date_text}</span> {invoice.invoice_date.strftime('%Y-%m-%d')}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">{total_text}</span> {float(invoice.total_amount):.2f} {invoice.currency}
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">{status_text}</span> {_get_payment_status_text(invoice.payment_status, has_arabic)}
                        </div>
                    </div>
                    
                    <div class="contact-info">
                        {contact_text}
                        <br>📧 business@es-gift.com
                        <br>📱 +966 12 345 6789
                        <br>🌐 www.es-gift.com
                    </div>
                    
                    <div class="footer">
                        {thanks_text}
                    </div>
                </div>
                
                <div class="footer-main">
                    <p>© 2025 ES-GIFT - {'جميع الحقوق محفوظة' if has_arabic else 'All Rights Reserved'}</p>
                    <p>{'تم إنشاء هذه الفاتورة تلقائياً في' if has_arabic else 'Invoice generated on'}: {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # إنشاء الرسالة
        msg = MIMEMultipart('mixed')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = f"ES-GIFT <{sender_email}>"
        msg['To'] = email_to_send
        
        # إضافة المحتوى HTML
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # محاولة إضافة مرفق PDF إذا كان متوفراً
        try:
            from flask import current_app
            # Generate PDF first
            from premium_english_invoice_service import PremiumEnglishInvoiceService
            pdf_path = PremiumEnglishInvoiceService.generate_enhanced_pdf(invoice)
            
            if pdf_path and current_app:
                pdf_full_path = os.path.join(current_app.static_folder, pdf_path)
                
                if os.path.exists(pdf_full_path):
                    with open(pdf_full_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="ES-GIFT_Invoice_{invoice.invoice_number}.pdf"'
                        )
                        msg.attach(part)
                        print(f"📎 تم إرفاق ملف PDF: {pdf_path}")
                else:
                    print("⚠️ ملف PDF غير موجود، سيتم الإرسال بدون مرفق")
            else:
                print("⚠️ لم يتم إنشاء PDF، سيتم الإرسال بدون مرفق")
        except Exception as pdf_error:
            print(f"⚠️ خطأ في إرفاق PDF: {pdf_error}")
        
        # إرسال الرسالة عبر Gmail
        print("🔄 الاتصال بـ Gmail...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("🔐 بدء التشفير...")
            server.starttls()
            
            print("🔑 تسجيل الدخول...")
            server.login(sender_email, sender_password)
            
            print("📤 إرسال الرسالة...")
            server.send_message(msg)
        
        print(f"✅ تم إرسال الفاتورة بنجاح إلى: {email_to_send}")
        return True
        
    except Exception as e:
        print(f"❌ فشل في إرسال الفاتورة: {e}")
        import traceback
        traceback.print_exc()
        return False

def _get_payment_status_text(status, is_arabic=True):
    """الحصول على نص حالة الدفع"""
    status_map_ar = {
        'pending': '⏳ في الانتظار',
        'paid': '✅ مدفوع',
        'failed': '❌ فشل',
        'cancelled': '🚫 ملغي',
        'refunded': '↩️ مسترد'
    }
    
    status_map_en = {
        'pending': '⏳ Pending',
        'paid': '✅ Paid',
        'failed': '❌ Failed',
        'cancelled': '🚫 Cancelled',
        'refunded': '↩️ Refunded'
    }
    
    if is_arabic:
        return status_map_ar.get(status, f'⚪ {status}')
    else:
        return status_map_en.get(status, f'⚪ {status}')

def test_invoice_email(test_email="hanizezo5@gmail.com"):
    """اختبار إرسال فاتورة وهمية"""
    try:
        print(f"🧪 اختبار إرسال فاتورة إلى: {test_email}")
        
        # إنشاء فاتورة وهمية
        class MockInvoice:
            def __init__(self):
                self.invoice_number = "TEST-2025-007"
                self.customer_name = "عميل تجريبي"
                self.customer_email = test_email
                self.customer_phone = "+966123456789"
                self.customer_type = "regular"
                self.invoice_date = datetime.now()
                self.due_date = None
                self.subtotal = 100.0
                self.discount_amount = 0.0
                self.tax_amount = 15.0
                self.total_amount = 115.0
                self.currency = "SAR"
                self.payment_status = "paid"
                self.payment_method = "credit_card"
                self.paid_date = datetime.now()
                self.notes = "فاتورة اختبار للنظام المحسن - جميع المشاكل تم حلها"
                self.pdf_file_path = None
        
        mock_invoice = MockInvoice()
        
        # إرسال الفاتورة
        success = send_invoice_guaranteed(mock_invoice, test_email)
        
        if success:
            print("🎉 تم الاختبار بنجاح!")
            print(f"📫 تحقق من صندوق الوارد في: {test_email}")
        else:
            print("❌ فشل الاختبار")
        
        return success
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        return False

if __name__ == "__main__":
    # تشغيل اختبار مباشر
    test_invoice_email()
