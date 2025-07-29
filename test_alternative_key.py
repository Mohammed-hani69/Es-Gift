#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار المفتاح البديل
"""

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def test_alternative_key():
    """اختبار المفتاح البديل"""
    
    # المفتاح البديل الموجود في test_latest_brevo_key.py
    api_key = "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"
    
    print(f"🔑 اختبار المفتاح البديل: {api_key[:20]}...{api_key[-10:]}")
    
    try:
        # إعداد API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        
        # إنشاء API instance
        api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # الحصول على معلومات الحساب
        api_response = api_instance.get_account()
        
        print("✅ المفتاح البديل يعمل بنجاح!")
        print(f"📧 البريد الإلكتروني: {api_response.email}")
        print(f"🏢 الشركة: {api_response.company_name}")
        print(f"📊 خطة الاشتراك: {api_response.plan[0].type}")
        
        return True, api_key
        
    except ApiException as e:
        print(f"❌ فشل في اختبار المفتاح البديل: {e}")
        return False, None
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return False, None

if __name__ == "__main__":
    success, key = test_alternative_key()
    if success:
        print(f"\n🎉 استخدم هذا المفتاح: {key}")
    else:
        print("\n❌ المفتاح البديل لا يعمل أيضاً")
