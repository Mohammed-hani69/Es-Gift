#!/bin/bash
# -*- coding: utf-8 -*-
"""
أداة إصلاح مشاكل الخادم لتطبيق ES-GIFT
=====================================
"""

echo "🔧 أداة إصلاح مشاكل الخادم - ES-GIFT"
echo "===================================="

# ألوان للعرض
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# 1. فحص ملف wsgi.py
check_wsgi() {
    echo "🔍 فحص ملف wsgi.py..."
    
    if [ ! -f "wsgi.py" ]; then
        print_error "ملف wsgi.py غير موجود"
        
        print_info "إنشاء ملف wsgi.py..."
        cat > wsgi.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

# إضافة مسار المشروع الحالي
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# استيراد التطبيق
from app import app

# تعريف application للـ WSGI server
application = app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF
        print_success "تم إنشاء ملف wsgi.py"
    else
        print_success "ملف wsgi.py موجود"
    fi
}

# 2. فحص ملف app.py
check_app() {
    echo "🔍 فحص ملف app.py..."
    
    if [ ! -f "app.py" ]; then
        print_error "ملف app.py غير موجود!"
        exit 1
    fi
    
    # فحص وجود app object
    if grep -q "app = create_app()" app.py; then
        print_success "app object موجود في app.py"
    else
        print_warning "app object قد يكون مفقود"
    fi
}

# 3. فحص المتطلبات
check_requirements() {
    echo "📋 فحص المتطلبات..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "ملف requirements.txt غير موجود!"
        return 1
    fi
    
    print_info "تثبيت المتطلبات..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "تم تثبيت المتطلبات"
    else
        print_error "فشل في تثبيت المتطلبات"
        return 1
    fi
}

# 4. فحص Gunicorn
check_gunicorn() {
    echo "🚀 فحص Gunicorn..."
    
    if ! command -v gunicorn &> /dev/null; then
        print_error "Gunicorn غير مثبت"
        print_info "تثبيت Gunicorn..."
        pip install gunicorn
    fi
    
    # اختبار تكوين Gunicorn
    print_info "اختبار تكوين Gunicorn..."
    if gunicorn --check-config wsgi:application; then
        print_success "تكوين Gunicorn صحيح"
    else
        print_error "خطأ في تكوين Gunicorn"
        return 1
    fi
}

# 5. فحص المسارات والأذونات
check_permissions() {
    echo "🔐 فحص المسارات والأذونات..."
    
    # إنشاء مجلدات ضرورية
    mkdir -p instance
    mkdir -p static/uploads
    mkdir -p logs
    
    # فحص أذونات الكتابة
    if [ -w "." ]; then
        print_success "أذونات الكتابة متوفرة"
    else
        print_error "أذونات الكتابة غير متوفرة"
        print_info "تشغيل: chmod 755 ."
    fi
}

# 6. اختبار الاستيراد
test_import() {
    echo "🧪 اختبار الاستيراد..."
    
    python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app import app
    print('✅ نجح استيراد app')
except Exception as e:
    print(f'❌ فشل استيراد app: {e}')
    exit(1)

try:
    from wsgi import application
    print('✅ نجح استيراد wsgi')
except Exception as e:
    print(f'❌ فشل استيراد wsgi: {e}')
    exit(1)

print('🎉 جميع الاستيرادات نجحت!')
"
    
    if [ $? -eq 0 ]; then
        print_success "اختبار الاستيراد نجح"
    else
        print_error "اختبار الاستيراد فشل"
        return 1
    fi
}

# 7. إصلاح تلقائي للمشاكل الشائعة
auto_fix() {
    echo "🔧 إصلاح تلقائي للمشاكل..."
    
    # إصلاح مشكلة run_es_gift في wsgi.py
    if grep -q "run_es_gift" wsgi.py 2>/dev/null; then
        print_warning "إزالة مرجع run_es_gift من wsgi.py"
        sed -i 's/run_es_gift/app/g' wsgi.py
    fi
    
    # التأكد من وجود __pycache__ وحذفها
    if [ -d "__pycache__" ]; then
        print_info "حذف ملفات cache..."
        rm -rf __pycache__
        find . -name "*.pyc" -delete
    fi
    
    print_success "تم الإصلاح التلقائي"
}

# تشغيل جميع الفحوصات
main() {
    echo "🚀 بدء فحص وإصلاح المشاكل..."
    echo "================================"
    
    auto_fix
    check_wsgi
    check_app
    check_permissions
    check_requirements
    check_gunicorn
    test_import
    
    echo ""
    echo "🎉 انتهى الفحص والإصلاح!"
    echo "========================="
    echo ""
    print_info "لتشغيل التطبيق:"
    echo "gunicorn -w 4 -b 127.0.0.1:8000 wsgi:application"
    echo ""
    print_info "لاختبار التطبيق محلياً:"
    echo "python3 app.py"
}

# تشغيل النص
main
