# -*- coding: utf-8 -*-
"""
Google OAuth Integration for ES-Gift
=====================================

This module provides Google OAuth authentication functionality for user login and registration.
Compatible with ES-Gift's existing Flask-Login system.

Author: ES-Gift Development Team
Created: 2025
"""

import os
import json
from flask import current_app, session, request, url_for, redirect, flash
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleAuthService:
    """
    Google OAuth service for handling authentication with Google
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the Google Auth service with Flask app"""
        # Google OAuth Configuration
        app.config.setdefault('GOOGLE_CLIENT_ID', '712420880804-hi84lrcs4igfplrm7mgp647v19g8sggk.apps.googleusercontent.com')
        app.config.setdefault('GOOGLE_CLIENT_SECRET', '')  # يجب إضافة هذا في ملف البيئة
        app.config.setdefault('GOOGLE_DISCOVERY_URL', 'https://accounts.google.com/.well-known/openid_configuration')
        
        # OAuth 2.0 Scopes
        self.scopes = [
            'openid',
            'email',
            'profile'
        ]
        
        # Store the app instance
        self.app = app
        
        logger.info("Google Auth Service initialized successfully")
    
    def get_google_auth_url(self):
        """
        Generate Google OAuth authorization URL
        
        Returns:
            str: Authorization URL for Google OAuth
        """
        try:
            # Get the correct redirect URI based on environment
            # Support multiple URIs for development
            if current_app.config.get('FLASK_ENV') == 'development':
                # Try different localhost variations
                possible_uris = [
                    'http://localhost:5000/auth/google/callback',
                    'http://127.0.0.1:5000/auth/google/callback'
                ]
                redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI', possible_uris[0])
            else:
                redirect_uri = url_for('google_callback', _external=True)
            
            logger.info(f"Using redirect URI: {redirect_uri}")
            
            # Create the flow using the client secrets
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                        "client_secret": current_app.config.get('GOOGLE_CLIENT_SECRET', ''),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            
            # Set the redirect URI
            flow.redirect_uri = redirect_uri
            
            # Generate authorization URL
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='select_account'  # Force account selection
            )
            
            # Store state in session for security
            session['google_auth_state'] = state
            
            logger.info(f"Generated Google auth URL successfully")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Error generating Google auth URL: {str(e)}")
            raise Exception(f"فشل في إنشاء رابط تسجيل الدخول: {str(e)}")
    
    def handle_google_callback(self, authorization_code, state):
        """
        Handle Google OAuth callback and extract user information
        
        Args:
            authorization_code (str): Authorization code from Google
            state (str): State parameter for security verification
            
        Returns:
            dict: User information from Google
        """
        try:
            # Verify state parameter
            if state != session.get('google_auth_state'):
                raise Exception("حالة المصادقة غير صحيحة")
            
            # Create the flow using the client secrets
            # Get the correct redirect URI based on environment
            if current_app.config.get('FLASK_ENV') == 'development':
                redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/google/callback')
            else:
                redirect_uri = url_for('google_callback', _external=True)
                
            logger.info(f"Using callback redirect URI: {redirect_uri}")
                
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                        "client_secret": current_app.config.get('GOOGLE_CLIENT_SECRET', ''),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=self.scopes,
                state=state
            )
            
            # Set the redirect URI
            flow.redirect_uri = redirect_uri
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            
            # Get user info from Google
            credentials = flow.credentials
            user_info = self.get_user_info(credentials)
            
            # Clear the state from session
            session.pop('google_auth_state', None)
            
            logger.info(f"Successfully processed Google callback for user: {user_info.get('email', 'Unknown')}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error handling Google callback: {str(e)}")
            raise Exception(f"فشل في معالجة تسجيل الدخول: {str(e)}")
    
    def get_user_info(self, credentials):
        """
        Get user information from Google using credentials
        
        Args:
            credentials: Google OAuth credentials
            
        Returns:
            dict: User information
        """
        try:
            # Build the service
            service = build('oauth2', 'v2', credentials=credentials)
            
            # Get user info
            user_info = service.userinfo().get().execute()
            
            # Return standardized user info
            return {
                'google_id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'picture': user_info.get('picture'),
                'verified_email': user_info.get('verified_email', False),
                'locale': user_info.get('locale', 'ar')
            }
            
        except Exception as e:
            logger.error(f"Error getting user info from Google: {str(e)}")
            raise Exception(f"فشل في الحصول على معلومات المستخدم: {str(e)}")
    
    def revoke_token(self, credentials):
        """
        Revoke Google OAuth token
        
        Args:
            credentials: Google OAuth credentials to revoke
        """
        try:
            credentials.revoke(Request())
            logger.info("Google OAuth token revoked successfully")
            
        except Exception as e:
            logger.error(f"Error revoking Google token: {str(e)}")
            raise Exception(f"فشل في إلغاء الرمز المميز: {str(e)}")

# Initialize Google Auth Service
google_auth_service = GoogleAuthService()

def init_google_auth(app):
    """Initialize Google Auth with Flask app"""
    google_auth_service.init_app(app)
    
    @app.route('/auth/google')
    def google_login():
        """Start Google OAuth flow"""
        try:
            auth_url = google_auth_service.get_google_auth_url()
            return redirect(auth_url)
        except Exception as e:
            flash(f'خطأ في تسجيل الدخول بجوجل: {str(e)}', 'error')
            return redirect(url_for('main.login'))
    
    @app.route('/auth/google/callback')
    def google_callback():
        """Handle Google OAuth callback"""
        try:
            # Get authorization code and state from request
            authorization_code = request.args.get('code')
            state = request.args.get('state')
            
            if not authorization_code:
                flash('فشل في تسجيل الدخول بجوجل: لم يتم الحصول على كود التفويض', 'error')
                return redirect(url_for('main.login'))
            
            # Handle the callback
            user_info = google_auth_service.handle_google_callback(authorization_code, state)
            
            # Import here to avoid circular imports
            from models import User, db
            from flask_login import login_user
            
            # Check if user exists
            user = User.query.filter_by(email=user_info['email']).first()
            
            if user:
                # Update user's Google info if needed
                if not user.google_id:
                    user.google_id = user_info['google_id']
                    user.profile_picture = user_info.get('picture')
                    db.session.commit()
                
                # Log the user in
                login_user(user, remember=True)
                flash(f'مرحباً بك {user.username}!', 'success')
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            
            else:
                # Create new user account
                new_user = User(
                    username=user_info['email'].split('@')[0],  # Use email prefix as username
                    email=user_info['email'],
                    full_name=user_info['name'],
                    google_id=user_info['google_id'],
                    profile_picture=user_info.get('picture'),
                    is_verified=user_info.get('verified_email', False),
                    password_hash='google_oauth'  # Mark as Google OAuth user
                )
                
                db.session.add(new_user)
                db.session.commit()
                
                # Log the new user in
                login_user(new_user, remember=True)
                flash(f'تم إنشاء حسابك بنجاح! مرحباً بك {new_user.username}!', 'success')
                
                return redirect(url_for('main.profile'))  # Redirect to profile to complete setup
                
        except Exception as e:
            logger.error(f"Error in Google callback: {str(e)}")
            flash(f'خطأ في تسجيل الدخول بجوجل: {str(e)}', 'error')
            return redirect(url_for('main.login'))
    
    logger.info("Google Auth routes registered successfully")

def get_google_client_id():
    """Get Google Client ID for frontend use"""
    return current_app.config.get('GOOGLE_CLIENT_ID', '')
