# -*- coding: utf-8 -*-
"""
خدمة إرسال أكواد المنتجات عبر البريد الإلكتروني - ES-GIFT
=======================================================
"""

import os
import io
import pandas as pd
from datetime import datetime
# from clean_unified_email_service import UnifiedEmailService
# الخدمة البديلة المؤقتة
class UnifiedEmailService:
    def send_product_codes_email(self, recipient_email, products_data):
        print(f"Product codes would be sent to {recipient_email}")
        return {'success': True, 'message': 'Email sent'}
import logging

logger = logging.getLogger(__name__)

class ProductCodeEmailService:
    """خدمة إرسال أكواد المنتجات عبر البريد الإلكتروني"""
    
    def __init__(self):
        """تهيئة الخدمة"""
        self.email_service = UnifiedEmailService()
    
    def send_product_codes_email(self, order_data, product_codes):
        """إرسال أكواد المنتجات عبر البريد الإلكتروني"""
        try:
            customer_email = order_data.get('customer_email')
            customer_name = order_data.get('customer_name', 'عزيزنا العميل')
            order_number = order_data.get('order_number', 'غير محدد')
            
            if not customer_email:
                return False, "عنوان البريد الإلكتروني غير محدد", None
            
            # إنشاء محتوى HTML للبريد
            html_content = self._create_email_html(order_data, product_codes)
            
            # إنشاء ملف Excel
            excel_file, saved_file_path = self._create_excel_file(order_data, product_codes)
            
            # إرسال البريد مع المرفق
            subject = f"🎁 أكواد طلبك #{order_number} - ES-GIFT"
            
            attachments = []
            if excel_file:
                filename = f"ES-Gift_Order_{order_number}_Codes.xlsx"
                attachments.append({
                    'filename': filename,
                    'content': excel_file.getvalue(),
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
            
            success = self.email_service.send_email(
                customer_email, 
                subject, 
                html_content,
                attachments
            )
            
            if success:
                logger.info(f"تم إرسال أكواد الطلب #{order_number} بنجاح إلى {customer_email}")
                return True, f"تم إرسال أكواد المنتجات إلى {customer_email} بنجاح", saved_file_path
            else:
                return False, "فشل في إرسال البريد الإلكتروني", None
                
        except Exception as e:
            error_msg = f"خطأ في إرسال أكواد المنتجات: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def _create_email_html(self, order_data, product_codes):
        """إنشاء محتوى HTML للبريد"""
        customer_name = order_data.get('customer_name', 'عزيزنا العميل')
        order_number = order_data.get('order_number', 'غير محدد')
        order_date = order_data.get('order_date', datetime.now().strftime('%Y-%m-%d'))
        total_amount = order_data.get('total_amount', '0')
        
        # إنشاء قائمة الأكواد
        codes_html = ""
        for i, code in enumerate(product_codes, 1):
            codes_html += f"""
            <div style="background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 8px; border-right: 4px solid #FF0033;">
                <div style="font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px;">
                    🎮 كود رقم {i}
                </div>
                <div style="font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; 
                           color: #FF0033; background: white; padding: 10px; border-radius: 5px; text-align: center;">
                    {code}
                </div>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>أكواد المنتجات - ES-GIFT</title>
        </head>
        <body style="font-family: Arial, sans-serif; direction: rtl; background-color: #f5f5f5; margin: 0; padding: 20px;">
            
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #FF0033 0%, #FF3366 100%); padding: 40px 30px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 2.5em;">🎁 ES-GIFT</h1>
                    <p style="margin: 15px 0 0 0; font-size: 1.3em; opacity: 0.9;">أكواد منتجاتك جاهزة!</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333; margin-bottom: 25px; font-size: 1.8em;">🎉 مبروك! أكوادك جاهزة!</h2>
                    
                    <p style="font-size: 18px; line-height: 1.8; color: #555; margin-bottom: 20px;">
                        مرحباً <strong style="color: #FF0033;">{customer_name}</strong>,
                    </p>
                    
                    <p style="font-size: 16px; line-height: 1.7; color: #666; margin-bottom: 30px;">
                        🎊 نسعد بإبلاغك أن أكواد طلبك قد تم تجهيزها بنجاح! إليك التفاصيل:
                    </p>
                    
                    <!-- Order Info -->
                    <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; border-right: 4px solid #FF0033; margin: 30px 0;">
                        <h3 style="color: #FF0033; margin-top: 0;">📋 تفاصيل الطلب:</h3>
                        <p style="margin: 5px 0; color: #666;"><strong>رقم الطلب:</strong> #{order_number}</p>
                        <p style="margin: 5px 0; color: #666;"><strong>تاريخ الطلب:</strong> {order_date}</p>
                        <p style="margin: 5px 0; color: #666;"><strong>المجموع:</strong> {total_amount} ريال</p>
                        <p style="margin: 5px 0; color: #666;"><strong>عدد الأكواد:</strong> {len(product_codes)}</p>
                    </div>
                    
                    <!-- Product Codes -->
                    <div style="margin: 30px 0;">
                        <h3 style="color: #333; margin-bottom: 20px;">🔑 أكواد منتجاتك:</h3>
                        {codes_html}
                    </div>
                    
                    <!-- Instructions -->
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 30px 0;">
                        <h4 style="color: #856404; margin-top: 0;">📝 تعليمات مهمة:</h4>
                        <ul style="color: #856404; margin: 10px 0; padding-right: 20px;">
                            <li>احتفظ بهذه الأكواد في مكان آمن</li>
                            <li>لا تشارك الأكواد مع أي شخص آخر</li>
                            <li>استخدم الأكواد قبل انتهاء صلاحيتها</li>
                            <li>في حالة وجود مشكلة، تواصل معنا فوراً</li>
                        </ul>
                    </div>
                    
                    <!-- Excel File Notice -->
                    <div style="background: #e3f2fd; border: 1px solid #90caf9; padding: 20px; border-radius: 8px; margin: 30px 0;">
                        <p style="color: #1565c0; margin: 0; text-align: center;">
                            📎 تم إرفاق ملف Excel يحتوي على جميع الأكواد للاحتفاظ بها
                        </p>
                    </div>
                    
                    <p style="font-size: 14px; color: #888; text-align: center; margin-top: 30px;">
                        شكراً لثقتك في ES-GIFT! نتمنى لك تجربة ممتعة 🎉
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #f8f9fa; padding: 25px 30px; text-align: center; border-top: 1px solid #eee;">
                    <p style="margin: 0 0 10px 0; color: #FF0033; font-weight: bold; font-size: 16px;">
                        🎁 ES-GIFT
                    </p>
                    <p style="margin: 0; color: #888; font-size: 14px;">
                        وجهتك الموثوقة للبطاقات الرقمية والهدايا الإلكترونية
                    </p>
                </div>
                
            </div>
            
        </body>
        </html>
        """
        
        return html_content
    
    def _create_excel_file(self, order_data, product_codes):
        """إنشاء ملف Excel للأكواد"""
        try:
            # إنشاء DataFrame
            data = []
            for i, code in enumerate(product_codes, 1):
                data.append({
                    'الرقم': i,
                    'الكود': code,
                    'رقم الطلب': order_data.get('order_number', 'غير محدد'),
                    'تاريخ الطلب': order_data.get('order_date', datetime.now().strftime('%Y-%m-%d')),
                    'اسم العميل': order_data.get('customer_name', 'غير محدد'),
                    'حالة الكود': 'جاهز للاستخدام'
                })
            
            df = pd.DataFrame(data)
            
            # إنشاء ملف Excel في الذاكرة
            excel_file = io.BytesIO()
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='أكواد المنتجات', index=False)
                
                # تنسيق الجدول
                worksheet = writer.sheets['أكواد المنتجات']
                worksheet.sheet_state = 'visible'  # التأكد من أن الورقة مرئية
                
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            excel_file.seek(0)
            
            # حفظ نسخة على القرص (اختياري)
            saved_file_path = None
            try:
                excel_dir = os.path.join(os.getcwd(), 'static', 'order_files')
                os.makedirs(excel_dir, exist_ok=True)
                
                filename = f"Order_{order_data.get('order_number', 'Unknown')}_Codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                saved_file_path = os.path.join(excel_dir, filename)
                
                with open(saved_file_path, 'wb') as f:
                    f.write(excel_file.getvalue())
                    
                logger.info(f"تم حفظ ملف Excel: {saved_file_path}")
            except Exception as e:
                logger.warning(f"لم يتم حفظ ملف Excel على القرص: {str(e)}")
            
            return excel_file, saved_file_path
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء ملف Excel: {str(e)}")
            return None, None

# إنشاء instance عام للاستخدام
product_code_email_service = ProductCodeEmailService()
