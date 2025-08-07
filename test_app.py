#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار سريع لتطبيق ES-GIFT
==========================
"""

import sys
import os

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """اختبار الاستيرادات الأساسية"""
    print("🔄 اختبار الاستيرادات الأساسية...")
    
    try:
        # اختبار Flask
        import flask
        print(f"✅ Flask {flask.__version__}")
        
        # اختبار SQLAlchemy
        import flask_sqlalchemy
        print("✅ Flask-SQLAlchemy")
        
        # اختبار Gunicorn
        import gunicorn
        print(f"✅ Gunicorn {gunicorn.__version__}")
        
        return True
    except ImportError as e:
        print(f"❌ خطأ في الاستيراد: {e}")
        return False

def test_app_creation():
    """اختبار إنشاء التطبيق"""
    print("🏗️ اختبار إنشاء التطبيق...")
    
    try:
        from app import create_app, app
        
        # اختبار إنشاء التطبيق
        test_app = create_app()
        print("✅ تم إنشاء التطبيق بنجاح")
        
        # اختبار الـ app object الجاهز
        print(f"✅ app object متوفر: {type(app)}")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء التطبيق: {e}")
        return False

def test_wsgi():
    """اختبار WSGI"""
    print("🌐 اختبار WSGI...")
    
    try:
        from wsgi import application
        print(f"✅ WSGI application متوفر: {type(application)}")
        return True
    except Exception as e:
        print(f"❌ خطأ في WSGI: {e}")
        return False

def test_routes():
    """اختبار المسارات"""
    print("🛣️ اختبار المسارات...")
    
    try:
        from app import app
        
        with app.app_context():
            # جلب قائمة المسارات
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append(str(rule))
            
            print(f"✅ تم العثور على {len(routes)} مسار")
            
            # عرض بعض المسارات المهمة
            important_routes = ['/', '/admin', '/login']
            for route in important_routes:
                if any(route in r for r in routes):
                    print(f"  ✅ {route}")
                else:
                    print(f"  ⚠️ {route} غير موجود")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في اختبار المسارات: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🧪 اختبار تطبيق ES-GIFT")
    print("=" * 30)
    
    tests = [
        ("الاستيرادات الأساسية", test_basic_imports),
        ("إنشاء التطبيق", test_app_creation),
        ("WSGI", test_wsgi),
        ("المسارات", test_routes)
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n📋 {name}:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
    
    print("\n" + "=" * 30)
    print(f"📊 النتيجة: {passed}/{len(tests)} اختبار نجح")
    
    if passed == len(tests):
        print("🎉 جميع الاختبارات نجحت!")
        print("\n🚀 الأوامر للتشغيل:")
        print("تطوير: python3 app.py")
        print("إنتاج: gunicorn -w 4 -b 127.0.0.1:8000 wsgi:application")
    else:
        print("⚠️ بعض الاختبارات فشلت")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
