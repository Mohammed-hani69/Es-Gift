"""
Premium Deposit Invoice Service - Professional ES-Gift Design
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
                               Image, PageBreak, KeepTogether, Frame, PageTemplate)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line
from reportlab.graphics import renderPDF
from flask import current_app
from datetime import datetime
import os

class PremiumDepositInvoiceService:
    """Premium PDF Invoice Service for Deposit Requests with Enhanced ES-Gift Design"""
    
    def __init__(self):
        """Initialize the premium service"""
        self.font_name = 'Helvetica'
        self.brand_color = colors.HexColor('#dc143c')  # ES-Gift primary red
        self.accent_color = colors.HexColor('#e74c3c')  # Lighter red accent
        self.white_color = colors.white
        self.text_color = colors.HexColor('#2c3e50')  # Dark gray for text
        self.light_bg = colors.HexColor('#f8f9fa')  # Light background for alternating rows
        self.success_color = colors.HexColor('#27ae60')  # Green for positive amounts
    
    def _create_separator_line(self):
        """Create decorative separator line"""
        drawing = Drawing(0.6*inch, 60)
        # Vertical decorative line
        drawing.add(Line(0.3*inch, 10, 0.3*inch, 50, strokeColor=colors.white, strokeWidth=2))
        # Small decorative circles
        drawing.add(Circle(0.3*inch, 30, 3, fillColor=colors.white, strokeColor=None))
        return drawing
    
    def _create_header_graphic(self, width, height):
        """Create premium ES-Gift header graphic"""
        drawing = Drawing(width, height)
        
        # Enhanced background with gradient-like effect
        drawing.add(Rect(0, 0, width, height, 
                        fillColor=self.brand_color, 
                        strokeColor=None))
        
        # Add subtle accent line at bottom
        drawing.add(Rect(0, 0, width, 3, 
                        fillColor=self.accent_color, 
                        strokeColor=None))
        
        return drawing
    
    def _create_header_section(self, request_data):
        """Create professional ES-Gift header matching the template exactly"""
        # Create header with proper layout and spacing like the template
        header_data = [
            [
                # Left column - SALES INVOICE title with smaller font
                Paragraph('<para alignment="center" fontSize="18" fontName="Helvetica-Bold" textColor="white" spaceAfter="8">SALES INVOICE</para>', 
                         getSampleStyleSheet()['Normal']),
                # Right column - ES-GIFT brand with smaller fonts
                [
                    Paragraph('<para alignment="center" fontSize="16" fontName="Helvetica-Bold" textColor="white" spaceAfter="4">🎁 ES-GIFT</para>', 
                             getSampleStyleSheet()['Normal']),
                    Paragraph('<para alignment="center" fontSize="9" textColor="white" spaceAfter="4">Premium Digital Gift Cards</para>', 
                             getSampleStyleSheet()['Normal'])
                ]
            ]
        ]
        
        header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.brand_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Invoice title
            ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),  # Brand logo
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        return header_table
    
    def _create_customer_info_section(self, request_data):
        """Create customer information section matching template layout"""
        # Extract customer data
        user = request_data.user
        customer_id = user.id
        customer_name = user.full_name or user.email.split('@')[0]
        invoice_number = f"INV-{request_data.id:010d}"
        invoice_date = request_data.created_at.strftime('%d-%m-%Y')
        
        # Create info layout exactly like the template with smaller fonts
        info_data = [
            # Row 1 - Customer ID
            [
                '',
                '',
                Paragraph(f'<para alignment="left" fontSize="11" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="3">{customer_id}</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="left" fontSize="11" fontName="Helvetica" textColor="#34495e" spaceAfter="3">Customer ID:</para>', 
                         getSampleStyleSheet()['Normal'])
            ],
            # Row 2 - Customer name and invoice number  
            [
                Paragraph(f'<para alignment="left" fontSize="11" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="3">{invoice_number}</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="left" fontSize="11" fontName="Helvetica" textColor="#34495e" spaceAfter="3">Invoice No:</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph(f'<para alignment="left" fontSize="11" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="3">{customer_name}</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="left" fontSize="11" fontName="Helvetica" textColor="#34495e" spaceAfter="3">Customer Name:</para>', 
                         getSampleStyleSheet()['Normal'])
            ],
            # Row 3 - Date
            [
                '',
                '',
                Paragraph(f'<para alignment="left" fontSize="11" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="3">{invoice_date}</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="left" fontSize="11" fontName="Helvetica" textColor="#34495e" spaceAfter="3">Date:</para>', 
                         getSampleStyleSheet()['Normal'])
            ]
        ]
        
        info_table = Table(info_data, colWidths=[1.2*inch, 1.2*inch, 1.8*inch, 1.3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        return info_table
    
    def _create_items_table(self, request_data):
        """Create items table matching the template design exactly"""
        # Table header with smaller fonts and proper spacing
        header_data = [
            [
                Paragraph('<para alignment="center" fontSize="12" fontName="Helvetica-Bold" textColor="white" spaceAfter="2">#</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="center" fontSize="12" fontName="Helvetica-Bold" textColor="white" spaceAfter="2">Description</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="center" fontSize="12" fontName="Helvetica-Bold" textColor="white" spaceAfter="2">Qty</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="center" fontSize="12" fontName="Helvetica-Bold" textColor="white" spaceAfter="2">Price</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="center" fontSize="12" fontName="Helvetica-Bold" textColor="white" spaceAfter="2">Total</para>', 
                         getSampleStyleSheet()['Normal'])
            ]
        ]
        
        # Items data with proper formatting and smaller fonts
        items_data = []
        items_data.extend(header_data)
        
        # Add wallet deposit item with smaller fonts and padding
        item_description = f"Wallet Deposit - {request_data.currency_code} Credit"
        amount = float(request_data.amount)
        
        item_row = [
            Paragraph('<para alignment="center" fontSize="10" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="2">1</para>', 
                     getSampleStyleSheet()['Normal']),
            Paragraph(f'<para alignment="center" fontSize="10" fontName="Helvetica" textColor="#2c3e50" spaceAfter="2">{item_description}</para>', 
                     getSampleStyleSheet()['Normal']),
            Paragraph('<para alignment="center" fontSize="10" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="2">1</para>', 
                     getSampleStyleSheet()['Normal']),
            Paragraph(f'<para alignment="center" fontSize="10" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="2">{amount:.2f}</para>', 
                     getSampleStyleSheet()['Normal']),
            Paragraph(f'<para alignment="center" fontSize="10" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="2">{amount:.2f}</para>', 
                     getSampleStyleSheet()['Normal'])
        ]
        items_data.append(item_row)
        
        # Add a few empty rows for spacing like in template
        for i in range(3):
            empty_row = [
                Paragraph('<para alignment="center" fontSize="8" textColor="#bdc3c7" spaceAfter="2">-</para>', 
                         getSampleStyleSheet()['Normal']) for _ in range(5)
            ]
            items_data.append(empty_row)
        
        # Create table with proper column widths
        items_table = Table(items_data, colWidths=[0.5*inch, 3*inch, 0.8*inch, 1*inch, 1*inch])
        
        # Apply proper styling with better padding
        table_style = [
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.brand_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            
            # Content styling with smaller fonts
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, 1), 1, colors.black),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
            
            # Alternating backgrounds
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.98, 0.98, 0.98)]),
            
            # Better padding to prevent overlapping
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            
            # Highlight the actual item row
            ('BACKGROUND', (0, 1), (-1, 1), colors.Color(0.95, 0.98, 1.0)),
        ]
        
        items_table.setStyle(TableStyle(table_style))
        
        return items_table
    
    def _create_totals_section(self, request_data):
        """Create totals section exactly like the template"""
        amount = float(request_data.amount)
        tax = 0.00  # No tax applied
        total = amount + tax
        
        # Create totals layout matching template with smaller fonts
        totals_data = [
            # Price row
            [
                Paragraph(f'<para alignment="left" fontSize="11" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="2">{amount:.2f}</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="right" fontSize="11" fontName="Helvetica" textColor="#34495e" spaceAfter="2">Price</para>', 
                         getSampleStyleSheet()['Normal'])
            ],
            # Tax row  
            [
                Paragraph(f'<para alignment="left" fontSize="11" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="2">{tax:.2f}</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="right" fontSize="11" fontName="Helvetica" textColor="#34495e" spaceAfter="2">Tax</para>', 
                         getSampleStyleSheet()['Normal'])
            ],
            # Total row with background like template
            [
                Paragraph(f'<para alignment="left" fontSize="11" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="2">{total:.2f}</para>', 
                         getSampleStyleSheet()['Normal']),
                Paragraph('<para alignment="right" fontSize="11" fontName="Helvetica-Bold" textColor="#2c3e50" spaceAfter="2">Grand Total</para>', 
                         getSampleStyleSheet()['Normal'])
            ]
        ]
        
        totals_table = Table(totals_data, colWidths=[1.2*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            
            # Background for total row like in template
            ('BACKGROUND', (0, 2), (-1, 2), colors.Color(0.95, 0.95, 0.95)),
            ('TOPPADDING', (0, 2), (-1, 2), 8),
            ('BOTTOMPADDING', (0, 2), (-1, 2), 8),
        ]))
        
        return totals_table
    
    def _create_signature_image(self):
        """Create signature image from ES Pay logo"""
        try:
            # Path to the signature image
            signature_path = os.path.join('static', 'images', 'es pay llc.jpg')
            
            if os.path.exists(signature_path):
                # Create image with appropriate size for signature
                signature_img = Image(signature_path, width=120, height=100)
                return signature_img
            else:
                # Fallback if image not found
                print(f"Signature image not found at: {signature_path}")
                return Paragraph('<para alignment="center" fontSize="8" textColor="#7f8c8d">Signature not available</para>', 
                               getSampleStyleSheet()['Normal'])
                
        except Exception as e:
            print(f"Error loading signature image: {e}")
            # Fallback text
            return Paragraph('<para alignment="center" fontSize="8" textColor="#7f8c8d">_________________</para>', 
                           getSampleStyleSheet()['Normal'])
    
    def _create_notes_and_signature_section(self):
        """Create notes and signature section like the template"""
        # Layout matching the template exactly with smaller fonts
        notes_data = [
            [
                # Notes column with smaller fonts and better spacing
                [
                    Paragraph('<para alignment="left" fontSize="12" fontName="Helvetica-Bold" textColor="#dc143c" spaceAfter="6">Notes</para>', 
                             getSampleStyleSheet()['Normal']),
                    Paragraph('<para alignment="left" fontSize="9" textColor="#2c3e50" spaceAfter="3">• Digital wallet credit is non-refundable</para>', 
                             getSampleStyleSheet()['Normal']),
                    Paragraph('<para alignment="left" fontSize="9" textColor="#2c3e50" spaceAfter="3">• Please verify all invoice items are correct</para>', 
                             getSampleStyleSheet()['Normal'])
                ],
                # Signature column with company logo
                [
                    Paragraph('<para alignment="center" fontSize="10" fontName="Helvetica-Bold" textColor="#dc143c" spaceAfter="3"></para>', 
                             getSampleStyleSheet()['Normal']),
                    self._create_signature_image()
                ]
            ]
        ]
        
        notes_table = Table(notes_data, colWidths=[3.5*inch, 2.5*inch])
        notes_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Notes column
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Signature column
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return notes_table
    
    def generate_deposit_invoice_pdf(self, deposit_request):
        """Generate clean PDF invoice matching the template design"""
        try:
            # Setup file path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"es_gift_invoice_{deposit_request.id}_{timestamp}.pdf"
            invoices_dir = os.path.join('static', 'deposit_invoices')
            
            # Ensure directory exists
            os.makedirs(invoices_dir, exist_ok=True)
            
            file_path = os.path.join(invoices_dir, filename)
            
            # Setup PDF with proper margins
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                  rightMargin=20, leftMargin=20,
                                  topMargin=20, bottomMargin=20)
            
            story = []
            
            # Header section with reduced spacing
            header = self._create_header_section(deposit_request)
            story.append(header)
            story.append(Spacer(1, 12))
            
            # Customer information section
            customer_info = self._create_customer_info_section(deposit_request)
            story.append(customer_info)
            story.append(Spacer(1, 12))
            
            # Items table
            items_table = self._create_items_table(deposit_request)
            story.append(items_table)
            story.append(Spacer(1, 12))
            
            # Totals section (left-aligned like template)
            totals_section = self._create_totals_section(deposit_request)
            totals_wrapper = Table([[totals_section, '']], colWidths=[2.7*inch, 3.8*inch])
            totals_wrapper.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(totals_wrapper)
            story.append(Spacer(1, 12))
            
            # Notes and signature section
            notes_section = self._create_notes_and_signature_section()
            story.append(notes_section)
            story.append(Spacer(1, 8))
            
            # Thank you message with smaller font
            thanks_style = ParagraphStyle(
                'Thanks',
                parent=getSampleStyleSheet()['Normal'],
                fontSize=10,
                textColor=self.text_color,
                fontName='Helvetica-Bold',
                alignment=0  # Left alignment
            )
            story.append(Paragraph('Thank you', thanks_style))
            
            # Build PDF
            doc.build(story)
            
            print(f"Clean ES-Gift invoice created: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"Error creating ES-Gift invoice: {e}")
            raise e
