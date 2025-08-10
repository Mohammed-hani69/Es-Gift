"""
خدمة إنشاء فواتير طلبات الإيداع PDF
تستخدم نفس تصميم فواتير الموقع الأساسية مع تخصيص لطلبات الإيداع
"""

import os
from datetime import datetime
from decimal import Decimal
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Line

class DepositInvoiceService:
    """خدمة إنشاء فواتير طلبات الإيداع PDF"""
    
    @staticmethod
    def generate_deposit_invoice_pdf(deposit_request):
        """إنشاء فاتورة PDF لطلب الإيداع"""
        try:
            # إنشاء مجلد الفواتير إذا لم يكن موجوداً
            invoices_dir = os.path.join(current_app.root_path, 'static', 'deposit_invoices')
            os.makedirs(invoices_dir, exist_ok=True)
            
            # مسار ملف الفاتورة
            filename = f"deposit_invoice_{deposit_request.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(invoices_dir, filename)
            
            # إعداد الألوان والخطوط
            primary_red = colors.HexColor('#ff0033')
            dark_gray = colors.HexColor('#333333')
            light_gray = colors.HexColor('#f8f9fa')
            very_light_red = colors.HexColor('#fff5f5')
            
            # إنشاء مستند PDF
            doc = SimpleDocTemplate(
                filepath, 
                pagesize=A4,
                rightMargin=0.75*inch, 
                leftMargin=0.75*inch,
                topMargin=1*inch, 
                bottomMargin=1*inch
            )
            
            # تحضير المحتوى
            story = []
            styles = getSampleStyleSheet()
            
            # إعداد الأنماط العربية
            arabic_style = ParagraphStyle(
                'Arabic',
                parent=styles['Normal'],
                fontName='Arial',
                fontSize=12,
                alignment=TA_RIGHT,
                spaceBefore=6,
                spaceAfter=6
            )
            
            title_style = ParagraphStyle(
                'ArabicTitle',
                parent=styles['Heading1'],
                fontName='Arial',
                fontSize=24,
                alignment=TA_CENTER,
                textColor=primary_red,
                spaceBefore=12,
                spaceAfter=20,
                fontWeight='bold'
            )
            
            header_style = ParagraphStyle(
                'Header',
                parent=styles['Normal'],
                fontName='Arial',
                fontSize=14,
                alignment=TA_CENTER,
                textColor=dark_gray,
                spaceBefore=6,
                spaceAfter=6
            )
            
            section_header = ParagraphStyle(
                'SectionHeader',
                parent=styles['Normal'],
                fontName='Arial',
                fontSize=14,
                alignment=TA_RIGHT,
                textColor=primary_red,
                spaceBefore=15,
                spaceAfter=10,
                fontWeight='bold'
            )
            
            # إضافة رأس الصفحة
            story.append(DepositInvoiceService._create_header())
            story.append(Spacer(1, 20))
            
            # عنوان الفاتورة
            story.append(Paragraph("فاتورة طلب إيداع", title_style))
            story.append(Spacer(1, 10))
            
            # معلومات الفاتورة الأساسية
            invoice_info_table = DepositInvoiceService._create_invoice_info_table(deposit_request)
            story.append(invoice_info_table)
            story.append(Spacer(1, 20))
            
            # معلومات العميل
            story.append(Paragraph("معلومات العميل", section_header))
            customer_table = DepositInvoiceService._create_customer_info_table(deposit_request)
            story.append(customer_table)
            story.append(Spacer(1, 20))
            
            # تفاصيل طلب الإيداع
            story.append(Paragraph("تفاصيل طلب الإيداع", section_header))
            deposit_details_table = DepositInvoiceService._create_deposit_details_table(deposit_request)
            story.append(deposit_details_table)
            story.append(Spacer(1, 20))
            
            # معلومات الدفع
            story.append(Paragraph("معلومات الدفع", section_header))
            payment_table = DepositInvoiceService._create_payment_info_table(deposit_request)
            story.append(payment_table)
            story.append(Spacer(1, 20))
            
            # حالة الطلب
            if deposit_request.status == 'approved':
                story.append(Paragraph("معلومات المعالجة", section_header))
                processing_table = DepositInvoiceService._create_processing_info_table(deposit_request)
                story.append(processing_table)
                story.append(Spacer(1, 20))
            
            # ملاحظات إضافية
            if deposit_request.admin_notes or deposit_request.rejection_reason:
                story.append(Paragraph("ملاحظات", section_header))
                notes_text = deposit_request.admin_notes or deposit_request.rejection_reason or ""
                story.append(Paragraph(notes_text, arabic_style))
                story.append(Spacer(1, 20))
            
            # تذييل الصفحة
            story.append(DepositInvoiceService._create_footer())
            
            # بناء الـ PDF
            doc.build(story)
            
            return os.path.join('deposit_invoices', filename)
            
        except Exception as e:
            print(f"خطأ في إنشاء فاتورة طلب الإيداع: {e}")
            return None
    
    @staticmethod
    def _create_header():
        """إنشاء رأس الصفحة"""
        primary_red = colors.HexColor('#ff0033')
        
        # جدول الرأس
        header_data = [
            ['🎁', 'ES-GIFT', ''],
            ['', 'خدمات البطائق الرقمية والمدفوعات', ''],
            ['', '📧 business@es-gift.com  |  📱 +966123456789  |  🌐 www.es-gift.com', '']
        ]
        
        header_table = Table(header_data, colWidths=[1*inch, 5*inch, 1*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary_red),
            ('FONTNAME', (1, 0), (1, 0), 'Arial'),
            ('FONTSIZE', (1, 0), (1, 0), 24),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ('FONTNAME', (1, 1), (1, 1), 'Arial'),
            ('FONTSIZE', (1, 1), (1, 1), 14),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
            ('FONTNAME', (1, 2), (1, 2), 'Arial'),
            ('FONTSIZE', (1, 2), (1, 2), 10),
            ('TEXTCOLOR', (1, 2), (1, 2), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return header_table
    
    @staticmethod
    def _create_invoice_info_table(deposit_request):
        """إنشاء جدول معلومات الفاتورة"""
        primary_red = colors.HexColor('#ff0033')
        light_gray = colors.HexColor('#f8f9fa')
        
        # تحديد حالة الطلب
        status_text = {
            'pending': 'قيد المراجعة',
            'approved': 'موافق',
            'rejected': 'مرفوض'
        }.get(deposit_request.status, deposit_request.status)
        
        invoice_data = [
            ['رقم طلب الإيداع:', f"#{deposit_request.id}"],
            ['تاريخ الطلب:', deposit_request.created_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['حالة الطلب:', status_text],
            ['تاريخ إنشاء الفاتورة:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2.5*inch, 3.5*inch])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ('TEXTCOLOR', (0, 0), (0, -1), primary_red),
            ('FONTWEIGHT', (0, 0), (0, -1), 'bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return invoice_table
    
    @staticmethod
    def _create_customer_info_table(deposit_request):
        """إنشاء جدول معلومات العميل"""
        primary_red = colors.HexColor('#ff0033')
        light_gray = colors.HexColor('#f8f9fa')
        
        # تحديد نوع العميل
        customer_type_text = {
            'regular': 'عميل عادي',
            'kyc': 'عميل موثق',
            'reseller': 'موزع'
        }.get(deposit_request.user.customer_type, deposit_request.user.customer_type)
        
        customer_data = [
            ['الاسم:', deposit_request.user.full_name or 'غير محدد'],
            ['البريد الإلكتروني:', deposit_request.user.email],
            ['نوع العميل:', customer_type_text],
        ]
        
        if deposit_request.user.phone:
            customer_data.append(['الهاتف:', deposit_request.user.phone])
        
        customer_table = Table(customer_data, colWidths=[2.5*inch, 3.5*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ('TEXTCOLOR', (0, 0), (0, -1), primary_red),
            ('FONTWEIGHT', (0, 0), (0, -1), 'bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return customer_table
    
    @staticmethod
    def _create_deposit_details_table(deposit_request):
        """إنشاء جدول تفاصيل الإيداع"""
        primary_red = colors.HexColor('#ff0033')
        light_gray = colors.HexColor('#f8f9fa')
        very_light_red = colors.HexColor('#fff5f5')
        
        deposit_data = [
            ['وصف الخدمة', 'المبلغ', 'العملة', 'المبلغ بالدولار'],
            [
                'طلب إيداع محفظة',
                f"{deposit_request.amount}",
                deposit_request.currency_code,
                f"{deposit_request.amount_usd} USD"
            ]
        ]
        
        # إضافة صف الإجمالي
        deposit_data.append([
            'المجموع الكلي',
            f"{deposit_request.amount}",
            deposit_request.currency_code,
            f"{deposit_request.amount_usd} USD"
        ])
        
        deposit_table = Table(deposit_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1.5*inch])
        deposit_table.setStyle(TableStyle([
            # رأس الجدول
            ('BACKGROUND', (0, 0), (-1, 0), primary_red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTWEIGHT', (0, 0), (-1, 0), 'bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # محتوى الجدول
            ('FONTNAME', (0, 1), (-1, -2), 'Arial'),
            ('FONTSIZE', (0, 1), (-1, -2), 11),
            ('ALIGN', (0, 1), (0, -2), 'RIGHT'),
            ('ALIGN', (1, 1), (-1, -2), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, 1), very_light_red),
            
            # صف الإجمالي
            ('BACKGROUND', (0, -1), (-1, -1), primary_red),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('FONTWEIGHT', (0, -1), (-1, -1), 'bold'),
            ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
            
            # حدود
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, primary_red),
            
            # حشو
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return deposit_table
    
    @staticmethod
    def _create_payment_info_table(deposit_request):
        """إنشاء جدول معلومات الدفع"""
        primary_red = colors.HexColor('#ff0033')
        light_gray = colors.HexColor('#f8f9fa')
        
        # تحديد طريقة الدفع
        payment_method_text = {
            'bank_transfer': 'تحويل بنكي',
            'usdt_trc20': 'USDT (TRC20)',
            'visa': 'فيزا/ماستركارد'
        }.get(deposit_request.payment_method, deposit_request.payment_method)
        
        payment_data = [
            ['طريقة الدفع:', payment_method_text],
            ['سعر الصرف:', f"1 {deposit_request.currency_code} = {deposit_request.exchange_rate} USD"],
        ]
        
        # إضافة تفاصيل الدفع إن وجدت
        if deposit_request.payment_details:
            payment_data.append(['تفاصيل الدفع:', deposit_request.payment_details])
        
        payment_table = Table(payment_data, colWidths=[2.5*inch, 3.5*inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ('TEXTCOLOR', (0, 0), (0, -1), primary_red),
            ('FONTWEIGHT', (0, 0), (0, -1), 'bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return payment_table
    
    @staticmethod
    def _create_processing_info_table(deposit_request):
        """إنشاء جدول معلومات المعالجة (للطلبات المقبولة)"""
        primary_red = colors.HexColor('#ff0033')
        light_gray = colors.HexColor('#f8f9fa')
        
        processing_data = [
            ['تاريخ المعالجة:', deposit_request.processed_at.strftime('%Y-%m-%d %H:%M:%S') if deposit_request.processed_at else 'غير محدد'],
            ['المبلغ المضاف:', f"{deposit_request.wallet_amount_added} {deposit_request.wallet_currency_added}" if deposit_request.wallet_amount_added else 'غير محدد'],
        ]
        
        if deposit_request.processor:
            processing_data.append(['معالج الطلب:', deposit_request.processor.full_name or deposit_request.processor.email])
        
        processing_table = Table(processing_data, colWidths=[2.5*inch, 3.5*inch])
        processing_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ('TEXTCOLOR', (0, 0), (0, -1), primary_red),
            ('FONTWEIGHT', (0, 0), (0, -1), 'bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return processing_table
    
    @staticmethod
    def _create_footer():
        """إنشاء تذييل الصفحة"""
        primary_red = colors.HexColor('#ff0033')
        
        # خط فاصل
        footer_line = Drawing(550, 2)
        footer_line.add(Line(0, 1, 550, 1, strokeColor=primary_red, strokeWidth=2))
        
        # نص التذييل
        footer_style = ParagraphStyle(
            'Footer',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            fontName='Arial'
        )
        
        footer_text = [
            footer_line,
            Spacer(1, 10),
            Paragraph("شكراً لك على التعامل مع Es-Gift", footer_style),
            Paragraph("لأي استفسارات، يرجى التواصل معنا عبر business@es-gift.com", footer_style),
            Paragraph(f"تم إنشاء هذه الفاتورة في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style),
        ]
        
        return footer_text
