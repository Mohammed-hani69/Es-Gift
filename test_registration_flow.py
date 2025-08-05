#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار تدفق التسجيل والتحقق من البريد الإلكتروني
===========================================

هذا ملف اختبار لتجربة عملية التسجيل والتحقق من الكود.
"""

import sys
import os

# إضافة مجلد المشروع لمسار Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_email_service():
    """اختبار خدمة البريد الإلكتروني"""
    try:
        from send_by_hostinger import test_email_connection
        
        print("🔍 اختبار الاتصال بخادم البريد الإلكتروني...")
        success, message = test_email_connection()
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            
        return success
        
    except Exception as e:
        print(f"❌ خطأ في اختبار خدمة البريد: {str(e)}")
        return False

def test_verification_service():
    """اختبار خدمة التحقق"""
    try:
        from email_pro_verification_service import send_user_verification_code, verify_user_code
        
        print("\n🔐 اختبار خدمة التحقق...")
        
        # اختبار إرسال كود تحقق تجريبي
        test_email = "test@example.com"
        test_name = "مستخدم تجريبي"
        
        print(f"📧 محاولة إرسال كود تحقق إلى: {test_email}")
        success, message, code = send_user_verification_code(test_email, test_name)
        
        if success:
            print(f"✅ {message}")
            print(f"🔑 كود التحقق: {code}")
            
            # اختبار التحقق من الكود
            print(f"🔍 اختبار التحقق من الكود...")
            verify_success, verify_message = verify_user_code(test_email, code)
            
            if verify_success:
                print(f"✅ {verify_message}")
            else:
                print(f"❌ {verify_message}")
                
            return verify_success
        else:
            print(f"❌ {message}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في اختبار خدمة التحقق: {str(e)}")
        return False

def test_routes():
    """اختبار تحميل المسارات"""
    try:
        print("\n🌐 اختبار تحميل المسارات...")
        
        import routes
        print("✅ تم تحميل routes بنجاح")
        
        import auth_routes
        print("✅ تم تحميل auth_routes بنجاح")
        
        import email_pro_verification_service
        print("✅ تم تحميل email_pro_verification_service بنجاح")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تحميل المسارات: {str(e)}")
        return False

def main():
    """تشغيل جميع الاختبارات"""
    print("🚀 بدء اختبار نظام التسجيل والتحقق")
    print("=" * 50)
    
    results = []
    
    # اختبار تحميل المسارات
    results.append(test_routes())
    
    # اختبار خدمة البريد الإلكتروني
    results.append(test_email_service())
    
    # اختبار خدمة التحقق (قد يفشل بسبب عدم وجود بريد حقيقي)
    # results.append(test_verification_service())
    
    print("\n" + "=" * 50)
    print("📊 نتائج الاختبارات:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ تم اجتياز جميع الاختبارات ({passed}/{total})")
        print("\n🎉 النظام جاهز للاستخدام!")
    else:
        print(f"⚠️  تم اجتياز {passed} من {total} اختبارات")
        print("\n🔧 يرجى مراجعة الأخطاء أعلاه")

if __name__ == "__main__":
    main()
