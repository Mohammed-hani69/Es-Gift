#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎁 Premium English Invoice Service with Red Design & ES-GIFT Logo
خدمة فواتير إنجليزية متميزة مع تصميم أحمر ولوجو ES-GIFT
"""

import os
import io
from datetime import datetime, timedelta
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line

# Arabic text support libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
    print("✅ Arabic text support libraries loaded successfully")
except ImportError as e:
    print(f"⚠️ Warning: Cannot load Arabic text support libraries: {e}")
    ARABIC_SUPPORT = False

from flask import current_app, url_for
from models import db, Invoice, Order, User

def fix_arabic_text(text):
    """
    Fix Arabic text to display correctly in PDF with proper letter shaping and RTL direction
    إصلاح النص العربي ليظهر بشكل صحيح مع تشابك الحروف والاتجاه الصحيح
    """
    if not ARABIC_SUPPORT or not text or not any('\u0600' <= char <= '\u06FF' for char in text):
        return text
    
    try:
        # Reshape Arabic letters for proper connection
        reshaped_text = arabic_reshaper.reshape(text)
        # Apply BiDi algorithm for correct text direction
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        print(f"Error fixing Arabic text: {e}")
        return text

def setup_fonts():
    """Setup fonts for English and Arabic text support"""
    try:
        # Try to register high-quality fonts
        font_paths = [
            # Windows fonts
            'C:\\Windows\\Fonts\\tahoma.ttf',
            'C:\\Windows\\Fonts\\arial.ttf',
            'C:\\Windows\\Fonts\\calibri.ttf',
            # macOS fonts
            '/System/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            # Linux fonts
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                    print(f"✅ Registered font: {font_path}")
                    return 'CustomFont'
                except Exception as e:
                    print(f"⚠️ Failed to register font {font_path}: {e}")
                    continue
        
        # Use default font if all fail
        print("⚠️ Using default font - may not support Arabic perfectly")
        return 'Helvetica'
        
    except Exception as e:
        print(f"❌ Error setting up fonts: {e}")
        return 'Helvetica'

# Register font when module is loaded
CUSTOM_FONT = setup_fonts()

class PremiumEnglishInvoiceService:
    """Premium English Invoice Service with Red Design and Arabic Support"""
    
    @staticmethod
    def create_invoice(order):
        """Create a new invoice from order"""
        try:
            # Check if invoice already exists
            existing_invoice = Invoice.query.filter_by(order_id=order.id).first()
            if existing_invoice:
                print(f"✅ Invoice already exists: {existing_invoice.invoice_number}")
                return existing_invoice
            
            # Generate invoice number
            invoice_count = Invoice.query.count()
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{(invoice_count + 1):06d}"
            
            # Create new invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                order_id=order.id,
                customer_name=order.user.name,
                customer_email=order.user.email,
                customer_phone=getattr(order.user, 'phone', None),
                customer_type=getattr(order.user, 'customer_type', 'regular'),
                subtotal=order.subtotal or order.total_amount,
                tax_amount=order.tax_amount or 0,
                discount_amount=order.discount_amount or 0,
                total_amount=order.total_amount,
                currency=order.currency or 'SAR',
                payment_method=order.payment_method,
                payment_status='paid' if order.status == 'completed' else 'pending',
                paid_date=order.paid_date if order.status == 'completed' else None,
                invoice_date=datetime.now(),
                due_date=datetime.now() + timedelta(days=30),
                notes="Invoice generated automatically by ES-GIFT system"
            )
            
            db.session.add(invoice)
            db.session.commit()
            print(f"✅ New invoice created: {invoice.invoice_number}")
            return invoice
            
        except Exception as e:
            print(f"❌ Error creating invoice: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def generate_enhanced_pdf(invoice):
        """Generate professional PDF with white and red design inspired by Canva template"""
        try:
            # Create invoices directory if it doesn't exist
            invoice_dir = os.path.join(current_app.static_folder, 'invoices')
            os.makedirs(invoice_dir, exist_ok=True)

            # PDF file path
            filename = f"ES-GIFT_Invoice_{invoice.invoice_number}.pdf"
            pdf_path = os.path.join(invoice_dir, filename)

            # Create PDF with professional design and light red background
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=10*mm,
                bottomMargin=15*mm
            )

            # Professional color scheme - White & Red with light background
            primary_red = colors.HexColor('#E31837')
            dark_red = colors.HexColor('#B71C1C')
            light_red = colors.HexColor('#FFEBEE')
            very_light_red = colors.HexColor('#FFF5F5')  # Very light red background
            dark_gray = colors.HexColor('#424242')
            light_gray = colors.HexColor('#F5F5F5')
            black = colors.HexColor('#212121')
            
            styles = getSampleStyleSheet()
            
            # Professional styles
            company_title = ParagraphStyle(
                'CompanyTitle',
                parent=styles['Heading1'],
                fontSize=36,
                textColor=primary_red,
                alignment=TA_CENTER,
                fontName=CUSTOM_FONT,
                spaceAfter=5,
                spaceBefore=10
            )
            
            company_subtitle = ParagraphStyle(
                'CompanySubtitle',
                parent=styles['Normal'],
                fontSize=14,
                textColor=dark_gray,
                alignment=TA_CENTER,
                fontName=CUSTOM_FONT,
                spaceAfter=20
            )
            
            section_header = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=primary_red,
                alignment=TA_LEFT,
                fontName=CUSTOM_FONT,
                spaceAfter=10,
                spaceBefore=15
            )
            
            normal_text = ParagraphStyle(
                'NormalText',
                parent=styles['Normal'],
                fontSize=11,
                textColor=black,
                alignment=TA_LEFT,
                fontName=CUSTOM_FONT,
                spaceAfter=6
            )

            story = []
            
            # Add light red background to all pages
            def add_background(canvas, doc):
                """Add very light red background to each page"""
                canvas.setFillColor(very_light_red)
                canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            
            # Header with logo and red background
            header_data = []
            
            # Try to add logo only (no stamp in header)
            logo_path = os.path.join(current_app.static_folder, 'images', 'logo.jpg')
            
            # Load logo
            logo_element = None
            if os.path.exists(logo_path):
                try:
                    logo_element = Image(logo_path, width=60, height=60)
                except Exception as e:
                    print(f"Could not load logo: {e}")
                    logo_element = '🎁'
            else:
                logo_element = '🎁'
            
            # Create header with logo only
            header_data = [
                [logo_element, 'ES-GIFT', ''],
                ['', 'Digital Gift Cards & Payment Services', ''],
                ['', f'📧 business@es-gift.com  |  📱 +966123456789  |  🌐 www.es-gift.com', '']
            ]
            
            header_table = Table(header_data, colWidths=[1*inch, 5*inch, 1*inch])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), primary_red),
                ('FONTNAME', (1, 0), (1, 0), CUSTOM_FONT),
                ('FONTSIZE', (1, 0), (1, 0), 36),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
                ('FONTNAME', (1, 1), (1, 1), CUSTOM_FONT),
                ('FONTSIZE', (1, 1), (1, 1), 14),
                ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
                ('FONTNAME', (1, 2), (1, 2), CUSTOM_FONT),
                ('FONTSIZE', (1, 2), (1, 2), 10),
                ('TEXTCOLOR', (1, 2), (1, 2), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ]))
            
            story.append(header_table)
            story.append(Spacer(1, 20))
            
            # Invoice title and number section - Get related order
            order = Order.query.get(invoice.order_id)
            
            invoice_header_data = [
                ['INVOICE', f'# {invoice.invoice_number}'],
                [f'Date: {invoice.invoice_date.strftime("%d %B %Y")}', f'Due: {invoice.due_date.strftime("%d %B %Y") if invoice.due_date else "Upon Receipt"}'],
                [f'Order Number: {order.order_number if order else "N/A"}', '']
            ]
            
            invoice_header_table = Table(invoice_header_data, colWidths=[3*inch, 3*inch])
            invoice_header_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), CUSTOM_FONT),
                ('FONTSIZE', (0, 0), (0, 0), 24),
                ('FONTSIZE', (1, 0), (1, 0), 18),
                ('FONTSIZE', (0, 1), (-1, 2), 12),
                ('TEXTCOLOR', (0, 0), (0, 0), primary_red),
                ('TEXTCOLOR', (1, 0), (1, 0), black),
                ('TEXTCOLOR', (0, 1), (-1, 2), dark_gray),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            story.append(invoice_header_table)
            story.append(Spacer(1, 20))
            
            # Bill to and Company info (no stamp here)
            company_info_text = (
                f"ES-GIFT Digital Services\n"
                f"Kingdom of Saudi Arabia\n"
                f"business@es-gift.com\n"
                f"+966 12 345 6789\n"
                f"www.es-gift.com"
            )
            
            # Use company info text directly without stamp
            company_info_final = company_info_text
            
            bill_to_data = [
                ['BILL TO:', 'COMPANY INFO:'],
                [
                    f"{fix_arabic_text(invoice.customer_name or 'Valued Customer')}\n"
                    f"{invoice.customer_email}\n"
                    f"{invoice.customer_phone or 'Phone not provided'}\n"
                    f"Customer Type: {PremiumEnglishInvoiceService._get_customer_type_english(invoice.customer_type)}",
                    
                    company_info_final
                ]
            ]
            
            bill_to_table = Table(bill_to_data, colWidths=[3*inch, 3*inch])
            bill_to_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), CUSTOM_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('TEXTCOLOR', (0, 0), (-1, 0), primary_red),
                ('FONTNAME', (0, 1), (-1, 1), CUSTOM_FONT),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('TEXTCOLOR', (0, 1), (-1, 1), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 1), (-1, 1), very_light_red),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ]))
            
            story.append(bill_to_table)
            story.append(Spacer(1, 25))
            
            # Products section
            story.append(Paragraph("ITEMS & SERVICES", section_header))
            
            # Products table with professional styling
            order = invoice.order
            product_header = ['#', 'DESCRIPTION', 'QTY', 'UNIT PRICE', 'AMOUNT']
            product_data = [product_header]
            
            item_number = 1
            if hasattr(order, 'items') and order.items:
                for item in order.items:
                    product_name = getattr(item.product, 'name', 'Digital Product') if hasattr(item, 'product') and item.product else 'Digital Product'
                    quantity = getattr(item, 'quantity', 1)
                    price = float(getattr(item, 'price', 0))
                    total_price = price * quantity
                    
                    product_data.append([
                        str(item_number),
                        fix_arabic_text(product_name),
                        str(quantity),
                        f"{price:.2f} {invoice.currency}",
                        f"{total_price:.2f} {invoice.currency}"
                    ])
                    item_number += 1
            else:
                quantity = 1
                total_price = float(invoice.total_amount)
                unit_price = total_price
                product_name = getattr(order.product, 'name', 'Digital Gift Card') if order and hasattr(order, 'product') and order.product else 'Digital Gift Card'
                
                product_data.append([
                    "1",
                    fix_arabic_text(product_name),
                    str(quantity),
                    f"{unit_price:.2f} {invoice.currency}",
                    f"{total_price:.2f} {invoice.currency}"
                ])
            
            products_table = Table(product_data, colWidths=[0.5*inch, 3.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
            products_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), primary_red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), CUSTOM_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Content styling
                ('FONTNAME', (0, 1), (-1, -1), CUSTOM_FONT),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TEXTCOLOR', (0, 1), (-1, -1), black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Item numbers
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Description
                ('ALIGN', (2, 1), (-1, -1), 'CENTER'), # Qty, Price, Amount
                
                # Alternating row colors
                ('BACKGROUND', (0, 1), (-1, 1), very_light_red),
                
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('LINEBELOW', (0, 0), (-1, 0), 2, primary_red),
                
                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(products_table)
            story.append(Spacer(1, 20))
            
            # Financial summary - professional layout
            summary_data = [
                ['Subtotal:', f"{float(invoice.subtotal):.2f} {invoice.currency}"],
                ['Discount:', f"-{float(invoice.discount_amount):.2f} {invoice.currency}"],
                ['Tax & Fees:', f"+{float(invoice.tax_amount):.2f} {invoice.currency}"],
                ['', ''],  # Empty row for spacing
                ['TOTAL:', f"{float(invoice.total_amount):.2f} {invoice.currency}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                # Regular rows
                ('FONTNAME', (0, 0), (-1, -2), CUSTOM_FONT),
                ('FONTSIZE', (0, 0), (-1, -2), 11),
                ('TEXTCOLOR', (0, 0), (-1, -2), black),
                ('ALIGN', (0, 0), (-1, -2), 'RIGHT'),
                
                # Total row
                ('FONTNAME', (0, -1), (-1, -1), CUSTOM_FONT),
                ('FONTSIZE', (0, -1), (-1, -1), 14),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('BACKGROUND', (0, -1), (-1, -1), primary_red),
                ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
                
                # Padding and spacing
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                
                # Borders
                ('LINEABOVE', (0, -1), (-1, -1), 2, primary_red),
            ]))
            
            summary_table.hAlign = 'RIGHT'
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Payment status
            payment_status_text, payment_color, payment_emoji = PremiumEnglishInvoiceService._get_payment_status_info(invoice.payment_status)
            payment_method_clean = PremiumEnglishInvoiceService._get_payment_method_english(invoice.payment_method)
            
            status_data = [
                ['PAYMENT STATUS', 'PAYMENT METHOD'],
                [f'{payment_emoji} {payment_status_text}', payment_method_clean]
            ]
            
            if invoice.paid_date:
                status_data.append(['PAID DATE', invoice.paid_date.strftime('%d %B %Y')])
            
            status_table = Table(status_data, colWidths=[3*inch, 3*inch])
            status_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), CUSTOM_FONT),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('TEXTCOLOR', (0, 0), (-1, 0), primary_red),
                ('FONTNAME', (0, 1), (-1, -1), CUSTOM_FONT),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('TEXTCOLOR', (0, 1), (-1, -1), payment_color),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 1), (-1, -1), very_light_red),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            story.append(status_table)
            story.append(Spacer(1, 20))
            
            # Notes section
            if invoice.notes:
                story.append(Paragraph("NOTES", section_header))
                notes_para = Paragraph(fix_arabic_text(invoice.notes), normal_text)
                story.append(notes_para)
                story.append(Spacer(1, 15))
            
            # Professional footer with stamp
            story.append(Spacer(1, 20))
            
            footer_line = Drawing(550, 2)
            footer_line.add(Line(0, 1, 550, 1, strokeColor=primary_red, strokeWidth=2))
            story.append(footer_line)
            story.append(Spacer(1, 10))
            
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=dark_gray,
                alignment=TA_CENTER,
                fontName=CUSTOM_FONT
            )
            
            # Add company stamp at the bottom (larger size, centered, no background)
            stamp_path = os.path.join(current_app.static_folder, 'images', 'es pay llc.jpg')
            if os.path.exists(stamp_path):
                try:
                    # Create larger stamp for footer (increased size)
                    stamp_footer = Image(stamp_path, width=120, height=100)
                    
                    # Create centered footer layout with stamp only
                    footer_data = [
                        ['Thank you for your business!'],
                        [f'Invoice generated on {datetime.now().strftime("%d %B %Y at %H:%M")}'],
                        ['ES-GIFT - Your trusted digital gift card partner'],
                        [''],  # Empty row for spacing
                        [stamp_footer]  # Stamp in its own centered row
                    ]
                    
                    footer_table = Table(footer_data, colWidths=[6*inch])
                    footer_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, 2), CUSTOM_FONT),
                        ('FONTSIZE', (0, 0), (0, 2), 9),
                        ('TEXTCOLOR', (0, 0), (0, 2), dark_gray),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 0), (0, 2), 5),
                        ('BOTTOMPADDING', (0, 0), (0, 2), 5),
                        ('TOPPADDING', (0, 4), (0, 4), 15),  # Extra space above stamp
                        ('BOTTOMPADDING', (0, 4), (0, 4), 10),
                    ]))
                    
                    story.append(footer_table)
                    print("✅ ES Pay LLC stamp added to footer (larger, centered, no background)")
                    
                except Exception as e:
                    print(f"Could not load footer stamp: {e}")
                    # Fallback to regular footer
                    story.append(Paragraph("Thank you for your business!", footer_style))
                    story.append(Paragraph(f"Invoice generated on {datetime.now().strftime('%d %B %Y at %H:%M')}", footer_style))
                    story.append(Paragraph("ES-GIFT - Your trusted digital gift card partner", footer_style))
            else:
                # Fallback to regular footer
                story.append(Paragraph("Thank you for your business!", footer_style))
                story.append(Paragraph(f"Invoice generated on {datetime.now().strftime('%d %B %Y at %H:%M')}", footer_style))
                story.append(Paragraph("ES-GIFT - Your trusted digital gift card partner", footer_style))
            
            # Build the document with background
            doc.build(story, onFirstPage=add_background, onLaterPages=add_background)
            return f"invoices/{filename}"
            
        except Exception as e:
            print(f"Error creating professional PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _get_customer_type_english(customer_type):
        """Translate customer type to English"""
        type_mapping = {
            'regular': 'Regular Customer',
            'kyc': 'Verified Customer (KYC)',
            'reseller': 'Reseller',
            'vip': 'VIP Customer',
            'corporate': 'Corporate Client'
        }
        return type_mapping.get(customer_type, 'Regular Customer')
    
    @staticmethod
    def _get_payment_method_english(payment_method):
        """Convert payment method to clean English format"""
        if not payment_method:
            return 'DIGITAL PAYMENT'
        
        # Clean and convert payment method
        method = str(payment_method).lower().strip()
        
        # Handle different payment method formats
        if 'card' in method or 'visa' in method or 'mastercard' in method or 'مدى' in method:
            if 'visa' in method:
                return 'VISA CARD'
            elif 'mastercard' in method or 'ماستركارد' in method:
                return 'MASTERCARD'
            elif 'مدى' in method:
                return 'MADA CARD'
            else:
                return 'CREDIT CARD'
        elif 'paypal' in method:
            return 'PAYPAL'
        elif 'bank' in method or 'تحويل' in method:
            return 'BANK TRANSFER'
        elif 'cash' in method or 'نقد' in method:
            return 'CASH'
        elif 'wallet' in method or 'محفظة' in method:
            return 'DIGITAL WALLET'
        elif 'apple' in method:
            return 'APPLE PAY'
        elif 'google' in method:
            return 'GOOGLE PAY'
        elif 'stc' in method:
            return 'STC PAY'
        else:
            # Clean any remaining Arabic/special characters
            cleaned = method.replace('card_/', '').replace('_/', '').replace('/', ' ').strip()
            return cleaned.upper() if cleaned else 'DIGITAL PAYMENT'

    @staticmethod
    def _get_payment_status_info(payment_status):
        """Get payment status information with colors and emojis"""
        if not payment_status:
            return ('PENDING', colors.HexColor('#FFC107'), '⏳')
        
        # Convert to lowercase for better matching
        status = str(payment_status).lower().strip()
        
        status_info = {
            'paid': ('PAID', colors.HexColor('#28A745'), '✅'),
            'completed': ('PAID', colors.HexColor('#28A745'), '✅'),
            'success': ('PAID', colors.HexColor('#28A745'), '✅'),
            'successful': ('PAID', colors.HexColor('#28A745'), '✅'),
            'مكتمل': ('PAID', colors.HexColor('#28A745'), '✅'),
            'مدفوع': ('PAID', colors.HexColor('#28A745'), '✅'),
            
            'pending': ('PENDING', colors.HexColor('#FFC107'), '⏳'),
            'processing': ('PENDING', colors.HexColor('#FFC107'), '⏳'),
            'waiting': ('PENDING', colors.HexColor('#FFC107'), '⏳'),
            'قيد الانتظار': ('PENDING', colors.HexColor('#FFC107'), '⏳'),
            'معلق': ('PENDING', colors.HexColor('#FFC107'), '⏳'),
            
            'failed': ('FAILED', colors.HexColor('#DC3545'), '❌'),
            'cancelled': ('FAILED', colors.HexColor('#DC3545'), '❌'),
            'declined': ('FAILED', colors.HexColor('#DC3545'), '❌'),
            'فشل': ('FAILED', colors.HexColor('#DC3545'), '❌'),
            'ملغي': ('FAILED', colors.HexColor('#DC3545'), '❌'),
            
            'refunded': ('REFUNDED', colors.HexColor('#6F42C1'), '🔄'),
            'returned': ('REFUNDED', colors.HexColor('#6F42C1'), '🔄'),
            'مسترد': ('REFUNDED', colors.HexColor('#6F42C1'), '🔄')
        }
        
        return status_info.get(status, ('PENDING', colors.HexColor('#FFC107'), '⏳'))
    
    @staticmethod
    def send_invoice_email(invoice, recipient_email=None):
        """Send invoice via email with enhanced guaranteed delivery system"""
        try:
            # Use provided email or invoice customer email
            email_to_send = recipient_email or invoice.customer_email
            
            if not email_to_send:
                print("❌ No email address provided")
                return False
            
            print(f"🚀 Enhanced: Sending invoice {invoice.invoice_number} to: {email_to_send}")
            
            # Try guaranteed delivery system first (NEW)
            try:
                from guaranteed_invoice_email import send_invoice_guaranteed
                success = send_invoice_guaranteed(invoice, email_to_send)
                
                if success:
                    print(f"✅ Invoice sent via GUARANTEED system to: {email_to_send}")
                    return True
                else:
                    print("⚠️ Guaranteed system failed, trying fallback services...")
            except Exception as e:
                print(f"⚠️ Guaranteed service error: {e}, trying fallback services...")
            
            # Generate PDF for other services
            pdf_path = PremiumEnglishInvoiceService.generate_enhanced_pdf(invoice)
            if not pdf_path:
                print("❌ Failed to generate PDF for email")
                return False
            
            pdf_full_path = os.path.join(current_app.static_folder, pdf_path)
            
            # Determine language based on customer name/notes for email content
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in (invoice.customer_name + (invoice.notes or '')))
            
            if has_arabic:
                # Arabic email content with new design matching HTML template
                subject = f"🎁 ES-GIFT Invoice - {invoice.invoice_number}"
                email_content = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); position: relative;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-direction: row;">
        <div style="background: #dc143c; color: white; padding: 20px; text-align: center; width: 25%; display: flex; flex-direction: column; height: 100px; justify-content: center;">
            <h1 style="margin: 0; font-size: 22px">🎁 ES-GIFT</h1>
            <p style="margin: 8px 0 0 0; font-size: 14px;">Leading Digital Gift Cards</p>
        </div>
        <div style="background: #dc143c; color: white; padding: 20px; width: 40%; height: 20px; text-align: center; display: flex; justify-content: center; align-items: center; margin-top: 60px;">
            <p style="color: #fff; font-size: 30px; font-weight: bold; letter-spacing: 5px;">Sales Invoice</p>
        </div>
    </div>

    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; text-align: left; display: flex; flex-direction: column; align-items: flex-start;">
        <div style="color: #2c3e50; margin-bottom: 20px">
            <span style="font-size: 20px; font-weight: 600">Client ID:</span>
            <span style="font-size: 20px; font-weight: 600">{invoice.customer_id if hasattr(invoice, 'customer_id') else 'Not Available'}</span>
        </div>

        <div style="display: flex; flex-direction: row; justify-content: space-between; align-items: center; width: 90%;">
            <div style="color: #2c3e50; margin-bottom: 20px">
                <span style="font-size: 20px; font-weight: 600">Client Name:</span>
                <span style="font-size: 20px; font-weight: 600">{invoice.customer_name}</span>
            </div>
            <div style="color: #2c3e50; margin-bottom: 20px">
                <span style="font-size: 20px; font-weight: 600">Invoice No:</span>
                <span style="font-size: 20px; font-weight: 600">{invoice.invoice_number}</span>
            </div>
        </div>

        <div style="color: #2c3e50; margin-bottom: 20px">
            <span style="font-size: 20px; font-weight: 600">Date:</span>
            <span style="font-size: 20px; font-weight: 600">{invoice.invoice_date.strftime('%d-%m-%Y')}</span>
        </div>

        <table style="width: 100%; border-collapse: collapse; text-align: center; font-family: Arial, sans-serif;">
            <thead>
                <tr style="background-color: #dc143c; color: white">
                    <th style="padding: 8px; font-size: 18px">#</th>
                    <th style="padding: 8px; font-size: 18px">Description</th>
                    <th style="padding: 8px; font-size: 18px">Quantity</th>
                    <th style="padding: 8px; font-size: 18px">Price</th>
                    <th style="padding: 8px; font-size: 18px">Total</th>
                </tr>
            </thead>
            <tbody>
                {"".join(f'''
                <tr {"style='background-color: #f5f5f5'" if i % 2 != 0 else ""}>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{i+1}</td>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{item['description']}</td>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{item['quantity']}</td>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{float(item['price']):.2f}</td>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{float(item['total']):.2f}</td>
                </tr>
                ''' for i, item in enumerate(invoice.items))}
            </tbody>
        </table>

        <div style="display: flex; flex-direction: column; align-items: flex-start; width: 100%; margin-top: 20px;">
            <div style="display: flex; width: 44%; gap: 20px; justify-content: space-around; height: 20px; align-items: center; margin-bottom: 15px;">
                <p style="font-size: 20px; font-weight: 700; margin-left: 20px">{float(invoice.total_amount):.2f}</p>
                <p style="font-size: 20px; font-weight: 700">Price</p>
            </div>
            <div style="display: flex; width: 44%; justify-content: space-around; height: 20px; align-items: center; margin-bottom: 10px;">
                <p style="font-size: 20px; font-weight: 700; margin-left: 20px">0.00</p>
                <p style="font-size: 20px; font-weight: 700">Tax</p>
            </div>
            <div style="display: flex; width: 44%; justify-content: space-around; height: 20px; align-items: center; margin-bottom: 10px; background-color: #f5f5f5; padding: 20px 0;">
                <p style="font-size: 20px; font-weight: 700; margin-left: 20px">{float(invoice.total_amount):.2f}</p>
                <p style="font-size: 20px; font-weight: 700">Grand Total</p>
            </div>
        </div>

        <div style="display: flex; flex-direction: row; justify-content: space-between; width: 80%; margin: 20px 0;">
            <div>
                <h3 style="font-size: 25px; font-weight: bolder; color: #dc143c; margin: 10px 0;">Notes</h3>
                <ul style="padding: 0 20px; margin: 0">
                    <li style="font-weight: 600; color: #2c3e50">Goods sold are not returnable or exchangeable</li>
                    <li style="font-weight: 600; color: #2c3e50">Please make sure all invoice items are received</li>
                </ul>
            </div>
            <div>
                <p style="font-size: 20px; font-weight: 700; color: #dc143c">Seller Signature</p>
            </div>
        </div>

        <div style="display: flex; justify-content: flex-start; width: 90%">
            <p style="font-size: 20px; color: #2c3e50; font-weight: 600">Thank you</p>
        </div>
    </div>

    <div style="position: absolute; bottom: 0px; right: 40%;">
        <img src="es.jpg" alt="es-gift" style="width: 100px; height: 100px" />
    </div>
</div>
"""

            else:
                # English email content with new design matching HTML template
                subject = f"🎁 ES-GIFT Invoice - {invoice.invoice_number}"
                email_content = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); position: relative;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-direction: row;">
        <div style="background: #dc143c; color: white; padding: 20px; text-align: center; width: 25%; display: flex; flex-direction: column; height: 100px; justify-content: center;">
            <h1 style="margin: 0; font-size: 22px">🎁 ES-GIFT</h1>
            <p style="margin: 8px 0 0 0; font-size: 14px;">Leading Digital Gift Cards</p>
        </div>
        <div style="background: #dc143c; color: white; padding: 20px; width: 40%; height: 20px; text-align: center; display: flex; justify-content: center; align-items: center; margin-top: 60px;">
            <p style="color: #fff; font-size: 30px; font-weight: bold; letter-spacing: 5px;">Sales Invoice</p>
        </div>
    </div>

    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; text-align: left; display: flex; flex-direction: column; align-items: flex-start;">
        <div style="color: #2c3e50; margin-bottom: 20px">
            <span style="font-size: 20px; font-weight: 600">Client ID:</span>
            <span style="font-size: 20px; font-weight: 600">{invoice.customer_id if hasattr(invoice, 'customer_id') else 'Not Available'}</span>
        </div>

        <div style="display: flex; flex-direction: row; justify-content: space-between; align-items: center; width: 90%;">
            <div style="color: #2c3e50; margin-bottom: 20px">
                <span style="font-size: 20px; font-weight: 600">Client Name:</span>
                <span style="font-size: 20px; font-weight: 600">{invoice.customer_name}</span>
            </div>
            <div style="color: #2c3e50; margin-bottom: 20px">
                <span style="font-size: 20px; font-weight: 600">Invoice No:</span>
                <span style="font-size: 20px; font-weight: 600">{invoice.invoice_number}</span>
            </div>
        </div>

        <div style="color: #2c3e50; margin-bottom: 20px">
            <span style="font-size: 20px; font-weight: 600">Date:</span>
            <span style="font-size: 20px; font-weight: 600">{invoice.invoice_date.strftime('%d-%m-%Y')}</span>
        </div>

        <table style="width: 100%; border-collapse: collapse; text-align: center; font-family: Arial, sans-serif;">
            <thead>
                <tr style="background-color: #dc143c; color: white">
                    <th style="padding: 8px; font-size: 18px">#</th>
                    <th style="padding: 8px; font-size: 18px">Description</th>
                    <th style="padding: 8px; font-size: 18px">Quantity</th>
                    <th style="padding: 8px; font-size: 18px">Price</th>
                    <th style="padding: 8px; font-size: 18px">Total</th>
                </tr>
            </thead>
            <tbody>
                {"".join(f'''
                <tr {"style='background-color: #f5f5f5'" if i % 2 != 0 else ""}>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{i+1}</td>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{item['description']}</td>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{item['quantity']}</td>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{float(item['price']):.2f}</td>
                    <td style="padding: 8px; font-size: 15px; font-weight: 600">{float(item['total']):.2f}</td>
                </tr>
                ''' for i, item in enumerate(invoice.items))}
            </tbody>
        </table>

        <div style="display: flex; flex-direction: column; align-items: flex-start; width: 100%; margin-top: 20px;">
            <div style="display: flex; width: 44%; gap: 20px; justify-content: space-around; height: 20px; align-items: center; margin-bottom: 15px;">
                <p style="font-size: 20px; font-weight: 700; margin-left: 20px">{float(invoice.total_amount):.2f}</p>
                <p style="font-size: 20px; font-weight: 700">Price</p>
            </div>
            <div style="display: flex; width: 44%; justify-content: space-around; height: 20px; align-items: center; margin-bottom: 10px;">
                <p style="font-size: 20px; font-weight: 700; margin-left: 20px">0.00</p>
                <p style="font-size: 20px; font-weight: 700">Tax</p>
            </div>
            <div style="display: flex; width: 44%; justify-content: space-around; height: 20px; align-items: center; margin-bottom: 10px; background-color: #f5f5f5; padding: 20px 0;">
                <p style="font-size: 20px; font-weight: 700; margin-left: 20px">{float(invoice.total_amount):.2f}</p>
                <p style="font-size: 20px; font-weight: 700">Grand Total</p>
            </div>
        </div>

        <div style="display: flex; flex-direction: row; justify-content: space-between; width: 80%; margin: 20px 0;">
            <div>
                <h3 style="font-size: 25px; font-weight: bolder; color: #dc143c; margin: 10px 0;">Notes</h3>
                <ul style="padding: 0 20px; margin: 0">
                    <li style="font-weight: 600; color: #2c3e50">Goods sold are not returnable or exchangeable</li>
                    <li style="font-weight: 600; color: #2c3e50">Please make sure all invoice items are received</li>
                </ul>
            </div>
            <div>
                <p style="font-size: 20px; font-weight: 700; color: #dc143c">Seller Signature</p>
            </div>
        </div>

        <div style="display: flex; justify-content: flex-start; width: 90%">
            <p style="font-size: 20px; color: #2c3e50; font-weight: 600">Thank you</p>
        </div>
    </div>

    <div style="position: absolute; bottom: 0px; right: 40%;">
        <img src="es.jpg" alt="es-gift" style="width: 100px; height: 100px" />
    </div>
</div>
"""

            
            # Multi-tier email sending strategy: Hostinger → Email Sender Pro → Flask-Mail → Direct Gmail
            
            # 1. Try Hostinger service first
            try:
                from send_by_hostinger import send_invoice_email_hostinger
                print("🚀 Trying Hostinger SMTP service...")
                success = send_invoice_email_hostinger(
                    to_email=email_to_send,
                    subject=subject,
                    html_content=email_content,
                    pdf_attachment_path=pdf_full_path,
                    pdf_filename=f"ES-GIFT_Invoice_{invoice.invoice_number}.pdf"
                )
                
                if success:
                    print(f"✅ Invoice email sent successfully via Hostinger to: {email_to_send}")
                    return True
                else:
                    print(f"⚠️ Hostinger failed, trying Email Sender Pro...")
            except Exception as e:
                print(f"⚠️ Hostinger service error: {e}, trying Email Sender Pro...")
            
            # 2. Try Email Sender Pro service
            try:
                from email_sender_pro_service import EmailSenderProService
                sender_pro = EmailSenderProService()
                
                print("⚡ Trying Email Sender Pro service...")
                success = sender_pro.send_custom_email(
                    email=email_to_send,
                    subject=subject,
                    html_content=email_content,
                    pdf_attachment_path=pdf_full_path
                )
                
                if success:
                    print(f"✅ Invoice sent via Email Sender Pro to: {email_to_send}")
                    return True
                else:
                    print("⚠️ Email Sender Pro failed, trying Flask-Mail...")
                    
            except Exception as e:
                print(f"⚠️ Email Sender Pro service error: {e}, trying Flask-Mail...")
            
            # 3. Try Flask-Mail with Gmail fallback
            try:
                success = PremiumEnglishInvoiceService._send_invoice_email_fallback(
                    invoice, email_content, pdf_full_path, email_to_send
                )
                
                if success:
                    print(f"✅ Invoice sent via Flask-Mail fallback to: {email_to_send}")
                    return True
                else:
                    print("⚠️ Flask-Mail failed, trying direct Gmail...")
                    
            except Exception as e:
                print(f"⚠️ Flask-Mail error: {e}, trying direct Gmail...")
            
            # 4. Final fallback - Direct Gmail SMTP
            try:
                success = PremiumEnglishInvoiceService._send_gmail_fallback(
                    email_to_send, invoice, email_content, pdf_full_path
                )
                
                if success:
                    print(f"✅ Invoice sent via direct Gmail to: {email_to_send}")
                    return True
                else:
                    print("❌ All email methods failed")
                    return False
                    
            except Exception as e:
                print(f"❌ Direct Gmail also failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending invoice email: {e}")
            return False
    
    @staticmethod
    def _send_invoice_email_fallback(invoice, email_html, pdf_full_path, email_to_send):
        """Send invoice using Flask-Mail with Gmail fallback configuration"""
        try:
            from flask_mail import Message, Mail
            from flask import current_app
            
            # Try to get mail instance
            mail = current_app.extensions.get('mail')
            if not mail:
                print("Flask-Mail service not configured, trying Gmail fallback...")
                return PremiumEnglishInvoiceService._send_gmail_fallback(email_to_send, invoice, email_html, pdf_full_path)
            
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in (invoice.customer_name + (invoice.notes or '')))
            subject = f"🎁 {'فاتورة' if has_arabic else 'Invoice'} ES-GIFT - {invoice.invoice_number}"
            
            # إعداد المرسل مع الإعدادات البديلة لـ Gmail
            sender_email = "esgiftscard@gmail.com"
            sender_name = "ES-GIFT"
            
            # تحديث إعدادات Flask-Mail مؤقتاً للإرسال البديل
            original_mail_server = current_app.config.get('MAIL_SERVER')
            original_mail_port = current_app.config.get('MAIL_PORT')
            original_mail_username = current_app.config.get('MAIL_USERNAME')
            original_mail_password = current_app.config.get('MAIL_PASSWORD')
            original_mail_use_tls = current_app.config.get('MAIL_USE_TLS')
            original_mail_use_ssl = current_app.config.get('MAIL_USE_SSL')
            original_default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            
            # تطبيق إعدادات Gmail البديلة
            current_app.config['MAIL_SERVER'] = 'smtp.gmail.com'
            current_app.config['MAIL_PORT'] = 587
            current_app.config['MAIL_USERNAME'] = sender_email
            current_app.config['MAIL_PASSWORD'] = 'jxtr qylc lzkj ehpb'
            current_app.config['MAIL_USE_TLS'] = True
            current_app.config['MAIL_USE_SSL'] = False
            current_app.config['MAIL_DEFAULT_SENDER'] = (sender_name, sender_email)
            
            # إعادة تهيئة Flask-Mail بالإعدادات الجديدة
            mail.init_app(current_app)
            
            try:
                msg = Message(
                    subject=subject,
                    sender=(sender_name, sender_email),
                    recipients=[email_to_send]
                )
                
                msg.html = email_html
                
                # Add invoice as attachment if PDF exists
                if pdf_full_path and os.path.exists(pdf_full_path):
                    with open(pdf_full_path, 'rb') as fp:
                        msg.attach(
                            filename=f"ES-GIFT_Invoice_{invoice.invoice_number}.pdf",
                            content_type='application/pdf',
                            data=fp.read()
                        )
                
                mail.send(msg)
                print(f"✅ Invoice sent successfully via Flask-Mail (Gmail) to: {email_to_send}")
                return True
                
            finally:
                # استعادة الإعدادات الأصلية
                current_app.config['MAIL_SERVER'] = original_mail_server
                current_app.config['MAIL_PORT'] = original_mail_port
                current_app.config['MAIL_USERNAME'] = original_mail_username
                current_app.config['MAIL_PASSWORD'] = original_mail_password
                current_app.config['MAIL_USE_TLS'] = original_mail_use_tls
                current_app.config['MAIL_USE_SSL'] = original_mail_use_ssl
                current_app.config['MAIL_DEFAULT_SENDER'] = original_default_sender
                
                # إعادة تهيئة Flask-Mail بالإعدادات الأصلية
                if original_mail_server:
                    mail.init_app(current_app)
            
        except Exception as e:
            print(f"❌ Error sending email using Flask-Mail: {e}")
            # Try using Gmail fallback as final option
            return PremiumEnglishInvoiceService._send_gmail_fallback(email_to_send, invoice, email_html, pdf_full_path)
    
    @staticmethod
    def _send_gmail_fallback(email_to_send, invoice, email_html, pdf_full_path):
        """Send email using direct Gmail SMTP as final fallback"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            from email.header import Header
            import os
            
            print("📧 محاولة إرسال مباشر عبر Gmail...")
            
            # Gmail fallback configuration
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "esgiftscard@gmail.com"
            sender_password = "xopq ikac efpj rdif"
            sender_name = "ES-GIFT"
            
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in (invoice.customer_name + (invoice.notes or '')))
            subject = f"🎁 {'فاتورة' if has_arabic else 'Invoice'} ES-GIFT - {invoice.invoice_number}"
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = f"ES-GIFT <{sender_email}>"
            msg['To'] = email_to_send
            
            # Add HTML content
            html_part = MIMEText(email_html, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add PDF attachment if exists
            if pdf_full_path and os.path.exists(pdf_full_path):
                with open(pdf_full_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= "ES-GIFT_Invoice_{invoice.invoice_number}.pdf"'
                    )
                    msg.attach(part)
                    print(f"📎 تم إرفاق الملف: {pdf_full_path}")
            
            # Send via Gmail SMTP
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print(f"✅ تم الإرسال المباشر عبر Gmail بنجاح")
            return True
            
        except Exception as e:
            print(f"❌ فشل في الإرسال المباشر عبر Gmail: {e}")
            return False

# Create alias for compatibility
ModernInvoiceService = PremiumEnglishInvoiceService
InvoiceService = PremiumEnglishInvoiceService
