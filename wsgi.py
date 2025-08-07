#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف WSGI لتطبيق ES-GIFT
======================
هذا الملف مطلوب لتشغيل التطبيق على الخادم باستخدام Gunicorn
"""

import os
import sys

# إضافة مسار المشروع الحالي لـ Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# استيراد التطبيق من app.py
from app import app

# تعريف application للـ WSGI server
application = app

if __name__ == "__main__":
    # تشغيل التطبيق في وضع التطوير
    app.run(host='0.0.0.0', port=5000, debug=False)
