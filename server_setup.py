#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد سريع للخادم - ES-GIFT
==========================
"""

import os
import sys
import subprocess
import shutil

def create_systemd_service():
    """إنشاء خدمة systemd للتطبيق"""
    service_content = """[Unit]
Description=ES-Gift Flask Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/esgift
Environment=PATH=/var/www/esgift/venv/bin
ExecStart=/var/www/esgift/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    
    service_path = "/etc/systemd/system/esgift.service"
    
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        print("✅ تم إنشاء خدمة systemd")
        print("🔄 تفعيل الخدمة...")
        
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'enable', 'esgift'], check=True)
        
        print("✅ تم تفعيل الخدمة")
        return True
        
    except PermissionError:
        print("❌ يُطلب صلاحيات root لإنشاء الخدمة")
        return False
    except Exception as e:
        print(f"❌ خطأ في إنشاء الخدمة: {e}")
        return False

def create_nginx_config():
    """إنشاء إعدادات Nginx"""
    nginx_content = """server {
    listen 80;
    server_name your-domain.com;  # غير هذا إلى اسم نطاقك

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static/ {
        alias /var/www/esgift/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # إعدادات الأمان
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
}
"""
    
    config_path = "/etc/nginx/sites-available/esgift"
    
    try:
        with open(config_path, 'w') as f:
            f.write(nginx_content)
        
        # إنشاء رابط في sites-enabled
        enabled_path = "/etc/nginx/sites-enabled/esgift"
        if not os.path.exists(enabled_path):
            os.symlink(config_path, enabled_path)
        
        print("✅ تم إنشاء إعدادات Nginx")
        print("⚠️ تذكر تغيير server_name إلى نطاقك")
        
        # اختبار إعدادات Nginx
        result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ إعدادات Nginx صحيحة")
        else:
            print(f"❌ خطأ في إعدادات Nginx: {result.stderr}")
        
        return True
        
    except PermissionError:
        print("❌ يُطلب صلاحيات root لإنشاء إعدادات Nginx")
        return False
    except Exception as e:
        print(f"❌ خطأ في إنشاء إعدادات Nginx: {e}")
        return False

def setup_firewall():
    """إعداد الجدار الناري"""
    try:
        print("🔒 إعداد الجدار الناري...")
        
        # فتح المنافذ المطلوبة
        subprocess.run(['ufw', 'allow', '22'], check=True)  # SSH
        subprocess.run(['ufw', 'allow', '80'], check=True)  # HTTP
        subprocess.run(['ufw', 'allow', '443'], check=True)  # HTTPS
        
        # تفعيل الجدار الناري
        subprocess.run(['ufw', '--force', 'enable'], check=True)
        
        print("✅ تم إعداد الجدار الناري")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ فشل في إعداد الجدار الناري")
        return False
    except FileNotFoundError:
        print("⚠️ ufw غير مثبت")
        return False

def create_backup_script():
    """إنشاء نص احتياطي"""
    backup_content = """#!/bin/bash
# نص احتياطي لتطبيق ES-GIFT

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/esgift"
APP_DIR="/var/www/esgift"

mkdir -p $BACKUP_DIR

echo "🔄 بدء النسخ الاحتياطي..."

# نسخ ملفات التطبيق
tar -czf $BACKUP_DIR/esgift_app_$DATE.tar.gz -C $APP_DIR .

# نسخ قاعدة البيانات
cp $APP_DIR/instance/es_gift.db $BACKUP_DIR/es_gift_$DATE.db

# حذف النسخ القديمة (أكثر من 7 أيام)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "✅ تم النسخ الاحتياطي"
"""
    
    script_path = "/usr/local/bin/backup_esgift.sh"
    
    try:
        with open(script_path, 'w') as f:
            f.write(backup_content)
        
        os.chmod(script_path, 0o755)
        
        print("✅ تم إنشاء نص النسخ الاحتياطي")
        print(f"📍 الموقع: {script_path}")
        
        # إضافة مهمة cron
        cron_job = f"0 2 * * * {script_path}\n"
        
        try:
            # إضافة إلى crontab
            subprocess.run(['crontab', '-l'], check=True, capture_output=True)
            print("⚠️ يرجى إضافة هذا السطر إلى crontab يدوياً:")
            print(cron_job.strip())
        except subprocess.CalledProcessError:
            print("ℹ️ يمكنك إضافة مهمة النسخ الاحتياطي:")
            print(f"crontab -e")
            print(cron_job.strip())
        
        return True
        
    except PermissionError:
        print("❌ يُطلب صلاحيات root لإنشاء نص النسخ الاحتياطي")
        return False
    except Exception as e:
        print(f"❌ خطأ في إنشاء نص النسخ الاحتياطي: {e}")
        return False

def check_system_requirements():
    """فحص متطلبات النظام"""
    print("🔍 فحص متطلبات النظام...")
    
    requirements = {
        'python3': 'Python 3.8+',
        'pip3': 'pip',
        'nginx': 'Nginx',
        'systemctl': 'systemd'
    }
    
    missing = []
    for cmd, desc in requirements.items():
        if not shutil.which(cmd):
            missing.append(desc)
            print(f"❌ {desc} غير مثبت")
        else:
            print(f"✅ {desc}")
    
    if missing:
        print(f"\n⚠️ متطلبات مفقودة: {', '.join(missing)}")
        print("يرجى تثبيتها أولاً:")
        print("apt update && apt install -y python3 python3-pip nginx")
    
    return len(missing) == 0

def main():
    """الدالة الرئيسية"""
    print("⚙️ إعداد خادم ES-GIFT")
    print("=" * 30)
    
    # فحص متطلبات النظام
    if not check_system_requirements():
        print("❌ متطلبات النظام غير مكتملة")
        return False
    
    # إعداد الخدمات
    print("\n🔧 إعداد الخدمات...")
    
    # خدمة systemd
    if create_systemd_service():
        print("✅ خدمة systemd جاهزة")
    
    # إعدادات Nginx
    if create_nginx_config():
        print("✅ Nginx جاهز")
    
    # الجدار الناري
    if setup_firewall():
        print("✅ الجدار الناري جاهز")
    
    # النسخ الاحتياطي
    if create_backup_script():
        print("✅ النسخ الاحتياطي جاهز")
    
    print("\n🎉 انتهى الإعداد!")
    print("=" * 30)
    print("\n📋 الخطوات التالية:")
    print("1. systemctl start esgift")
    print("2. systemctl reload nginx")
    print("3. تغيير server_name في /etc/nginx/sites-available/esgift")
    print("4. اختبار التطبيق")
    
    return True

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("⚠️ يُنصح بتشغيل هذا النص بصلاحيات root")
        print("sudo python3 server_setup.py")
    
    main()
