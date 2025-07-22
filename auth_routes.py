# -*- coding: utf-8 -*-
"""
Google OAuth Routes for ES-Gift
===============================

This module provides Google OAuth authentication routes for user login and registration.

Author: ES-Gift Development Team
Created: 2025
"""

from flask import Blueprint, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, current_user
from models import User, db
from google_auth import GoogleAuthService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize Google Auth Service
google_auth = GoogleAuthService()

@auth_bp.route('/google/login')
def google_login():
    """
    Redirect to Google OAuth authorization URL
    """
    try:
        if current_user.is_authenticated:
            flash('أنت مسجل دخول بالفعل', 'info')
            return redirect(url_for('main.index'))
        
        # Get Google authorization URL
        auth_url = google_auth.get_google_auth_url()
        logger.info("Redirecting to Google OAuth")
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
            flash(f'تم إلغاء تسجيل الدخول: {error}', 'warning')
            return redirect(url_for('main.login'))
        
        if not authorization_code:
            flash('لم يتم الحصول على كود التفويض', 'error')
            return redirect(url_for('main.login'))
        
        # Handle Google callback and get user info
        user_info = google_auth.handle_google_callback(authorization_code, state)
        
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
        new_user.set_password(secrets.token_urlsafe(32))
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the new user
        login_user(new_user)
        flash(f'مرحباً بك في ES-Gift، {new_user.username}! تم إنشاء حسابك بنجاح', 'success')
        logger.info(f"New Google user registered and logged in: {new_user.username}")
        
        return redirect(url_for('main.index'))
        
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        flash(f'خطأ في معالجة تسجيل الدخول: {str(e)}', 'error')
        return redirect(url_for('main.login'))
