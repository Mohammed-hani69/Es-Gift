#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إنشاء فواتير حديثة وجذابة مع إرسال البريد الإلكتروني
"""

import os
import io
from datetime import datetime, timedelta
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF

from flask import current_app, url_for
from send_by_hostinger import send_custom_email, send_email

from models import db, Invoice, Order, User
from utils import send_email as utils_send_email


class ModernInvoiceService:
    """خدمة إنشاء فواتير حديثة وجذابة"""
    
    @staticmethod
    def create_invoice(order):
        """إنشاء فاتورة جديدة للطلب"""
        try:
            # التحقق من عدم وجود فاتورة سابقة للطلب
            existing_invoice = Invoice.query.filter_by(order_id=order.id).first()
            if existing_invoice:
                return existing_invoice
            
            # إنشاء رقم فاتورة فريد مع تصميم جذاب
            invoice_number = f"ESGIFT-{datetime.now().strftime('%Y%m%d')}-{order.id:06d}"
            
            # حساب المبالغ
            subtotal = order.total_amount
            tax_amount = Decimal('0.00')  # يمكن تطبيق ضريبة لاحقاً
            discount_amount = Decimal('0.00')  # يمكن تطبيق خصم لاحقاً
            total_amount = subtotal + tax_amount - discount_amount
            
            # إنشاء الفاتورة
            invoice = Invoice(
                invoice_number=invoice_number,
                order_id=order.id,
                user_id=order.user_id,
                subtotal=subtotal,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                currency=order.currency or 'SAR',
                payment_method=order.payment_method,
                payment_status=order.status if order.status in ['completed', 'pending', 'failed'] else 'pending',
                paid_amount=total_amount if order.status == 'completed' else Decimal('0.00'),
                customer_name=order.user.full_name or order.user.username,
                customer_email=order.user.email,
                customer_phone=order.user.phone,
                customer_type=order.user.customer_type,
                invoice_date=datetime.now(),
                due_date=datetime.now() + timedelta(days=30),
                paid_date=datetime.now() if order.status == 'completed' else None,
                notes=f"فاتورة للطلب #{order.order_number} - {order.product.name}"
            )
            
            db.session.add(invoice)
            db.session.commit()
            
            # إنشاء ملف PDF للفاتورة
            pdf_path = ModernInvoiceService.generate_modern_pdf(invoice)
            if pdf_path:
                invoice.pdf_file_path = pdf_path
                db.session.commit()
            
            return invoice
            
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في إنشاء الفاتورة: {e}")
            return None
    
    @staticmethod
    def generate_modern_pdf(invoice):
        """إنشاء ملف PDF عصري وجذاب للفاتورة"""
        try:
            # إنشاء مجلد الفواتير إذا لم يكن موجوداً
            invoice_dir = os.path.join(current_app.static_folder, 'invoices')
            os.makedirs(invoice_dir, exist_ok=True)
            
            # مسار ملف PDF
            filename = f"invoice_{invoice.invoice_number}.pdf"
            pdf_path = os.path.join(invoice_dir, filename)
            
            # إنشاء الـ PDF بتصميم عصري
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=25*mm,
                leftMargin=25*mm,
                topMargin=25*mm,
                bottomMargin=25*mm
            )
            
            # قائمة العناصر للصفحة
            story = []
            
            # الألوان العصرية والجذابة لـ ES-GIFT
            primary_color = colors.HexColor('#FF0033')    # أحمر ES-Gift المميز
            secondary_color = colors.HexColor('#2C3E50')  # رمادي أنيق
            light_gray = colors.HexColor('#F8F9FA')       # رمادي فاتح
            accent_color = colors.HexColor('#E74C3C')     # أحمر داكن للتفاصيل
            success_color = colors.HexColor('#27AE60')    # أخضر للحالة المدفوعة
            gold_color = colors.HexColor('#F39C12')       # ذهبي للعناصر المميزة
            
            # الأنماط
            styles = getSampleStyleSheet()
            
            # شعار وعنوان الشركة بتصميم متطور
            company_style = ParagraphStyle(
                'ModernCompany',
                parent=styles['Heading1'],
                fontSize=40,
                spaceAfter=8,
                textColor=primary_color,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            # شعار فرعي أنيق
            tagline_style = ParagraphStyle(
                'Tagline',
                parent=styles['Normal'],
                fontSize=14,
                textColor=secondary_color,
                alignment=TA_CENTER,
                spaceAfter=6,
                fontName='Helvetica-Oblique'
            )
            
            # معلومات التواصل
            contact_style = ParagraphStyle(
                'Contact',
                parent=styles['Normal'],
                fontSize=10,
                textColor=secondary_color,
                alignment=TA_CENTER,
                spaceAfter=25
            )
            
            # إضافة شعار وعنوان بتصميم جذاب ✨
            story.append(Paragraph("🎁 ES-GIFT 🎁", company_style))
            story.append(Paragraph("الشركة الرائدة في بطاقات الهدايا الرقمية", tagline_style))
            story.append(Paragraph("📧 business@es-gift.com | 📱 +966123456789 | 🌐 www.es-gift.com", contact_style))
            
            # خط فاصل أنيق مع تدرج
            line_drawing = Drawing(500, 8)
            line_drawing.add(Line(0, 5, 500, 5, strokeColor=primary_color, strokeWidth=4))
            line_drawing.add(Line(0, 2, 500, 2, strokeColor=gold_color, strokeWidth=2))
            story.append(line_drawing)
            story.append(Spacer(1, 30))
            
            # هيدر الفاتورة مع تصميم جذاب
            invoice_header_data = [
                ['INVOICE فاتورة', ''],
                [f'رقم الفاتورة: {invoice.invoice_number}', ''],
                [f'تاريخ الإصدار: {invoice.invoice_date.strftime("%Y-%m-%d")}', ''],
                [f'تاريخ الاستحقاق: {invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "غير محدد"}', '']
            ]
            
            invoice_header_table = Table(invoice_header_data, colWidths=[4*inch, 1.5*inch])
            invoice_header_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 24),
                ('FONTSIZE', (0, 1), (-1, -1), 13),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), secondary_color),
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('SPAN', (0, 0), (1, 0)),
            ]))
            
            story.append(invoice_header_table)
            story.append(Spacer(1, 30))
            
            # معلومات العميل والشركة في تصميم حديث
            client_info_data = [
                ['معلومات العميل', 'معلومات الشركة'],
                [
                    f"👤 {invoice.customer_name or 'غير محدد'}\n"
                    f"📧 {invoice.customer_email}\n"
                    f"📱 {invoice.customer_phone or 'غير محدد'}\n"
                    f"🏷️ نوع العميل: {ModernInvoiceService._get_customer_type_arabic(invoice.customer_type)}",
                    
                    "🏢 ES-GIFT\n"
                    "🌍 المملكة العربية السعودية\n"
                    "📧 business@es-gift.com\n"
                    "📱 +966123456789"
                ]
            ]
            
            client_table = Table(client_info_data, colWidths=[3*inch, 3*inch])
            client_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTSIZE', (0, 1), (-1, 1), 11),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
                ('TEXTCOLOR', (0, 1), (-1, 1), secondary_color),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1.5, colors.lightgrey),
                ('BACKGROUND', (0, 1), (-1, 1), light_gray),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            story.append(client_table)
            story.append(Spacer(1, 35))
            
            # عنوان تفاصيل المنتجات
            products_title_style = ParagraphStyle(
                'ProductsTitle',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=primary_color,
                alignment=TA_RIGHT,
                spaceAfter=15,
                fontName='Helvetica-Bold'
            )
            
            story.append(Paragraph("🛍️ تفاصيل المنتجات", products_title_style))
            
            # جدول المنتجات بتصميم متطور
            order = invoice.order
            product_data = [
                ['#', 'المنتج والوصف', 'الكمية', 'السعر', 'المجموع']
            ]
            
            # إضافة تفاصيل المنتج
            unit_price = float(order.total_amount) / order.quantity if order.quantity > 0 else float(order.total_amount)
            product_description = f"{order.product.name}\n🌍 {order.product.region} - 💳 {order.product.value}"
            
            product_data.append([
                '1',
                product_description,
                str(order.quantity),
                f"{unit_price:.2f} {invoice.currency}",
                f"{float(order.total_amount):.2f} {invoice.currency}"
            ])
            
            products_table = Table(product_data, colWidths=[0.6*inch, 3*inch, 0.8*inch, 1.2*inch, 1.2*inch])
            products_table.setStyle(TableStyle([
                # رأس الجدول
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                
                # محتوى الجدول
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TEXTCOLOR', (0, 1), (-1, -1), secondary_color),
                ('BACKGROUND', (0, 1), (-1, -1), light_gray),
                
                # التخطيط والمحاذاة
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # العمود الأول
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # عمود الوصف
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'), # باقي الأعمدة
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.gray),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            story.append(products_table)
            story.append(Spacer(1, 30))
            
            # جدول الإجماليات بتصميم أنيق
            totals_data = [
                ['المجموع الفرعي:', f"{float(invoice.subtotal):.2f} {invoice.currency}"],
                ['الخصم (-)', f"{float(invoice.discount_amount):.2f} {invoice.currency}"],
                ['الضريبة (+)', f"{float(invoice.tax_amount):.2f} {invoice.currency}"],
                ['الإجمالي النهائي', f"{float(invoice.total_amount):.2f} {invoice.currency}"]
            ]
            
            totals_table = Table(totals_data, colWidths=[2.5*inch, 1.8*inch])
            totals_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -2), 12),
                ('FONTSIZE', (0, -1), (-1, -1), 16),
                ('TEXTCOLOR', (0, 0), (-1, -2), secondary_color),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('BACKGROUND', (0, -1), (-1, -1), primary_color),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.gray),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -2), light_gray),
            ]))
            
            # محاذاة الجدول لليسار
            totals_table.hAlign = 'LEFT'
            story.append(totals_table)
            story.append(Spacer(1, 35))
            
            # حالة الدفع مع تصميم بصري
            payment_status_text, payment_color, payment_emoji = ModernInvoiceService._get_payment_status_info(invoice.payment_status)
            
            payment_style = ParagraphStyle(
                'PaymentStatus',
                parent=styles['Normal'],
                fontSize=18,
                textColor=payment_color,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                spaceAfter=20
            )
            
            story.append(Paragraph(f"{payment_emoji} حالة الدفع: {payment_status_text}", payment_style))
            
            # صندوق الملاحظات
            if invoice.notes:
                notes_style = ParagraphStyle(
                    'Notes',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=secondary_color,
                    alignment=TA_RIGHT,
                    spaceAfter=25,
                    leftIndent=20,
                    rightIndent=20
                )
                story.append(Paragraph(f"📝 ملاحظات: {invoice.notes}", notes_style))
            
            # Footer مع تصميم جذاب
            story.append(Spacer(1, 40))
            
            # خط فاصل للـ footer
            footer_line = Drawing(500, 2)
            footer_line.add(Line(0, 1, 500, 1, strokeColor=accent_color, strokeWidth=2))
            story.append(footer_line)
            story.append(Spacer(1, 15))
            
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.gray,
                alignment=TA_CENTER,
                spaceAfter=8
            )
            
            story.append(Paragraph("🙏 شكراً لاختياركم ES-GIFT - شريككم الموثوق في عالم الهدايا الرقمية", footer_style))
            story.append(Paragraph("هذه الفاتورة تم إنشاؤها إلكترونياً ولا تحتاج إلى توقيع", footer_style))
            story.append(Paragraph(f"تم الإنشاء في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            
            # بناء المستند
            doc.build(story)
            
            return f"invoices/{filename}"
            
        except Exception as e:
            print(f"خطأ في إنشاء ملف PDF: {e}")
            return None
    
    @staticmethod
    def send_invoice_email(invoice):
        """إرسال الفاتورة عبر البريد الإلكتروني مع تصميم جذاب"""
        try:
            # التأكد من وجود ملف PDF
            if not invoice.pdf_file_path:
                pdf_path = ModernInvoiceService.generate_modern_pdf(invoice)
                if pdf_path:
                    invoice.pdf_file_path = pdf_path
                    db.session.commit()
                else:
                    return False
            
            # مسار ملف PDF
            pdf_full_path = os.path.join(current_app.static_folder, invoice.pdf_file_path)
            
            if not os.path.exists(pdf_full_path):
                print(f"ملف PDF غير موجود: {pdf_full_path}")
                return False
            
            # إنشاء محتوى البريد الإلكتروني
            order = invoice.order
            customer_name = invoice.customer_name or "عزيزي العميل"
            
            email_html = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>🎁 فاتورة ES-GIFT</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        direction: rtl;
                        text-align: right;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 20px;
                        box-shadow: 0 30px 60px rgba(0,0,0,0.15);
                        overflow: hidden;
                        position: relative;
                    }}
                    .container::before {{
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 4px;
                        background: linear-gradient(90deg, #ff0033, #ff6666, #ff0033);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #ff0033, #cc0029);
                        color: white;
                        text-align: center;
                        padding: 50px 20px;
                        position: relative;
                    }}
                    .header::after {{
                        content: '';
                        position: absolute;
                        bottom: -10px;
                        left: 50%;
                        transform: translateX(-50%);
                        width: 0;
                        height: 0;
                        border-left: 20px solid transparent;
                        border-right: 20px solid transparent;
                        border-top: 20px solid #cc0029;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 32px;
                        font-weight: bold;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }}
                    .header p {{
                        margin: 15px 0 0 0;
                        font-size: 18px;
                        opacity: 0.95;
                        font-weight: 300;
                    }}
                    .content {{
                        padding: 50px 40px;
                    }}
                    .greeting {{
                        font-size: 24px;
                        color: #333;
                        margin-bottom: 20px;
                        font-weight: 600;
                    }}
                    .welcome-message {{
                        font-size: 16px;
                        color: #666;
                        margin-bottom: 30px;
                        line-height: 1.6;
                    }}
                    .invoice-info {{
                        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                        border-radius: 15px;
                        padding: 30px;
                        margin: 25px 0;
                        border-right: 5px solid #ff0033;
                        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
                    }}
                    .invoice-info h3 {{
                        color: #ff0033;
                        margin: 0 0 20px 0;
                        font-size: 22px;
                        font-weight: bold;
                    }}
                    .info-row {{
                        display: flex;
                        justify-content: space-between;
                        margin: 15px 0;
                        padding: 12px 0;
                        border-bottom: 1px solid #eee;
                        transition: all 0.3s ease;
                    }}
                    .info-row:hover {{
                        background: rgba(255, 0, 51, 0.05);
                        border-radius: 8px;
                        padding: 12px 15px;
                    }}
                    .info-row:last-child {{
                        border-bottom: none;
                    }}
                    .label {{
                        font-weight: bold;
                        color: #333;
                        font-size: 16px;
                    }}
                    .value {{
                        color: #666;
                        font-size: 16px;
                    }}
                    .total-amount {{
                        background: linear-gradient(135deg, #ff0033, #cc0029);
                        color: white;
                        padding: 25px;
                        border-radius: 15px;
                        text-align: center;
                        margin: 30px 0;
                        box-shadow: 0 15px 30px rgba(255, 0, 51, 0.3);
                    }}
                    .total-amount h2 {{
                        margin: 0;
                        font-size: 28px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }}
                    .download-section {{
                        text-align: center;
                        margin: 35px 0;
                    }}
                    .download-note {{
                        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                        border: 2px solid #2196f3;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 25px 0;
                        color: #1976d2;
                        box-shadow: 0 8px 16px rgba(33, 150, 243, 0.2);
                    }}
                    .tips-section {{
                        background: linear-gradient(135deg, #e8f5e8, #c8e6c9);
                        border: 2px solid #4caf50;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 25px 0;
                        color: #2e7d32;
                    }}
                    .footer {{
                        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                        padding: 40px;
                        text-align: center;
                        color: #666;
                        border-top: 3px solid #ff0033;
                    }}
                    .social-links {{
                        margin: 25px 0;
                    }}
                    .social-links a {{
                        color: #ff0033;
                        text-decoration: none;
                        margin: 0 15px;
                        font-weight: bold;
                        font-size: 16px;
                        transition: all 0.3s ease;
                    }}
                    .social-links a:hover {{
                        color: #cc0029;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                    }}
                    .emoji {{
                        font-size: 1.4em;
                    }}
                    .pulse {{
                        animation: pulse 2s infinite;
                    }}
                    @keyframes pulse {{
                        0% {{ transform: scale(1); }}
                        50% {{ transform: scale(1.05); }}
                        100% {{ transform: scale(1); }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 class="pulse">🎁 ES-GIFT</h1>
                        <p>شريككم الموثوق في عالم الهدايا الرقمية</p>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">مرحباً {customer_name}، 👋</div>
                        <div class="welcome-message">
                            نشكركم لاختياركم ES-GIFT! 🌟 تجدون في المرفقات فاتورة طلبكم الأخير مع جميع التفاصيل المطلوبة.
                        </div>
                        
                        <div class="invoice-info">
                            <h3>📋 تفاصيل الفاتورة</h3>
                            <div class="info-row">
                                <span class="label">🔢 رقم الفاتورة:</span>
                                <span class="value">{invoice.invoice_number}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">🛒 رقم الطلب:</span>
                                <span class="value">{order.order_number}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">🎮 المنتج:</span>
                                <span class="value">{order.product.name}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">🌍 المنطقة والقيمة:</span>
                                <span class="value">{order.product.region} - {order.product.value}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">🔢 الكمية:</span>
                                <span class="value">{order.quantity}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">📅 تاريخ الطلب:</span>
                                <span class="value">{order.created_at.strftime('%Y-%m-%d %H:%M')}</span>
                            </div>
                        </div>
                        
                        <div class="total-amount">
                            <h2>💰 المبلغ الإجمالي: {float(invoice.total_amount):.2f} {invoice.currency}</h2>
                        </div>
                        
                        <div class="download-note">
                            <span class="emoji">📎</span>
                            <strong>ملف الفاتورة مرفق:</strong> يمكنكم تحميل وطباعة الفاتورة من المرفقات أعلاه.
                        </div>
                        
                        <div class="tips-section">
                            <span class="emoji">✅</span>
                            <strong>نصائح مهمة:</strong>
                            <ul style="margin: 15px 0; padding-right: 25px;">
                                <li>احتفظوا بنسخة من هذه الفاتورة لسجلاتكم 📄</li>
                                <li>في حالة أي استفسار، تواصلوا معنا فوراً 📞</li>
                                <li>أكواد المنتجات سيتم إرسالها في بريد منفصل 🎁</li>
                                <li>تأكدوا من حفظ الملف في مكان آمن 🔒</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p><strong>🙏 شكراً لثقتكم بـ ES-GIFT</strong></p>
                        <div class="social-links">
                            <a href="mailto:business@es-gift.com">📧 business@es-gift.com</a>
                            <a href="tel:+966123456789">📱 +966123456789</a>
                        </div>
                        <p style="font-size: 14px; color: #999; margin-top: 25px;">
                            🤖 هذا البريد تم إرساله تلقائياً من نظام ES-GIFT. لا تترددوا في التواصل معنا لأي استفسار.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # إرسال البريد الإلكتروني مع المرفق باستخدام Brevo
            try:
                import base64
                
                # قراءة ملف PDF وتحويله إلى base64
                with open(pdf_full_path, 'rb') as fp:
                    pdf_content = base64.b64encode(fp.read()).decode('utf-8')
                
                # تحضير بيانات الفاتورة
                invoice_data = {
                    'invoice_number': invoice.invoice_number,
                    'total_amount': float(invoice.total_amount),
                    'currency': invoice.currency,
                    'customer_name': invoice.customer_name,
                    'invoice_date': invoice.invoice_date.strftime('%Y/%m/%d') if invoice.invoice_date else 'غير محدد'
                }
                
                # إرسال الفاتورة باستخدام Hostinger SMTP
                invoice_subject = f"فاتورة رقم {invoice.invoice_number} - {invoice.customer_name}"
                success, message = send_custom_email(
                    email=invoice.customer_email,
                    subject=invoice_subject,
                    message_content=email_html,
                    message_title="فاتورة ES-GIFT"
                )
                
                if success:
                    print(f"تم إرسال الفاتورة بنجاح إلى: {invoice.customer_email} باستخدام Email Sender Pro")
                    return True
                else:
                    print(f"فشل إرسال الفاتورة باستخدام Email Sender Pro: {message}")
                    # استخدام الطريقة البديلة
                    return _send_invoice_email_fallback(invoice, email_html, pdf_full_path)
                
            except Exception as e:
                print(f"خطأ في إرسال البريد الإلكتروني باستخدام Email Sender Pro: {e}")
                # استخدام الطريقة البديلة
                return _send_invoice_email_fallback(invoice, email_html, pdf_full_path)
            
        except Exception as e:
            print(f"خطأ في إرسال فاتورة البريد الإلكتروني: {e}")
            return False
    
    @staticmethod
    def _get_customer_type_arabic(customer_type):
        """تحويل نوع العميل إلى العربية"""
        types = {
            'regular': 'عميل عادي',
            'kyc': 'عميل موثق',
            'reseller': 'موزع'
        }
        return types.get(customer_type, 'غير محدد')
    
    @staticmethod
    def _get_payment_status_info(payment_status):
        """الحصول على معلومات حالة الدفع"""
        if payment_status == 'completed':
            return 'مدفوعة ✅', colors.green, '✅'
        elif payment_status == 'pending':
            return 'معلقة ⏳', colors.orange, '⏳'
        else:
            return 'فاشلة ❌', colors.red, '❌'


def _send_invoice_email_fallback(invoice, email_html, pdf_full_path):
    """إرسال الفاتورة باستخدام Flask-Mail كبديل"""
    try:
        from flask_mail import Message, Mail
        
        mail = current_app.extensions.get('mail')
        if not mail:
            print("خدمة البريد الإلكتروني غير مكونة")
            return False
        
        msg = Message(
            subject=f"🎁 فاتورة ES-GIFT - {invoice.invoice_number}",
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
    else:
        return 'فاشلة ❌', colors.red, '❌'


# إنشاء alias للتوافق مع الكود الحالي
InvoiceService = ModernInvoiceService
