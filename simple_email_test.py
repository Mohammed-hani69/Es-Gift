#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار بسيط لإرسال البريد الإلكتروني
==================================
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

def test_smtp_connection():
    """اختبار اتصال SMTP مباشر"""
    load_dotenv()
    
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    if not username or not password:
        print("❌ متغيرات البيئة غير محددة")
        return False
    
    try:
        # إنشاء اتصال SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print(f"🔑 محاولة تسجيل الدخول بـ: {username}")
        server.login(username, password)
        
        # إنشاء رسالة بسيطة
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username  # إرسال لنفس البريد
        msg['Subject'] = "اختبار SMTP - ES-Gift"
        
        body = "هذا اختبار بسيط لاتصال SMTP"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # إرسال الرسالة
        server.send_message(msg)
        server.quit()
        
        print("✅ تم إرسال البريد بنجاح!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return False

if __name__ == "__main__":
    test_smtp_connection()
