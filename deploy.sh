#!/bin/bash
# -*- coding: utf-8 -*-
"""
نص نشر تطبيق ES-GIFT على الخادم
===============================
"""

echo "🚀 بدء نشر تطبيق ES-GIFT"
echo "=========================="

# التحقق من وجود Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 غير مثبت!"
    exit 1
fi

echo "✅ Python 3 متوفر"

# التحقق من وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 غير مثبت!"
    exit 1
fi

echo "✅ pip3 متوفر"

# إنشاء البيئة الافتراضية إذا لم تكن موجودة
if [ ! -d "venv" ]; then
    echo "📦 إنشاء البيئة الافتراضية..."
    python3 -m venv venv
fi

# تفعيل البيئة الافتراضية
echo "🔄 تفعيل البيئة الافتراضية..."
source venv/bin/activate

# ترقية pip
echo "⬆️ ترقية pip..."
pip install --upgrade pip

# تثبيت المتطلبات
echo "📋 تثبيت المتطلبات..."
pip install -r requirements.txt

# إنشاء مجلدات ضرورية
echo "📁 إنشاء المجلدات الضرورية..."
mkdir -p instance
mkdir -p static/uploads
mkdir -p logs

# تحضير قاعدة البيانات
echo "🗄️ تحضير قاعدة البيانات..."
export FLASK_APP=app.py
flask db upgrade || echo "⚠️ تحديث قاعدة البيانات فشل (قد يكون طبيعياً للمرة الأولى)"

# تشغيل اختبار سريع للتطبيق
echo "🧪 اختبار التطبيق..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app import app
    print('✅ تم تحميل التطبيق بنجاح')
    print(f'📍 التطبيق جاهز على: {app.config.get(\"SERVER_NAME\", \"localhost:5000\")}')
except Exception as e:
    print(f'❌ خطأ في تحميل التطبيق: {e}')
    exit(1)
"

echo ""
echo "🎉 تم النشر بنجاح!"
echo "==================="
echo ""
echo "🚀 لتشغيل التطبيق باستخدام Gunicorn:"
echo "gunicorn -w 4 -b 127.0.0.1:8000 wsgi:application"
echo ""
echo "🔧 أو لتشغيل خادم التطوير:"
echo "python3 app.py"
echo ""
echo "📊 لتشغيل النظام الكامل:"
echo "python3 run_es_gift.py"
