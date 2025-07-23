import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

class Config:
    """إعدادات التطبيق"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'es-gift-super-secret-key-2025-for-oauth-sessions')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///es_gift.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات البيئة
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    ENV = os.getenv('ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # إعدادات Session للـ OAuth
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    UPLOAD_FOLDER_ARTICALES = os.getenv('UPLOAD_FOLDER', 'static/uploads/articles')
    UPLOAD_FOLDER_GIFT = os.getenv('UPLOAD_FOLDER', 'static/uploads/gift-cards')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))
    
    # إعدادات البريد الإلكتروني
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    # إعدادات Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '712420880804-hi84lrcs4igfplrm7mgp647v19g8sggk.apps.googleusercontent.com')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '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')
