#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auth Routes for Email Verification using Email Sender Pro
=========================================================

This module provides authentication routes for email verification
using the new Email Sender Pro API system with 6-digit verification codes.
"""

from flask import Blueprint, request, redirect, url_for, flash, session, current_app, render_template, jsonify
from flask_login import login_user, current_user, login_required
from werkzeug.security import generate_password_hash
from models import User, db
from email_pro_verification_service import (
    send_user_verification_code, 
    verify_user_code, 
    resend_user_verification_code, 
    is_verification_pending,
    get_user_verification_info
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
auth_routes = Blueprint('auth_routes', __name__, url_prefix='/auth')

@auth_routes.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """صفحة التحقق من البريد الإلكتروني"""
    try:
        # التحقق من وجود بريد إلكتروني في الجلسة
        email = session.get('pending_user_email') or session.get('verification_email')
        
        if not email:
            flash('جلسة التحقق منتهية الصلاحية، يرجى التسجيل مرة أخرى', 'error')
            return redirect(url_for('main.register'))
        
        if request.method == 'GET':
            # إظهار صفحة التحقق
            logger.info(f"عرض صفحة التحقق للبريد: {email}")
            return render_template('auth/verify_email.html', email=email)
        
        # معالجة POST - التحقق من الكود
        verification_code = request.form.get('verification_code', '').strip()
        
        if not verification_code:
            flash('يرجى إدخال كود التحقق', 'error')
            return render_template('auth/verify_email.html', email=email)
        
        if len(verification_code) != 6 or not verification_code.isdigit():
            flash('كود التحقق يجب أن يكون 6 أرقام', 'error')
            return render_template('auth/verify_email.html', email=email)
        
        # التحقق من الكود
        logger.info(f"التحقق من الكود للبريد: {email}")
        success, message = verify_user_code(email, verification_code)
        
        if success:
            # البحث عن المستخدم
            user_id = session.get('pending_user_id')
            user = User.query.get(user_id) if user_id else User.query.filter_by(email=email).first()
            
            if user:
                # تفعيل الحساب
                user.is_verified = True
                user.email_verification_token = None
                user.email_verification_sent_at = None
                db.session.commit()
                
                # تسجيل دخول المستخدم
                login_user(user)
                
                # تنظيف الجلسة
                session.pop('pending_user_id', None)
                session.pop('pending_user_email', None)
                session.pop('pending_user_name', None)
                session.pop('verification_email', None)
                session.pop('verification_pending', None)
                
                logger.info(f"تم التحقق بنجاح وتسجيل دخول المستخدم: {user.email}")
                flash('تم التحقق من بريدك الإلكتروني بنجاح! مرحباً بك في ES-GIFT', 'success')
                return redirect(url_for('main.index'))
            else:
                logger.error(f"لم يتم العثور على المستخدم بعد التحقق: {email}")
                flash('حدث خطأ في النظام، يرجى التواصل مع الدعم', 'error')
                return render_template('auth/verify_email.html', email=email)
        else:
            # فشل التحقق
            logger.warning(f"فشل التحقق من الكود للبريد {email}: {message}")
            flash(message, 'error')
            return render_template('auth/verify_email.html', email=email)
            
    except Exception as e:
        error_msg = f"خطأ في صفحة التحقق: {str(e)}"
        logger.error(error_msg)
        flash('حدث خطأ أثناء التحقق من البريد الإلكتروني', 'error')
        return redirect(url_for('main.register'))

@auth_routes.route('/resend-verification', methods=['POST'])
def resend_verification():
    """إعادة إرسال كود التحقق"""
    try:
        # التحقق من طريقة الطلب
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
        else:
            email = request.form.get('email')
        
        if not email:
            logger.warning("طلب إعادة إرسال بدون بريد إلكتروني")
            return jsonify({'success': False, 'message': 'البريد الإلكتروني مطلوب'})
        
        logger.info(f"طلب إعادة إرسال كود التحقق للبريد: {email}")
        
        # التحقق من وجود المستخدم
        user = User.query.filter_by(email=email).first()
        if not user:
            logger.warning(f"طلب إعادة إرسال لبريد غير مسجل: {email}")
            return jsonify({'success': False, 'message': 'البريد الإلكتروني غير مسجل'})
        
        if user.is_verified:
            logger.info(f"طلب إعادة إرسال لحساب مفعل: {email}")
            return jsonify({'success': False, 'message': 'تم التحقق من هذا الحساب مسبقاً'})
        
        # إعادة إرسال الكود
        user_name = session.get('pending_user_name') or user.full_name or email.split('@')[0]
        success, message = resend_user_verification_code(email)
        
        if success:
            logger.info(f"تم إعادة إرسال كود التحقق بنجاح للبريد: {email}")
            return jsonify({'success': True, 'message': 'تم إعادة إرسال كود التحقق بنجاح'})
        else:
            logger.error(f"فشل إعادة إرسال كود التحقق للبريد {email}: {message}")
            return jsonify({'success': False, 'message': message})
        
    except Exception as e:
        error_msg = f"خطأ في إعادة إرسال كود التحقق: {str(e)}"
        logger.error(error_msg)
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء إعادة الإرسال'})

@auth_routes.route('/verification-status/<email>')
def verification_status(email):
    """التحقق من حالة التحقق من البريد"""
    try:
        logger.info(f"فحص حالة التحقق للبريد: {email}")
        
        # التحقق من وجود المستخدم
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False, 
                'message': 'البريد الإلكتروني غير مسجل',
                'verified': False
            })
        
        if user.is_verified:
            return jsonify({
                'success': True,
                'message': 'تم التحقق من الحساب مسبقاً',
                'verified': True
            })
        
        # التحقق من وجود كود تحقق معلق
        verification_info = get_user_verification_info(email)
        
        if verification_info:
            return jsonify({
                'success': True,
                'message': 'يوجد كود تحقق معلق',
                'verified': False,
                'pending': True,
                'attempts_remaining': 3 - verification_info['attempts'],
                'time_remaining': verification_info['time_remaining']
            })
        else:
            return jsonify({
                'success': True,
                'message': 'لا يوجد كود تحقق معلق',
                'verified': False,
                'pending': False
            })
        
    except Exception as e:
        error_msg = f"خطأ في فحص حالة التحقق: {str(e)}"
        logger.error(error_msg)
        return jsonify({'success': False, 'message': 'حدث خطأ في النظام'})

@auth_routes.route('/test-verification')
def test_verification():
    """صفحة اختبار نظام التحقق - للتطوير فقط"""
    if not current_app.debug:
        return "هذه الصفحة متاحة في وضع التطوير فقط", 403
    
    return render_template('auth/test_verification.html')

@auth_routes.route('/cancel-verification')
def cancel_verification():
    """إلغاء عملية التحقق والعودة للتسجيل"""
    try:
        email = session.get('pending_user_email')
        
        if email:
            logger.info(f"إلغاء عملية التحقق للبريد: {email}")
            
            # حذف المستخدم إذا كان في حالة انتظار التحقق
            user_id = session.get('pending_user_id')
            if user_id:
                user = User.query.get(user_id)
                if user and not user.is_verified:
                    db.session.delete(user)
                    db.session.commit()
                    logger.info(f"تم حذف المستخدم غير المفعل: {email}")
        
        # تنظيف الجلسة
        session.pop('pending_user_id', None)
        session.pop('pending_user_email', None)
        session.pop('pending_user_name', None)
        session.pop('verification_email', None)
        session.pop('verification_pending', None)
        
        flash('تم إلغاء عملية التحقق، يمكنك التسجيل مرة أخرى', 'info')
        return redirect(url_for('main.register'))
        
    except Exception as e:
        error_msg = f"خطأ في إلغاء التحقق: {str(e)}"
        logger.error(error_msg)
        flash('حدث خطأ أثناء إلغاء التحقق', 'error')
        return redirect(url_for('main.register'))

# تسجيل Blueprint
def register_auth_routes(app):
    """تسجيل مسارات المصادقة في التطبيق"""
    app.register_blueprint(auth_routes)
    logger.info("تم تسجيل مسارات المصادقة بنجاح")
