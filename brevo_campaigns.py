#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الحملات البريدية لـ Brevo
==============================

هذا الملف يحتوي على جميع وظائف إنشاء وإدارة الحملات البريدية باستخدام Brevo API
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brevo_config import BrevoConfig

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CampaignRecipients:
    """بيانات مستقبلي الحملة"""
    list_ids: List[int] = None
    exclusion_list_ids: List[int] = None
    segment_ids: List[int] = None

@dataclass
class CampaignSettings:
    """إعدادات الحملة"""
    ab_testing: bool = False
    ip_warmup_enable: bool = False
    unsubscription_page_id: str = None
    update_form_id: str = None

class BrevoCampaignService:
    """خدمة الحملات البريدية باستخدام Brevo"""
    
    def __init__(self):
        self.config = BrevoConfig
        self.base_url = self.config.BASE_URL
        self.headers = self.config.get_api_headers()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # التحقق من صحة الإعدادات
        is_valid, message = self.config.is_valid_config()
        if not is_valid:
            logger.error(f"خطأ في إعدادات Brevo: {message}")
            raise ValueError(f"إعدادات Brevo غير صحيحة: {message}")
        
        logger.info("تم تهيئة خدمة الحملات البريدية بنجاح")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Tuple[bool, Union[Dict, str]]:
        """إجراء طلب HTTP مع إعادة المحاولة"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                if method.lower() == 'get':
                    response = self.session.get(url, params=data)
                elif method.lower() == 'post':
                    response = self.session.post(url, json=data)
                elif method.lower() == 'put':
                    response = self.session.put(url, json=data)
                elif method.lower() == 'delete':
                    response = self.session.delete(url)
                else:
                    return False, f"طريقة HTTP غير مدعومة: {method}"
                
                if response.status_code in [200, 201, 204]:
                    try:
                        return True, response.json() if response.content else {}
                    except:
                        return True, {}
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        return False, error_data.get('message', 'خطأ في البيانات المرسلة')
                    except:
                        return False, "خطأ في البيانات المرسلة"
                elif response.status_code == 401:
                    return False, "API Key غير صالح"
                elif response.status_code == 402:
                    return False, "تم تجاوز حد الاستخدام"
                elif response.status_code == 404:
                    return False, "المورد غير موجود"
                else:
                    logger.warning(f"المحاولة {attempt + 1}: فشل الطلب - {response.status_code}")
                    if attempt < self.config.MAX_RETRIES - 1:
                        time.sleep(self.config.RETRY_DELAY)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"المحاولة {attempt + 1}: خطأ في الشبكة - {str(e)}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY)
        
        return False, "فشل في إجراء الطلب بعد عدة محاولات"
    
    def create_email_campaign(self, 
                             name: str,
                             subject: str,
                             html_content: str,
                             sender: Dict = None,
                             recipients: CampaignRecipients = None,
                             scheduled_at: str = None,
                             campaign_type: str = "classic",
                             text_content: str = None,
                             reply_to: str = None,
                             to_field: str = None,
                             tag: str = None,
                             settings: CampaignSettings = None) -> Tuple[bool, Union[Dict, str]]:
        """
        إنشاء حملة بريدية جديدة
        
        Args:
            name: اسم الحملة
            subject: موضوع الرسالة
            html_content: محتوى HTML
            sender: بيانات المرسل
            recipients: مستقبلي الحملة
            scheduled_at: موعد الإرسال المجدول (YYYY-MM-DD HH:MM:SS)
            campaign_type: نوع الحملة (classic, trigger, etc.)
            text_content: محتوى نصي
            reply_to: بريد الرد
            to_field: حقل المستقبل
            tag: علامة للحملة
            settings: إعدادات إضافية
        
        Returns:
            Tuple[bool, Union[Dict, str]]: (نجح الإنشاء، البيانات/رسالة الخطأ)
        """
        try:
            # إعداد بيانات الحملة
            campaign_data = {
                "name": name,
                "subject": subject,
                "type": campaign_type,
                "htmlContent": html_content
            }
            
            # إعداد المرسل
            if sender:
                campaign_data["sender"] = sender
            else:
                campaign_data["sender"] = self.config.get_sender_info()
            
            # إعداد المستقبلين
            if recipients:
                recipients_data = {}
                if recipients.list_ids:
                    recipients_data["listIds"] = recipients.list_ids
                if recipients.exclusion_list_ids:
                    recipients_data["exclusionListIds"] = recipients.exclusion_list_ids
                if recipients.segment_ids:
                    recipients_data["segmentIds"] = recipients.segment_ids
                
                if recipients_data:
                    campaign_data["recipients"] = recipients_data
            
            # إعدادات إضافية
            if text_content:
                campaign_data["textContent"] = text_content
            
            if reply_to:
                campaign_data["replyTo"] = reply_to
            
            if to_field:
                campaign_data["toField"] = to_field
            
            if tag:
                campaign_data["tag"] = tag
            
            if scheduled_at:
                campaign_data["scheduledAt"] = scheduled_at
            
            # إعدادات متقدمة
            if settings:
                if settings.ab_testing:
                    campaign_data["abTesting"] = settings.ab_testing
                if settings.ip_warmup_enable:
                    campaign_data["ipWarmupEnable"] = settings.ip_warmup_enable
                if settings.unsubscription_page_id:
                    campaign_data["unsubscriptionPageId"] = settings.unsubscription_page_id
                if settings.update_form_id:
                    campaign_data["updateFormId"] = settings.update_form_id
            
            # إعدادات التتبع
            campaign_data.update({
                "header": f"[{self.config.COMPANY_INFO['name_ar']}] {subject}",
                "footer": f"تم الإرسال من {self.config.COMPANY_INFO['name_ar']}",
                "utmCampaign": name.replace(" ", "_").lower(),
                "params": {
                    "FNAME": "[FNAME,fallback=عزيزي العميل]",
                    "LNAME": "[LNAME,fallback=]"
                }
            })
            
            # إرسال الطلب
            success, response = self._make_request('POST', 'emailCampaigns', campaign_data)
            
            if success:
                logger.info(f"تم إنشاء الحملة بنجاح: {name}")
                return True, response
            else:
                logger.error(f"فشل في إنشاء الحملة: {response}")
                return False, response
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء الحملة: {str(e)}")
            return False, f"خطأ في إنشاء الحملة: {str(e)}"
    
    def send_campaign_now(self, campaign_id: int) -> Tuple[bool, str]:
        """إرسال حملة فوراً"""
        try:
            success, response = self._make_request('POST', f'emailCampaigns/{campaign_id}/sendNow')
            
            if success:
                logger.info(f"تم إرسال الحملة {campaign_id} بنجاح")
                return True, "تم إرسال الحملة بنجاح"
            else:
                logger.error(f"فشل في إرسال الحملة {campaign_id}: {response}")
                return False, response
                
        except Exception as e:
            logger.error(f"خطأ في إرسال الحملة: {str(e)}")
            return False, f"خطأ في إرسال الحملة: {str(e)}"
    
    def schedule_campaign(self, campaign_id: int, scheduled_at: str) -> Tuple[bool, str]:
        """جدولة حملة للإرسال في وقت محدد"""
        try:
            data = {"scheduledAt": scheduled_at}
            success, response = self._make_request('PUT', f'emailCampaigns/{campaign_id}', data)
            
            if success:
                logger.info(f"تم جدولة الحملة {campaign_id} للإرسال في {scheduled_at}")
                return True, f"تم جدولة الحملة للإرسال في {scheduled_at}"
            else:
                logger.error(f"فشل في جدولة الحملة {campaign_id}: {response}")
                return False, response
                
        except Exception as e:
            logger.error(f"خطأ في جدولة الحملة: {str(e)}")
            return False, f"خطأ في جدولة الحملة: {str(e)}"
    
    def get_campaigns(self, type_filter: str = None, status: str = None, 
                     start_date: str = None, end_date: str = None,
                     limit: int = 50, offset: int = 0) -> Tuple[bool, Union[List[Dict], str]]:
        """الحصول على قائمة الحملات"""
        try:
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if type_filter:
                params["type"] = type_filter
            if status:
                params["status"] = status
            if start_date:
                params["startDate"] = start_date
            if end_date:
                params["endDate"] = end_date
            
            success, response = self._make_request('GET', 'emailCampaigns', params)
            
            if success:
                campaigns = response.get('campaigns', [])
                logger.info(f"تم الحصول على {len(campaigns)} حملة")
                return True, campaigns
            else:
                logger.error(f"فشل في الحصول على الحملات: {response}")
                return False, response
                
        except Exception as e:
            logger.error(f"خطأ في الحصول على الحملات: {str(e)}")
            return False, f"خطأ في الحصول على الحملات: {str(e)}"
    
    def get_campaign_stats(self, campaign_id: int) -> Tuple[bool, Union[Dict, str]]:
        """الحصول على إحصائيات حملة"""
        try:
            success, response = self._make_request('GET', f'emailCampaigns/{campaign_id}')
            
            if success:
                logger.info(f"تم الحصول على إحصائيات الحملة {campaign_id}")
                return True, response
            else:
                logger.error(f"فشل في الحصول على إحصائيات الحملة {campaign_id}: {response}")
                return False, response
                
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات الحملة: {str(e)}")
            return False, f"خطأ في الحصول على إحصائيات الحملة: {str(e)}"
    
    def delete_campaign(self, campaign_id: int) -> Tuple[bool, str]:
        """حذف حملة"""
        try:
            success, response = self._make_request('DELETE', f'emailCampaigns/{campaign_id}')
            
            if success:
                logger.info(f"تم حذف الحملة {campaign_id}")
                return True, "تم حذف الحملة بنجاح"
            else:
                logger.error(f"فشل في حذف الحملة {campaign_id}: {response}")
                return False, response
                
        except Exception as e:
            logger.error(f"خطأ في حذف الحملة: {str(e)}")
            return False, f"خطأ في حذف الحملة: {str(e)}"
    
    def create_contact_list(self, name: str, folder_id: int = None) -> Tuple[bool, Union[Dict, str]]:
        """إنشاء قائمة جهات اتصال جديدة"""
        try:
            data = {"name": name}
            if folder_id:
                data["folderId"] = folder_id
            
            success, response = self._make_request('POST', 'contacts/lists', data)
            
            if success:
                logger.info(f"تم إنشاء قائمة الاتصال: {name}")
                return True, response
            else:
                logger.error(f"فشل في إنشاء قائمة الاتصال: {response}")
                return False, response
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء قائمة الاتصال: {str(e)}")
            return False, f"خطأ في إنشاء قائمة الاتصال: {str(e)}"
    
    def get_contact_lists(self, limit: int = 50, offset: int = 0) -> Tuple[bool, Union[List[Dict], str]]:
        """الحصول على قوائم جهات الاتصال"""
        try:
            params = {"limit": limit, "offset": offset}
            success, response = self._make_request('GET', 'contacts/lists', params)
            
            if success:
                lists = response.get('lists', [])
                logger.info(f"تم الحصول على {len(lists)} قائمة اتصال")
                return True, lists
            else:
                logger.error(f"فشل في الحصول على قوائم الاتصال: {response}")
                return False, response
                
        except Exception as e:
            logger.error(f"خطأ في الحصول على قوائم الاتصال: {str(e)}")
            return False, f"خطأ في الحصول على قوائم الاتصال: {str(e)}"


# إنشاء مثيل الخدمة
campaign_service = BrevoCampaignService()

# ========== دوال مساعدة للاستخدام السريع ==========

def create_promotional_campaign(name: str, subject: str, html_content: str, 
                               list_ids: List[int], scheduled_at: str = None) -> Tuple[bool, Union[Dict, str]]:
    """إنشاء حملة ترويجية"""
    recipients = CampaignRecipients(list_ids=list_ids)
    
    return campaign_service.create_email_campaign(
        name=name,
        subject=subject,
        html_content=html_content,
        recipients=recipients,
        scheduled_at=scheduled_at,
        tag="promotional"
    )

def create_newsletter_campaign(name: str, subject: str, html_content: str,
                              newsletter_list_id: int, scheduled_at: str = None) -> Tuple[bool, Union[Dict, str]]:
    """إنشاء حملة نشرة إخبارية"""
    recipients = CampaignRecipients(list_ids=[newsletter_list_id])
    
    return campaign_service.create_email_campaign(
        name=name,
        subject=subject,
        html_content=html_content,
        recipients=recipients,
        scheduled_at=scheduled_at,
        tag="newsletter"
    )

def create_es_gift_campaign(campaign_name: str, campaign_subject: str, 
                           campaign_content: str, target_lists: List[int] = None) -> Tuple[bool, Union[Dict, str]]:
    """إنشاء حملة خاصة بـ ES-GIFT"""
    
    # الحصول على القوائم المتاحة أولاً
    success, available_lists = campaign_service.get_contact_lists()
    if not success or not available_lists:
        return False, "لا توجد قوائم اتصال متاحة"
    
    # استخدام أول قائمة متاحة إذا لم يتم تحديد قوائم
    if not target_lists:
        target_lists = [available_lists[0]['id']]
    
    # التحقق من وجود القوائم المحددة
    available_ids = [lst['id'] for lst in available_lists]
    valid_lists = [lst_id for lst_id in target_lists if lst_id in available_ids]
    
    if not valid_lists:
        # استخدام أول قائمة متاحة كبديل
        valid_lists = [available_lists[0]['id']]
    
    # إنشاء محتوى HTML مخصص لـ ES-GIFT
    branded_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{campaign_subject}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                direction: rtl;
                margin: 0;
                padding: 0;
                background-color: #f8f9fa;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, {BrevoConfig.BRAND_COLORS['primary']}, {BrevoConfig.BRAND_COLORS['accent']});
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .content {{
                padding: 30px 20px;
                line-height: 1.6;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
            .button {{
                display: inline-block;
                background-color: {BrevoConfig.BRAND_COLORS['primary']};
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{BrevoConfig.COMPANY_INFO['name_ar']}</h1>
                <p>متجر البطائق والهدايا الرقمية</p>
            </div>
            <div class="content">
                {campaign_content}
            </div>
            <div class="footer">
                <p>© 2025 {BrevoConfig.COMPANY_INFO['name_ar']} - جميع الحقوق محفوظة</p>
                <p>الموقع: {BrevoConfig.COMPANY_INFO['website']} | الدعم: {BrevoConfig.COMPANY_INFO['support_email']}</p>
                <p><a href="{{{{ unsubscribe }}}}">إلغاء الاشتراك</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # إنشاء الحملة
    recipients = CampaignRecipients(list_ids=valid_lists)
    
    return campaign_service.create_email_campaign(
        name=campaign_name,
        subject=campaign_subject,
        html_content=branded_content,
        recipients=recipients,
        tag="es-gift-campaign"
    )

# ========== دوال إدارة الحملات ==========

def get_all_campaigns() -> Tuple[bool, Union[List[Dict], str]]:
    """الحصول على جميع الحملات"""
    return campaign_service.get_campaigns()

def send_campaign_immediately(campaign_id: int) -> Tuple[bool, str]:
    """إرسال حملة فوراً"""
    return campaign_service.send_campaign_now(campaign_id)

def schedule_campaign_later(campaign_id: int, send_datetime: str) -> Tuple[bool, str]:
    """جدولة حملة للإرسال لاحقاً"""
    return campaign_service.schedule_campaign(campaign_id, send_datetime)

def get_campaign_statistics(campaign_id: int) -> Tuple[bool, Union[Dict, str]]:
    """الحصول على إحصائيات حملة"""
    return campaign_service.get_campaign_stats(campaign_id)

# ========== تصدير الوظائف ==========
__all__ = [
    'BrevoCampaignService',
    'CampaignRecipients', 
    'CampaignSettings',
    'campaign_service',
    'create_promotional_campaign',
    'create_newsletter_campaign',
    'create_es_gift_campaign',
    'get_all_campaigns',
    'send_campaign_immediately',
    'schedule_campaign_later',
    'get_campaign_statistics'
]
