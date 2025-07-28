#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمات إنشاء الفواتير وملفات Excel
"""

import os
import io
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from flask import current_app, url_for
from flask_mail import Message

from models import db, Invoice, Order, User
from utils import convert_currency, send_email

# تسجيل خط آمن للنص العربي
def register_safe_fonts():
    """تسجيل خطوط آمنة للاستخدام مع النص العربي"""
    try:
        # محاولة تسجيل خط Arial إذا كان متوفراً
        from reportlab.pdfbase.pdfmetrics import registerFont
        from reportlab.pdfbase.ttfonts import TTFont
        
        # البحث عن خط Arial في النظام
        possible_arial_paths = [
            # Windows
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/Arial.ttf',
            # معاً أخرى محتملة
            '/System/Library/Fonts/Arial.ttf',
            '/usr/share/fonts/truetype/dejavu/arial.ttf'
        ]
        
        arial_found = False
        for path in possible_arial_paths:
            if os.path.exists(path):
                try:
                    registerFont(TTFont('Arial', path))
                    arial_found = True
                    print(f"✅ تم تسجيل خط Arial من: {path}")
                    break
                except Exception as e:
                    print(f"❌ فشل تسجيل Arial من {path}: {e}")
                    continue
        
        if not arial_found:
            print("⚠️ لم يتم العثور على خط Arial، سيتم استخدام Helvetica")
            return 'Helvetica'
        
        return 'Arial'
        
    except Exception as e:
        print(f"❌ خطأ في تسجيل الخطوط: {e}")
        return 'Helvetica'

# تسجيل الخطوط عند تحميل الوحدة
SAFE_FONT = register_safe_fonts()


class InvoiceService:
    """خدمة إنشاء وإدارة الفواتير"""
    
    @staticmethod
    def create_invoice(order):
        """إنشاء فاتورة جديدة للطلب"""
        try:
            # التحقق من عدم وجود فاتورة سابقة للطلب
            existing_invoice = Invoice.query.filter_by(order_id=order.id).first()
            if existing_invoice:
                return existing_invoice
            
            # إنشاء رقم فاتورة فريد
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{order.id:06d}"
            
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
                currency=order.currency,
                payment_method=order.payment_method,
                payment_status=order.payment_status,
                paid_amount=total_amount if order.payment_status == 'completed' else Decimal('0.00'),
                customer_name=order.user.full_name or order.user.email,
                customer_email=order.user.email,
                customer_phone=order.user.phone,
                customer_type=order.user.customer_type,
                invoice_date=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=30),
                paid_date=datetime.utcnow() if order.payment_status == 'completed' else None
            )
            
            db.session.add(invoice)
            db.session.commit()
            
            # إنشاء ملف PDF للفاتورة
            pdf_path = InvoiceService.generate_invoice_pdf(invoice)
            if pdf_path:
                invoice.pdf_file_path = pdf_path
                db.session.commit()
            
            return invoice
            
        except Exception as e:
            print(f"خطأ في إنشاء الفاتورة: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def generate_invoice_pdf(invoice):
        """إنشاء ملف PDF للفاتورة"""
        try:
            # إنشاء مجلد الفواتير إذا لم يكن موجوداً
            invoices_dir = os.path.join(current_app.root_path, 'static', 'invoices')
            os.makedirs(invoices_dir, exist_ok=True)
            
            # مسار ملف الفاتورة
            filename = f"invoice_{invoice.invoice_number}.pdf"
            filepath = os.path.join(invoices_dir, filename)
            
            # إنشاء الـ PDF
            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=0.75*inch, leftMargin=0.75*inch,
                                   topMargin=1*inch, bottomMargin=1*inch)
            
            # تحضير المحتوى
            story = []
            styles = getSampleStyleSheet()
            
            # إضافة ستايل عربي
            arabic_style = ParagraphStyle(
                'Arabic',
                parent=styles['Normal'],
                fontName=SAFE_FONT,
                fontSize=12,
                alignment=TA_RIGHT,
                spaceBefore=6,
                spaceAfter=6
            )
            
            title_style = ParagraphStyle(
                'ArabicTitle',
                parent=styles['Heading1'],
                fontName=SAFE_FONT,
                fontSize=18,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#ff0033'),
                spaceBefore=12,
                spaceAfter=12
            )
            
            # عنوان الفاتورة
            story.append(Paragraph("فاتورة إلكترونية", title_style))
            story.append(Paragraph(f"Es-Gift - {current_app.config.get('SITE_NAME', 'Es-Gift')}", arabic_style))
            story.append(Spacer(1, 0.2*inch))
            
            # معلومات الفاتورة
            invoice_data = [
                ['رقم الفاتورة:', invoice.invoice_number],
                ['تاريخ الفاتورة:', invoice.invoice_date.strftime('%Y-%m-%d')],
                ['رقم الطلب:', invoice.order.order_number],
                ['حالة الدفع:', 'مدفوعة' if invoice.payment_status == 'completed' else 'معلقة'],
            ]
            
            invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
            invoice_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), SAFE_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            
            story.append(invoice_table)
            story.append(Spacer(1, 0.3*inch))
            
            # معلومات العميل
            story.append(Paragraph("معلومات العميل", arabic_style))
            customer_data = [
                ['الاسم:', invoice.customer_name or 'غير محدد'],
                ['البريد الإلكتروني:', invoice.customer_email],
                ['نوع العميل:', 'عميل عادي' if invoice.customer_type == 'regular' else 
                                'عميل موثق' if invoice.customer_type == 'kyc' else 'موزع'],
            ]
            
            if invoice.customer_phone:
                customer_data.append(['الهاتف:', invoice.customer_phone])
            
            customer_table = Table(customer_data, colWidths=[2*inch, 3*inch])
            customer_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            
            story.append(customer_table)
            story.append(Spacer(1, 0.3*inch))
            
            # تفاصيل المنتجات
            story.append(Paragraph("تفاصيل المنتجات", arabic_style))
            
            # رأس جدول المنتجات
            products_data = [['المنتج', 'الكمية', 'السعر الوحدة', 'الإجمالي']]
            
            # إضافة منتجات الطلب
            for item in invoice.order.items:
                products_data.append([
                    item.product.name,
                    str(item.quantity),
                    f"{item.price} {invoice.currency}",
                    f"{item.price * item.quantity} {invoice.currency}"
                ])
            
            # إضافة صف الإجمالي
            products_data.append(['', '', 'المجموع الفرعي:', f"{invoice.subtotal} {invoice.currency}"])
            if invoice.tax_amount > 0:
                products_data.append(['', '', 'الضرائب:', f"{invoice.tax_amount} {invoice.currency}"])
            if invoice.discount_amount > 0:
                products_data.append(['', '', 'الخصم:', f"-{invoice.discount_amount} {invoice.currency}"])
            products_data.append(['', '', 'المجموع الكلي:', f"{invoice.total_amount} {invoice.currency}"])
            
            products_table = Table(products_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
            products_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'RIGHT'),  # محاذاة أسماء المنتجات لليمين
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # رأس الجدول
                ('BACKGROUND', (0, -3), (-1, -1), colors.lightblue),  # صفوف الإجمالي
                ('FONTSIZE', (0, -1), (-1, -1), 12),  # حجم خط أكبر للإجمالي النهائي
                ('FONTNAME', (0, -1), (-1, -1), 'Arial'),
            ]))
            
            story.append(products_table)
            story.append(Spacer(1, 0.3*inch))
            
            # ملاحظات
            if invoice.notes:
                story.append(Paragraph("ملاحظات", arabic_style))
                story.append(Paragraph(invoice.notes, arabic_style))
                story.append(Spacer(1, 0.2*inch))
            
            # تذييل الفاتورة
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph("شكراً لك على الشراء من Es-Gift", arabic_style))
            story.append(Paragraph("لأي استفسارات، يرجى التواصل معنا", arabic_style))
            
            # بناء الـ PDF
            doc.build(story)
            
            return os.path.join('static', 'invoices', filename)
            
        except Exception as e:
            print(f"خطأ في إنشاء ملف PDF للفاتورة: {e}")
            return None


class ExcelReportService:
    """خدمة إنشاء تقارير Excel"""
    
    @staticmethod
    def create_order_excel(order, codes_data):
        """إنشاء ملف Excel يحتوي على تفاصيل الطلب والأكواد"""
        try:
            # إنشاء مجلد التقارير إذا لم يكن موجوداً
            reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # اسم الملف
            filename = f"order_{order.order_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(reports_dir, filename)
            
            # إنشاء ExcelWriter
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # ورقة معلومات الطلب
                order_info = {
                    'البيان': [
                        'رقم الطلب',
                        'اسم العميل',
                        'البريد الإلكتروني',
                        'نوع العميل',
                        'تاريخ الطلب',
                        'المبلغ الإجمالي',
                        'العملة',
                        'طريقة الدفع',
                        'حالة الدفع',
                        'حالة الطلب'
                    ],
                    'القيمة': [
                        order.order_number,
                        order.user.full_name or order.user.email,
                        order.user.email,
                        'عميل عادي' if order.user.customer_type == 'regular' else 
                        'عميل موثق' if order.user.customer_type == 'kyc' else 'موزع',
                        order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        str(order.total_amount),
                        order.currency,
                        order.payment_method or 'غير محدد',
                        'مكتمل' if order.payment_status == 'completed' else 'معلق',
                        'مكتمل' if order.order_status == 'completed' else 'معلق'
                    ]
                }
                
                order_df = pd.DataFrame(order_info)
                order_df.to_excel(writer, sheet_name='معلومات الطلب', index=False)
                
                # ورقة تفاصيل المنتجات
                products_data = []
                for item in order.items:
                    products_data.append({
                        'اسم المنتج': item.product.name,
                        'الوصف': item.product.description or '',
                        'الكمية': item.quantity,
                        'السعر الوحدة': float(item.price),
                        'الإجمالي': float(item.price * item.quantity),
                        'العملة': item.currency
                    })
                
                products_df = pd.DataFrame(products_data)
                products_df.to_excel(writer, sheet_name='تفاصيل المنتجات', index=False)
                
                # ورقة الأكواد المشتراة
                if codes_data:
                    codes_df = pd.DataFrame(codes_data)
                    # إعادة ترتيب الأعمدة
                    column_order = ['اسم المنتج', 'الكود', 'الرقم التسلسلي', 'التعليمات', 'السعر', 'العملة']
                    codes_df = codes_df.reindex(columns=column_order)
                    codes_df.to_excel(writer, sheet_name='الأكواد المشتراة', index=False)
                
                # تنسيق الملف
                workbook = writer.book
                
                # تنسيق ورقة معلومات الطلب
                order_sheet = writer.sheets['معلومات الطلب']
                order_sheet.column_dimensions['A'].width = 20
                order_sheet.column_dimensions['B'].width = 30
                
                # تنسيق ورقة المنتجات
                products_sheet = writer.sheets['تفاصيل المنتجات']
                for column in products_sheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    products_sheet.column_dimensions[column_letter].width = adjusted_width
                
                # تنسيق ورقة الأكواد
                if codes_data:
                    codes_sheet = writer.sheets['الأكواد المشتراة']
                    for column in codes_sheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        codes_sheet.column_dimensions[column_letter].width = adjusted_width
            
            return os.path.join('static', 'reports', filename)
            
        except Exception as e:
            print(f"خطأ في إنشاء ملف Excel: {e}")
            return None
    
    @staticmethod
    def send_order_email_with_excel(order, codes_data, excel_path):
        """إرسال بريد إلكتروني مع ملف Excel"""
        try:
            # إنشاء موضوع البريد
            subject = f"تفاصيل طلبك #{order.order_number} - Es-Gift"
            
            # إنشاء محتوى البريد
            email_body = f"""
            <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
                <div style="background: linear-gradient(135deg, #ff0033, #ff3366); color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
                    <h1 style="margin: 0; font-size: 2rem;">Es-Gift</h1>
                    <p style="margin: 10px 0 0 0; font-size: 1.1rem;">متجر البطاقات الرقمية</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                    <h2 style="color: #ff0033; margin-top: 0;">عزيزي العميل،</h2>
                    <p style="font-size: 1.1rem; line-height: 1.6;">
                        نشكرك على ثقتك في Es-Gift. تم إتمام طلبك بنجاح وإليك تفاصيل مشترياتك.
                    </p>
                </div>
                
                <div style="background: white; padding: 25px; border-radius: 10px; border-left: 4px solid #ff0033; margin-bottom: 25px;">
                    <h3 style="color: #333; margin-top: 0;">معلومات الطلب:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">رقم الطلب:</td>
                            <td style="padding: 8px 0; color: #333;">{order.order_number}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">تاريخ الطلب:</td>
                            <td style="padding: 8px 0; color: #333;">{order.created_at.strftime('%Y-%m-%d %H:%M')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">المبلغ الإجمالي:</td>
                            <td style="padding: 8px 0; color: #ff0033; font-weight: bold;">{order.total_amount} {order.currency}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">طريقة الدفع:</td>
                            <td style="padding: 8px 0; color: #333;">{order.payment_method or 'غير محدد'}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: white; padding: 25px; border-radius: 10px; border-left: 4px solid #28a745; margin-bottom: 25px;">
                    <h3 style="color: #333; margin-top: 0;">المنتجات المشتراة:</h3>
                    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">المنتج</th>
                                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">الكمية</th>
                                <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">السعر</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for item in order.items:
                email_body += f"""
                            <tr>
                                <td style="padding: 12px; border: 1px solid #ddd;">{item.product.name}</td>
                                <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">{item.quantity}</td>
                                <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">{item.price * item.quantity} {order.currency}</td>
                            </tr>
                """
            
            email_body += f"""
                        </tbody>
                    </table>
                </div>
                
                <div style="background: #fff3cd; padding: 20px; border-radius: 10px; border-left: 4px solid #ffc107; margin-bottom: 25px;">
                    <h3 style="color: #856404; margin-top: 0;">
                        <i style="color: #ffc107;">📎</i> مرفق مع هذا البريد:
                    </h3>
                    <p style="color: #856404; margin: 0;">
                        ملف Excel يحتوي على جميع تفاصيل طلبك والأكواد المشتراة
                    </p>
                </div>
                
                <div style="background: #d1ecf1; padding: 20px; border-radius: 10px; border-left: 4px solid #bee5eb; margin-bottom: 25px;">
                    <h3 style="color: #0c5460; margin-top: 0;">تعليمات الاستخدام:</h3>
                    <ul style="color: #0c5460; margin: 0; padding-right: 20px;">
                        <li>يمكنك العثور على جميع الأكواد في ملف Excel المرفق</li>
                        <li>تأكد من حفظ الملف في مكان آمن</li>
                        <li>اتبع التعليمات المرفقة مع كل كود لاستخدامه بشكل صحيح</li>
                        <li>في حالة وجود أي مشكلة، لا تتردد في التواصل معنا</li>
                    </ul>
                </div>
                
                <div style="text-align: center; padding: 25px; background: #f8f9fa; border-radius: 10px;">
                    <p style="color: #666; margin: 0 0 15px 0;">شكراً لاختيارك Es-Gift</p>
                    <p style="color: #666; margin: 0; font-size: 0.9rem;">
                        متجر البطاقات الرقمية الأول في المملكة العربية السعودية
                    </p>
                </div>
            </div>
            """
            
            # إرسال البريد مع المرفق
            return send_email_with_attachment(
                to_email=order.user.email,
                subject=subject,
                body=email_body,
                attachment_path=excel_path,
                attachment_name=f"order_{order.order_number}.xlsx"
            )
            
        except Exception as e:
            print(f"خطأ في إرسال البريد الإلكتروني: {e}")
            return False


def send_email_with_attachment(to_email, subject, body, attachment_path, attachment_name):
    """إرسال بريد إلكتروني مع مرفق"""
    try:
        from flask_mail import Mail, Message
        from flask import current_app
        
        mail = current_app.extensions.get('mail')
        if not mail:
            print("خدمة البريد الإلكتروني غير مكونة")
            return False
        
        msg = Message(
            subject=subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[to_email]
        )
        msg.html = body
        
        # إضافة المرفق
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as fp:
                msg.attach(
                    attachment_name, 
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    fp.read()
                )
        
        mail.send(msg)
        print(f"تم إرسال البريد بنجاح إلى: {to_email}")
        return True
        
    except Exception as e:
        print(f"خطأ في إرسال البريد الإلكتروني: {e}")
        return False
