# -*- coding: utf-8 -*-
"""
Google OAuth Routes for ES-Gift
===============================

This module provides Google OAuth authentication routes for user login and registration.

Author: ES-Gift Development Team
Created: 2025
"""

from flask import Blueprint, request, redirect, url_for, flash, session, current_app, render_template
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash
from models import User, db
from google_auth import GoogleAuthService
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Import Google Auth Service instance
from google_auth import google_auth_service

@auth_bp.route('/google/login')
def google_login():
    """
    Redirect to Google OAuth authorization URL
    """
    try:
        if current_user.is_authenticated:
            logger.info(f"User {current_user.username} already authenticated, redirecting to index")
            flash('أنت مسجل دخول بالفعل', 'info')
            return redirect(url_for('main.index'))
        
        # Clear any existing Google auth state
        session.pop('google_auth_state', None)
        session.pop('google_auth_timestamp', None)
        
        # Get Google authorization URL
        auth_url = google_auth_service.get_google_auth_url()
        logger.info("Successfully generated Google OAuth URL, redirecting user")
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Error in Google login: {str(e)}")
        flash(f'خطأ في تسجيل الدخول: {str(e)}', 'error')
        return redirect(url_for('main.login'))

@auth_bp.route('/google/callback')
def google_callback():
    """
    Handle Google OAuth callback
    """
    try:
        # Get authorization code and state from request
        authorization_code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        # Check for errors from Google
        if error:
            logger.warning(f"Google OAuth error: {error}")
            flash(f'تم إلغاء تسجيل الدخول: {error}', 'warning')
            return redirect(url_for('main.login'))
        
        if not authorization_code:
            logger.error("No authorization code received from Google")
            flash('لم يتم الحصول على كود التفويض', 'error')
            return redirect(url_for('main.login'))
        
        if not state:
            logger.error("No state parameter received from Google")
            flash('معلومات الحالة مفقودة', 'error')
            return redirect(url_for('main.login'))
        
        # Handle Google callback and get user info
        user_info = google_auth_service.handle_google_callback(authorization_code, state)
        
        if not user_info:
            flash('فشل في الحصول على معلومات المستخدم من Google', 'error')
            return redirect(url_for('main.login'))
        
        # Extract user information
        google_id = user_info.get('google_id')
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        if not google_id or not email:
            flash('معلومات المستخدم غير مكتملة', 'error')
            return redirect(url_for('main.login'))
        
        # Check if user exists with this Google ID
        existing_user = User.query.filter_by(google_id=google_id).first()
        
        if existing_user:
            # User exists, log them in
            login_user(existing_user)
            flash(f'مرحباً بك مرة أخرى، {existing_user.username}!', 'success')
            logger.info(f"Existing Google user logged in: {existing_user.username}")
            return redirect(url_for('main.index'))
        
        # Check if user exists with this email
        existing_user_by_email = User.query.filter_by(email=email).first()
        
        if existing_user_by_email:
            # Link Google account to existing user
            existing_user_by_email.google_id = google_id
            existing_user_by_email.profile_picture = picture
            db.session.commit()
            
            login_user(existing_user_by_email)
            flash(f'تم ربط حسابك بـ Google بنجاح! مرحباً بك، {existing_user_by_email.username}', 'success')
            logger.info(f"Linked Google account to existing user: {existing_user_by_email.username}")
            return redirect(url_for('main.index'))
        
        # Create new user
        # Generate username from name or email
        username = name.strip() if name else email.split('@')[0]
        
        # Make sure username is unique
        original_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{original_username}{counter}"
            counter += 1
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            google_id=google_id,
            profile_picture=picture,
            is_verified=True  # Google accounts are pre-verified
        )
        
        # Set a random password (user won't need it since they login with Google)
        import secrets
        new_user.password_hash = generate_password_hash(secrets.token_urlsafe(32))
        
        db.session.add(new_user)
        db.session.flush()  # للحصول على user.id قبل commit
        
        # إنشاء حدود المستخدم بالقيم الافتراضية للمستخدم العادي
        from wallet_utils import create_user_limits, get_or_create_wallet
        user_limits = create_user_limits(new_user)
        
        # إنشاء محفظة المستخدم
        wallet = get_or_create_wallet(new_user)
        
        db.session.commit()
        
        # Log in the new user
        login_user(new_user)
        flash(f'مرحباً بك في ES-Gift، {new_user.username}! تم إنشاء حسابك بنجاح مع إعداد الحدود المالية', 'success')
        logger.info(f"New Google user registered and logged in: {new_user.username}")
        
        return redirect(url_for('main.index'))
        
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        flash(f'خطأ في معالجة تسجيل الدخول: {str(e)}', 'error')
        return redirect(url_for('main.login'))

# ========== مسارات التحقق من البريد الإلكتروني باستخدام Email Sender Pro ==========

@auth_bp.route('/verify-email-code')
def verify_email_code_page():
    """صفحة إدخال كود التحقق"""
    user_email = session.get('pending_verification_email')
    if not user_email:
        flash('جلسة التحقق منتهية الصلاحية', 'warning')
        return redirect(url_for('main.register'))
    
    return render_template('auth/verify_email_code.html', user_email=user_email)

@auth_bp.route('/verify-email-code', methods=['POST'])
def verify_email_code():
    """التحقق من كود التحقق المرسل عبر Email Sender Pro"""
    try:
        from flask import jsonify, render_template
        from email_verification_service import EmailVerificationService
        
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني وكود التحقق مطلوبان'
            })
        
        # التحقق من الكود
        success, message = EmailVerificationService.verify_code(email, code)
        
        if success:
            # مسح جلسة التحقق
            session.pop('pending_verification_email', None)
            
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            })
            
    except Exception as e:
        logger.error(f"خطأ في التحقق من الكود: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء التحقق من الكود'
        })

@auth_bp.route('/resend-verification-code', methods=['POST'])
def resend_verification_code():
    """إعادة إرسال كود التحقق"""
    try:
        from flask import jsonify
        from email_sender_pro_service import send_verification_email
        
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني مطلوب'
            })
        
        # البحث عن المستخدم
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            })
        
        # إرسال كود جديد
        success, message, verification_code = send_verification_email(email)
        
        if success:
            # حفظ الكود الجديد
            try:
                user.email_verification_code = verification_code
                user.email_verification_sent_at = datetime.utcnow()
                db.session.commit()
            except Exception as e:
                logger.error(f"خطأ في حفظ الكود الجديد: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'تم إرسال كود التحقق الجديد بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            })
            
    except Exception as e:
        logger.error(f"خطأ في إعادة إرسال الكود: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إعادة إرسال الكود'
        })

@auth_bp.route('/send-welcome-email', methods=['POST'])
def send_welcome_email_route():
    """إرسال رسالة ترحيبية للمستخدم الجديد"""
    try:
        from flask import jsonify
        from email_sender_pro_service import send_welcome_email
        
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني مطلوب'
            })
        
        # البحث عن المستخدم
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            })
        
        # إرسال رسالة الترحيب
        success, message = send_welcome_email(
            email=email,
            customer_name=user.name or user.username or 'عميل عزيز'
        )
        
        return jsonify({
            'success': success,
            'message': message if not success else 'تم إرسال رسالة الترحيب بنجاح'
        })
        
    except Exception as e:
        logger.error(f"خطأ في إرسال رسالة الترحيب: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إرسال رسالة الترحيب'
        })
