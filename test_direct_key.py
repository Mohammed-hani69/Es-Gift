#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار مباشر لمفتاح Brevo API
"""

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def test_direct_api_key():
    """اختبار مباشر للمفتاح"""
    
    # المفتاح المباشر الذي نجح في الاختبار السابق
    api_key = "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"
    
    print(f"🔑 اختبار المفتاح: {api_key[:20]}...{api_key[-10:]}")
    
    try:
        # إعداد API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        
        # إنشاء API instance
        api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # الحصول على معلومات الحساب
        api_response = api_instance.get_account()
        
        print("✅ المفتاح يعمل بنجاح!")
        print(f"📧 البريد الإلكتروني: {api_response.email}")
        print(f"🏢 الشركة: {api_response.company_name}")
        print(f"📊 خطة الاشتراك: {api_response.plan[0].type}")
        
        return True
        
    except ApiException as e:
        print(f"❌ فشل في اختبار المفتاح: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return False

if __name__ == "__main__":
    test_direct_api_key()
