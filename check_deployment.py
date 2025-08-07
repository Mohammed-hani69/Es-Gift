#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص نشر تطبيق ES-GIFT
===================
"""

import os
import sys
import subprocess
import importlib.util

def check_python():
    """فحص إصدار Python"""
    print("🐍 فحص Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} قديم جداً. يُطلب Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_virtual_env():
    """فحص البيئة الافتراضية"""
    print("📦 فحص البيئة الافتراضية...")
    if not os.path.exists('venv'):
        print("❌ البيئة الافتراضية غير موجودة")
        return False
    print("✅ البيئة الافتراضية موجودة")
    return True

def check_requirements():
    """فحص ملف المتطلبات"""
    print("📋 فحص المتطلبات...")
    if not os.path.exists('requirements.txt'):
        print("❌ ملف requirements.txt غير موجود")
        return False
    
    # قراءة المتطلبات
    with open('requirements.txt', 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"✅ تم العثور على {len(requirements)} متطلب")
    return True

def check_main_files():
    """فحص الملفات الرئيسية"""
    print("📁 فحص الملفات الرئيسية...")
    
    required_files = [
        'app.py',
        'wsgi.py',
        'config.py',
        'models.py',
        'routes.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"  ✅ {file}")
    
    if missing_files:
        print(f"❌ ملفات مفقودة: {', '.join(missing_files)}")
        return False
    
    return True

def check_app_import():
    """فحص إمكانية استيراد التطبيق"""
    print("🔄 فحص استيراد التطبيق...")
    
    try:
        # إضافة المسار الحالي
        sys.path.insert(0, os.getcwd())
        
        # محاولة استيراد app
        from app import app
        print("✅ تم استيراد app بنجاح")
        
        # محاولة استيراد wsgi
        from wsgi import application
        print("✅ تم استيراد wsgi بنجاح")
        
        return True
        
    except ImportError as e:
        print(f"❌ خطأ في الاستيراد: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False

def check_directories():
    """فحص المجلدات المطلوبة"""
    print("📂 فحص المجلدات...")
    
    required_dirs = [
        'instance',
        'static',
        'templates'
    ]
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"⚠️ مجلد مفقود: {dir_name}")
            os.makedirs(dir_name, exist_ok=True)
            print(f"✅ تم إنشاء {dir_name}")
        else:
            print(f"✅ {dir_name}")
    
    return True

def check_gunicorn_command():
    """فحص أمر Gunicorn"""
    print("🚀 فحص أمر Gunicorn...")
    
    test_commands = [
        "gunicorn --check-config wsgi:application",
        "gunicorn --check-config app:app"
    ]
    
    for cmd in test_commands:
        try:
            result = subprocess.run(
                cmd.split(), 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {cmd} - صحيح")
                return True
            else:
                print(f"⚠️ {cmd} - خطأ: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"⚠️ {cmd} - انتهت المهلة الزمنية")
        except FileNotFoundError:
            print("❌ Gunicorn غير مثبت")
            return False
        except Exception as e:
            print(f"❌ خطأ في الأمر: {e}")
    
    return False

def main():
    """الدالة الرئيسية"""
    print("🔍 فحص نشر تطبيق ES-GIFT")
    print("=" * 40)
    
    checks = [
        ("Python", check_python),
        ("البيئة الافتراضية", check_virtual_env),
        ("المتطلبات", check_requirements),
        ("الملفات الرئيسية", check_main_files),
        ("المجلدات", check_directories),
        ("استيراد التطبيق", check_app_import),
        ("أمر Gunicorn", check_gunicorn_command)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ خطأ في {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 40)
    print("📊 نتائج الفحص:")
    print("=" * 40)
    
    passed = 0
    for name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{status} - {name}")
        if result:
            passed += 1
    
    print(f"\n📈 النتيجة النهائية: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 جميع الفحوصات نجحت! التطبيق جاهز للنشر")
        print("\n🚀 لتشغيل التطبيق:")
        print("gunicorn -w 4 -b 127.0.0.1:8000 wsgi:application")
    else:
        print("⚠️ بعض الفحوصات فشلت. يرجى إصلاح المشاكل قبل النشر")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
