"""
خدمة فواتير طلبات الإيداع - نسخة محسنة مع دعم العربية
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask import current_app
from datetime import datetime
import os

class SimpleDepositInvoiceService:
    """خدمة إنشاء فواتير PDF بسيطة لطلبات الإيداع"""
    
    def __init__(self):
        """تهيئة الخدمة"""
        self.font_name = 'Helvetica'  # استخدام خط بسيط
    
    def generate_deposit_invoice_pdf(self, deposit_request):
        """إنشاء فاتورة PDF لطلب الإيداع"""
        try:
            # إعداد مسار الملف
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"deposit_invoice_{deposit_request.id}_{timestamp}.pdf"
            invoices_dir = os.path.join('static', 'deposit_invoices')
            
            # التأكد من وجود المجلد
            os.makedirs(invoices_dir, exist_ok=True)
            
            file_path = os.path.join(invoices_dir, filename)
            
            # إنشاء مستند PDF بسيط
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # بناء محتوى الفاتورة
            story = []
            
            # العنوان الرئيسي
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=getSampleStyleSheet()['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#ff0033'),
                alignment=1  # توسيط
            )
            story.append(Paragraph("ES-GIFT DEPOSIT INVOICE", title_style))
            
            # معلومات الشركة
            company_style = ParagraphStyle(
                'CompanyInfo',
                parent=getSampleStyleSheet()['Normal'],
                fontSize=12,
                spaceAfter=20,
                alignment=1
            )
            story.append(Paragraph("Es-Gift Digital Services", company_style))
            story.append(Paragraph("Email: info@es-gift.com", company_style))
            
            # خط فاصل
            story.append(Spacer(1, 20))
            
            # معلومات الفاتورة في جدول
            invoice_info = [
                ['Invoice Information', ''],
                ['Request ID:', str(deposit_request.id)],
                ['Request Date:', deposit_request.created_at.strftime('%Y-%m-%d %H:%M')],
                ['Status:', deposit_request.status.upper()],
                ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M')]
            ]
            
            invoice_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
            invoice_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff0033')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(invoice_table)
            story.append(Spacer(1, 20))
            
            # معلومات العميل
            user = deposit_request.user
            customer_info = [
                ['Customer Information', ''],
                ['Email:', user.email],
                ['User Type:', deposit_request.user_type.replace('_', ' ').title()],
                ['Phone:', user.phone if hasattr(user, 'phone') and user.phone else 'N/A']
            ]
            
            customer_table = Table(customer_info, colWidths=[2*inch, 3*inch])
            customer_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff0033')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(customer_table)
            story.append(Spacer(1, 20))
            
            # تفاصيل الإيداع
            deposit_details = [
                ['Deposit Details', ''],
                ['Description:', 'Wallet Deposit Request'],
                ['Original Amount:', f"{deposit_request.amount} {deposit_request.currency_code}"],
                ['USD Equivalent:', f"${deposit_request.amount_usd}"],
                ['Exchange Rate:', f"{deposit_request.exchange_rate}"],
                ['Payment Method:', deposit_request.payment_method or 'N/A']
            ]
            
            deposit_table = Table(deposit_details, colWidths=[2*inch, 3*inch])
            deposit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff0033')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(deposit_table)
            story.append(Spacer(1, 20))
            
            # معلومات المعالجة (إن وجدت)
            if deposit_request.status == 'approved':
                processing_info = [
                    ['Processing Information', ''],
                    ['Processed Date:', deposit_request.processed_at.strftime('%Y-%m-%d %H:%M') if deposit_request.processed_at else 'N/A'],
                    ['Amount Added:', f"{deposit_request.wallet_amount_added} {deposit_request.wallet_currency_added}"],
                    ['Processor:', f"Admin #{deposit_request.processed_by}"],
                    ['Notes:', deposit_request.admin_notes or 'No additional notes']
                ]
                
                processing_table = Table(processing_info, colWidths=[2*inch, 3*inch])
                processing_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(processing_table)
                story.append(Spacer(1, 20))
            
            # إضافة الختم للمستخدم العادي والموثق فقط
            user_type = deposit_request.user_type
            if user_type in ['regular', 'kyc']:
                try:
                    # مسار ملف الختم
                    stamp_path = os.path.join('static', 'images', 'es pay llc.jpg')
                    
                    # التحقق من وجود ملف الختم
                    if os.path.exists(stamp_path):
                        # إضافة الختم
                        stamp_image = Image(stamp_path, width=2*inch, height=1.5*inch)
                        
                        # إنشاء جدول لوضع الختم
                        stamp_table = Table([['', stamp_image]], colWidths=[3*inch, 2*inch])
                        stamp_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        
                        story.append(Spacer(1, 20))
                        story.append(stamp_table)
                        story.append(Spacer(1, 10))
                        
                        current_app.logger.info(f"تم إضافة الختم للمستخدم نوع: {user_type}")
                    else:
                        current_app.logger.warning(f"ملف الختم غير موجود: {stamp_path}")
                        
                except Exception as e:
                    current_app.logger.error(f"خطأ في إضافة الختم: {e}")
                    # لا نوقف العملية في حالة فشل إضافة الختم
            
            # التذييل
            footer_style = ParagraphStyle(
                'Footer',
                parent=getSampleStyleSheet()['Normal'],
                fontSize=10,
                spaceAfter=10,
                alignment=1,
                textColor=colors.HexColor('#666666')
            )
            story.append(Spacer(1, 30))
            story.append(Paragraph("Thank you for choosing Es-Gift!", footer_style))
            story.append(Paragraph("For inquiries: info@es-gift.com", footer_style))
            story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            
            # بناء PDF
            doc.build(story)
            
            current_app.logger.info(f"تم إنشاء فاتورة PDF: {file_path}")
            return file_path
            
        except Exception as e:
            current_app.logger.error(f"خطأ في إنشاء فاتورة طلب الإيداع: {e}")
            raise e
