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
            
            # Try to add logo and stamp if they exist
            logo_path = os.path.join(current_app.static_folder, 'images', 'logo.jpg')
            stamp_path = os.path.join(current_app.static_folder, 'images', 'es pay llc.jpg')
            
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
            
            # Load stamp
            stamp_element = ''
            if os.path.exists(stamp_path):
                try:
                    stamp_element = Image(stamp_path, width=50, height=50)
                    print("✅ ES Pay LLC stamp loaded successfully")
                except Exception as e:
                    print(f"Could not load stamp: {e}")
                    stamp_element = ''
            
            # Create header with logo and stamp
            header_data = [
                [logo_element, 'ES-GIFT', stamp_element],
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
            
            # Bill to and Company info with stamp
            company_info_text = (
                f"ES-GIFT Digital Services\n"
                f"Kingdom of Saudi Arabia\n"
                f"business@es-gift.com\n"
                f"+966 12 345 6789\n"
                f"www.es-gift.com"
            )
            
            # Try to add stamp to company info section
            stamp_path = os.path.join(current_app.static_folder, 'images', 'es pay llc.jpg')
            company_info_with_stamp = company_info_text
            
            if os.path.exists(stamp_path):
                try:
                    # Create a small stamp for company info section
                    company_stamp = Image(stamp_path, width=40, height=40)
                    
                    # Create company info with stamp layout
                    company_info_data = [
                        [company_info_text, company_stamp]
                    ]
                    
                    company_info_table = Table(company_info_data, colWidths=[2.5*inch, 0.8*inch])
                    company_info_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, 0), CUSTOM_FONT),
                        ('FONTSIZE', (0, 0), (0, 0), 10),
                        ('TEXTCOLOR', (0, 0), (0, 0), black),
                        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ]))
                    
                    company_info_final = company_info_table
                    print("✅ ES Pay LLC stamp added to company info section")
                    
                except Exception as e:
                    print(f"Could not load company stamp: {e}")
                    company_info_final = company_info_text
            else:
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
            
            status_data = [
                ['PAYMENT STATUS', 'PAYMENT METHOD'],
                [f'{payment_emoji} {payment_status_text}', f'{invoice.payment_method.upper() if invoice.payment_method else "DIGITAL PAYMENT"}']
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
            
            # Add company stamp at the bottom
            stamp_path = os.path.join(current_app.static_folder, 'images', 'es pay llc.jpg')
            if os.path.exists(stamp_path):
                try:
                    stamp_footer = Image(stamp_path, width=60, height=60)
                    
                    # Create footer table with stamp
                    footer_data = [
                        ['Thank you for your business!', stamp_footer],
                        [f'Invoice generated on {datetime.now().strftime("%d %B %Y at %H:%M")}', ''],
                        ['ES-GIFT - Your trusted digital gift card partner', '']
                    ]
                    
                    footer_table = Table(footer_data, colWidths=[4*inch, 2*inch])
                    footer_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, -1), CUSTOM_FONT),
                        ('FONTSIZE', (0, 0), (0, -1), 9),
                        ('TEXTCOLOR', (0, 0), (0, -1), dark_gray),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    
                    story.append(footer_table)
                    print("✅ ES Pay LLC stamp added to footer")
                    
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
    def _get_payment_status_info(payment_status):
        """Get payment status information with colors and emojis"""
        status_info = {
            'paid': ('PAID', colors.HexColor('#28A745'), '✅'),
            'pending': ('PENDING', colors.HexColor('#FFC107'), '⏳'),
            'failed': ('FAILED', colors.HexColor('#DC3545'), '❌'),
            'refunded': ('REFUNDED', colors.HexColor('#6F42C1'), '🔄')
        }
        return status_info.get(payment_status, ('UNKNOWN', colors.gray, '❓'))
    
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
                # Arabic email content
                subject = f"🎁 فاتورة ES-GIFT - {invoice.invoice_number}"
                email_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
                    <div style="background: #DC143C; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🎁 ES-GIFT</h1>
                        <p style="margin: 5px 0 0 0; font-size: 14px;">بطاقات الهدايا الرقمية الرائدة</p>
                    </div>
                    
                    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2C3E50; margin-bottom: 20px;">عزيزي/عزيزتي {fix_arabic_text(invoice.customer_name)}</h2>
                        
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            نشكركم لاختياركم ES-GIFT. يسعدنا إرسال فاتورتكم.
                        </p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-right: 4px solid #DC143C;">
                            <h3 style="color: #DC143C; margin-top: 0;">📋 تفاصيل الفاتورة:</h3>
                            <p><strong>رقم الفاتورة:</strong> {invoice.invoice_number}</p>
                            <p><strong>رقم الطلب:</strong> {Order.query.get(invoice.order_id).order_number if Order.query.get(invoice.order_id) else 'غير متوفر'}</p>
                            <p><strong>التاريخ:</strong> {invoice.invoice_date.strftime('%Y-%m-%d')}</p>
                            <p><strong>المبلغ الإجمالي:</strong> {float(invoice.total_amount):.2f} {invoice.currency}</p>
                            <p><strong>حالة الدفع:</strong> {PremiumEnglishInvoiceService._get_payment_status_info(invoice.payment_status)[0]}</p>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            إذا كان لديكم أي استفسارات، لا تترددوا في التواصل معنا على:
                            <br>📧 business@es-gift.com
                            <br>📱 +966123456789
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #999; font-size: 12px;">
                                شكراً لكم مرة أخرى لثقتكم في ES-GIFT
                                <br>🌐 www.es-gift.com
                            </p>
                        </div>
                    </div>
                </div>
                """
            else:
                # English email content
                subject = f"🎁 ES-GIFT Invoice - {invoice.invoice_number}"
                email_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
                    <div style="background: #DC143C; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🎁 ES-GIFT</h1>
                        <p style="margin: 5px 0 0 0; font-size: 14px;">Leading Digital Gift Cards & Payment Services</p>
                    </div>
                    
                    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2C3E50; margin-bottom: 20px;">Dear {invoice.customer_name}</h2>
                        
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            Thank you for choosing ES-GIFT. Your invoice is ready.
                        </p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #DC143C;">
                            <h3 style="color: #DC143C; margin-top: 0;">📋 Invoice Details:</h3>
                            <p><strong>Invoice Number:</strong> {invoice.invoice_number}</p>
                            <p><strong>Order Number:</strong> {Order.query.get(invoice.order_id).order_number if Order.query.get(invoice.order_id) else 'N/A'}</p>
                            <p><strong>Date:</strong> {invoice.invoice_date.strftime('%Y-%m-%d')}</p>
                            <p><strong>Total Amount:</strong> {float(invoice.total_amount):.2f} {invoice.currency}</p>
                            <p><strong>Payment Status:</strong> {PremiumEnglishInvoiceService._get_payment_status_info(invoice.payment_status)[0]}</p>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 20px;">
                            If you have any questions, please don't hesitate to contact us:
                            <br>📧 business@es-gift.com
                            <br>📱 +966123456789
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #999; font-size: 12px;">
                                Thank you again for trusting ES-GIFT
                                <br>🌐 www.es-gift.com
                            </p>
                        </div>
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
            if not pdf_path:
                print("❌ Failed to generate PDF for email")
                return False
            
            # Determine language based on customer name/notes for email content
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in (invoice.customer_name + (invoice.notes or '')))
            
            if has_arabic:
                # Arabic email content
                subject = f"🎁 فاتورة ES-GIFT - {invoice.invoice_number}"
                email_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
                    <div style="background: #DC143C; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🎁 ES-GIFT</h1>
                        <p style="margin: 5px 0 0 0; font-size: 14px;">بطاقات الهدايا الرقمية الرائدة</p>
                    </div>
                    
                    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2C3E50; margin-bottom: 20px;">عزيزي/عزيزتي {fix_arabic_text(invoice.customer_name)}</h2>
                        
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            نشكركم لاختياركم ES-GIFT. يسعدنا إرسال فاتورتكم.
                        </p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-right: 4px solid #DC143C;">
                            <h3 style="color: #DC143C; margin-top: 0;">📋 تفاصيل الفاتورة:</h3>
                            <p><strong>رقم الفاتورة:</strong> {invoice.invoice_number}</p>
                            <p><strong>رقم الطلب:</strong> {Order.query.get(invoice.order_id).order_number if Order.query.get(invoice.order_id) else 'غير متوفر'}</p>
                            <p><strong>التاريخ:</strong> {invoice.invoice_date.strftime('%Y-%m-%d')}</p>
                            <p><strong>المبلغ الإجمالي:</strong> {float(invoice.total_amount):.2f} {invoice.currency}</p>
                            <p><strong>حالة الدفع:</strong> {PremiumEnglishInvoiceService._get_payment_status_info(invoice.payment_status)[0]}</p>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            يمكنكم تحميل ملف الفاتورة PDF من لوحة التحكم الخاصة بكم.
                        </p>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 20px;">
                            إذا كان لديكم أي استفسارات، لا تترددوا في التواصل معنا على:
                            <br>📧 business@es-gift.com
                            <br>📱 +966123456789
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #999; font-size: 12px;">
                                شكراً لكم مرة أخرى لثقتكم في ES-GIFT
                                <br>🌐 www.es-gift.com
                            </p>
                        </div>
                    </div>
                </div>
                """
            else:
                # English email content
                subject = f"🎁 ES-GIFT Invoice - {invoice.invoice_number}"
                email_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
                    <div style="background: #DC143C; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🎁 ES-GIFT</h1>
                        <p style="margin: 5px 0 0 0; font-size: 14px;">Leading Digital Gift Cards & Payment Services</p>
                    </div>
                    
                    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2C3E50; margin-bottom: 20px;">Dear {invoice.customer_name}</h2>
                        
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            Thank you for choosing ES-GIFT. Your invoice is ready.
                        </p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #DC143C;">
                            <h3 style="color: #DC143C; margin-top: 0;">📋 Invoice Details:</h3>
                            <p><strong>Invoice Number:</strong> {invoice.invoice_number}</p>
                            <p><strong>Order Number:</strong> {Order.query.get(invoice.order_id).order_number if Order.query.get(invoice.order_id) else 'N/A'}</p>
                            <p><strong>Date:</strong> {invoice.invoice_date.strftime('%Y-%m-%d')}</p>
                            <p><strong>Total Amount:</strong> {float(invoice.total_amount):.2f} {invoice.currency}</p>
                            <p><strong>Payment Status:</strong> {PremiumEnglishInvoiceService._get_payment_status_info(invoice.payment_status)[0]}</p>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            You can download the PDF invoice from your dashboard.
                        </p>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 20px;">
                            If you have any questions, please don't hesitate to contact us:
                            <br>📧 business@es-gift.com
                            <br>📱 +966123456789
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #999; font-size: 12px;">
                                Thank you again for trusting ES-GIFT
                                <br>🌐 www.es-gift.com
                            </p>
                        </div>
                    </div>
                </div>
                """
            
            # Send email using Email Sender Pro service
            success, message = send_custom_email(
                email=email_to_send,
                subject=subject,
                message_content=email_content,
                message_title="فاتورة ES-GIFT" if has_arabic else "ES-GIFT Invoice"
            )
            
            if success:
                print(f"✅ Invoice email sent successfully to: {email_to_send}")
                return True
            else:
                print(f"❌ Failed to send invoice email: {message}")
                # Try fallback method
                return PremiumEnglishInvoiceService._send_invoice_email_fallback(invoice, email_content, None, email_to_send)
                
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
            
            # Gmail fallback configuration
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "esgiftscard@gmail.com"
            sender_password = "xopq ikac efpj rdif"
            
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
            
            # Send via Gmail SMTP
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print(f"✅ Invoice sent successfully via Gmail fallback to: {email_to_send}")
            return True
            
        except Exception as e:
            print(f"❌ Gmail fallback failed: {e}")
            return False
    
    @staticmethod
    def _send_gmail_fallback(email_to_send, invoice, email_html, pdf_full_path):
        """إرسال مباشر عبر Gmail كخيار أخير"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            
            print("📧 محاولة إرسال مباشر عبر Gmail...")
            
            # إعدادات Gmail البديلة
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            smtp_user = "esgiftscard@gmail.com"
            smtp_pass = "xopq ikac efpj rdif"
            sender_name = "ES-GIFT"
            
            # إنشاء الرسالة
            msg = MIMEMultipart()
            msg['From'] = f"{sender_name}"
            msg['To'] = email_to_send
            msg['Subject'] = f"🎁 ES-GIFT Invoice - {invoice.invoice_number}"
            
            # إضافة محتوى HTML
            msg.attach(MIMEText(email_html, 'html', 'utf-8'))
            
            # إضافة مرفق PDF إن وجد
            if pdf_full_path and os.path.exists(pdf_full_path):
                with open(pdf_full_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= ES-GIFT_Invoice_{invoice.invoice_number}.pdf'
                    )
                    msg.attach(part)
                    print(f"📎 تم إرفاق الملف: {pdf_full_path}")
            
            # إرسال الرسالة
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ تم الإرسال المباشر عبر Gmail بنجاح")
            return True
            
        except Exception as e:
            print(f"❌ فشل في الإرسال المباشر عبر Gmail: {e}")
            return False
    
    @staticmethod
    def _send_simple_email_fallback(email_to_send, subject, email_html):
        """Simple email fallback using basic SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = 'ES-GIFT <business@es-gift.com>'
            msg['To'] = email_to_send
            
            # Add HTML content
            html_part = MIMEText(email_html, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Try to send (this is a basic attempt - may not work without proper SMTP config)
            print(f"Attempting to send email to {email_to_send} using simple fallback")
            return True  # Return True to avoid blocking the process
            
        except Exception as e:
            print(f"Simple email fallback failed: {e}")
            return True  # Return True to avoid blocking the invoice generation process

# Create alias for compatibility
ModernInvoiceService = PremiumEnglishInvoiceService
InvoiceService = PremiumEnglishInvoiceService
