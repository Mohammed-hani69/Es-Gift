#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
routes إدارة طلبات المحفظة للأدمن
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
import json

from models import (db, WalletDepositRequest, UserWallet, WalletTransaction, 
                   Currency, User, UserBalance)
from utils import convert_currency
from wallet_utils import get_or_create_wallet

# إنشاء Blueprint لإدارة المحفظة
admin_wallet_bp = Blueprint('admin_wallet', __name__, url_prefix='/admin/wallet')

def admin_required(f):
    """decorator للتأكد من صلاحيات الأدمن"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_wallet_bp.route('/deposit-requests')
@login_required
@admin_required
def deposit_requests():
    """صفحة إدارة طلبات الإيداع"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        status_filter = request.args.get('status', 'all')
        search = request.args.get('search', '')
        
        # بناء الاستعلام
        query = WalletDepositRequest.query
        
        # فلترة حسب الحالة
        if status_filter != 'all':
            query = query.filter(WalletDepositRequest.status == status_filter)
        
        # البحث في البريد الإلكتروني أو الاسم
        if search:
            query = query.join(User).filter(
                db.or_(
                    User.email.contains(search),
                    User.full_name.contains(search)
                )
            )
        
        # ترتيب وتقسيم الصفحات
        requests = query.order_by(
            WalletDepositRequest.created_at.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # إحصائيات
        stats = {
            'total': WalletDepositRequest.query.count(),
            'pending': WalletDepositRequest.query.filter_by(status='pending').count(),
            'approved': WalletDepositRequest.query.filter_by(status='approved').count(),
            'rejected': WalletDepositRequest.query.filter_by(status='rejected').count(),
        }
        
        # العملات المتاحة
        currencies = Currency.query.filter_by(is_active=True).all()
        
        return render_template('admin/wallet_deposit_requests.html',
                             requests=requests,
                             stats=stats,
                             currencies=currencies,
                             status_filter=status_filter,
                             search=search)
        
    except Exception as e:
        print(f"خطأ في عرض طلبات الإيداع: {e}")
        flash('حدث خطأ في عرض طلبات الإيداع', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_wallet_bp.route('/approve-deposit/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def approve_deposit(request_id):
    """قبول طلب الإيداع وإضافة المبلغ للمحفظة"""
    try:
        deposit_request = WalletDepositRequest.query.get_or_404(request_id)
        
        if deposit_request.status != 'pending':
            return jsonify({
                'success': False, 
                'message': f'لا يمكن معالجة طلب بحالة {deposit_request.status}'
            })
        
        # الحصول على البيانات من النموذج
        amount_to_add = Decimal(request.form.get('amount', str(deposit_request.amount)))
        currency_to_add = request.form.get('currency', deposit_request.currency_code)
        admin_notes = request.form.get('admin_notes', '')
        
        # التحقق من العملة
        currency = Currency.query.filter_by(code=currency_to_add, is_active=True).first()
        if not currency:
            return jsonify({
                'success': False, 
                'message': 'العملة المحددة غير متاحة'
            })
        
        # الحصول على محفظة المستخدم
        user_wallet = get_or_create_wallet(deposit_request.user)
        
        # تحويل المبلغ إلى عملة المحفظة إذا لزم الأمر
        if currency_to_add != user_wallet.currency:
            exchange_rate = convert_currency(1, currency_to_add, user_wallet.currency)
            amount_in_wallet_currency = amount_to_add * Decimal(str(exchange_rate))
        else:
            exchange_rate = 1.0
            amount_in_wallet_currency = amount_to_add
        
        # تحويل إلى الدولار للإحصائيات
        if currency_to_add != 'USD':
            usd_rate = convert_currency(1, currency_to_add, 'USD')
            amount_usd = amount_to_add * Decimal(str(usd_rate))
        else:
            amount_usd = amount_to_add
        
        # تحديث المحفظة
        balance_before = user_wallet.balance
        user_wallet.balance += amount_in_wallet_currency
        user_wallet.total_deposits += amount_usd
        user_wallet.updated_at = datetime.utcnow()
        
        # تحديث طلب الإيداع
        deposit_request.status = 'approved'
        deposit_request.processed_by = current_user.id
        deposit_request.processed_at = datetime.utcnow()
        deposit_request.admin_notes = admin_notes
        deposit_request.wallet_amount_added = amount_to_add
        deposit_request.wallet_currency_added = currency_to_add
        
        # إنشاء معاملة
        transaction = WalletTransaction(
            user_id=deposit_request.user_id,
            transaction_type='deposit',
            amount_usd=amount_usd,
            amount_original=amount_to_add,
            currency_code=currency_to_add,
            exchange_rate=Decimal(str(exchange_rate)),
            description=f'إيداع موافق عليه من الإدارة - طلب #{deposit_request.id}',
            reference_id=str(deposit_request.id),
            reference_type='deposit_request',
            status='completed',
            admin_notes=admin_notes
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم قبول الطلب وإضافة {amount_to_add} {currency_to_add} إلى محفظة المستخدم'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في قبول الإيداع: {e}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في معالجة الطلب'
        })

@admin_wallet_bp.route('/reject-deposit/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def reject_deposit(request_id):
    """رفض طلب الإيداع"""
    try:
        deposit_request = WalletDepositRequest.query.get_or_404(request_id)
        
        if deposit_request.status != 'pending':
            return jsonify({
                'success': False, 
                'message': f'لا يمكن معالجة طلب بحالة {deposit_request.status}'
            })
        
        # الحصول على سبب الرفض
        rejection_reason = request.form.get('rejection_reason', '')
        admin_notes = request.form.get('admin_notes', '')
        
        if not rejection_reason:
            return jsonify({
                'success': False,
                'message': 'يجب إدخال سبب الرفض'
            })
        
        # تحديث طلب الإيداع
        deposit_request.status = 'rejected'
        deposit_request.processed_by = current_user.id
        deposit_request.processed_at = datetime.utcnow()
        deposit_request.rejection_reason = rejection_reason
        deposit_request.admin_notes = admin_notes
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم رفض الطلب بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في رفض الإيداع: {e}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في معالجة الطلب'
        })

@admin_wallet_bp.route('/deposit-request/<int:request_id>')
@login_required
@admin_required
def deposit_request_details(request_id):
    """تفاصيل طلب الإيداع"""
    try:
        deposit_request = WalletDepositRequest.query.get_or_404(request_id)
        currencies = Currency.query.filter_by(is_active=True).all()
        
        return render_template('admin/deposit_request_details.html',
                             request=deposit_request,
                             currencies=currencies)
        
    except Exception as e:
        print(f"خطأ في عرض تفاصيل الطلب: {e}")
        flash('حدث خطأ في عرض تفاصيل الطلب', 'error')
        return redirect(url_for('admin_wallet.deposit_requests'))

@admin_wallet_bp.route('/manual-deposit', methods=['GET', 'POST'])
@login_required
@admin_required
def manual_deposit():
    """إيداع يدوي في محفظة مستخدم"""
    if request.method == 'GET':
        currencies = Currency.query.filter_by(is_active=True).all()
        return render_template('admin/manual_deposit.html', currencies=currencies)
    
    try:
        user_email = request.form.get('user_email', '').strip()
        amount = Decimal(request.form.get('amount', '0'))
        currency_code = request.form.get('currency', 'USD')
        notes = request.form.get('notes', '')
        
        # التحقق من البيانات
        if not user_email or amount <= 0:
            return jsonify({
                'success': False,
                'message': 'يرجى إدخال بريد إلكتروني صحيح ومبلغ أكبر من صفر'
            })
        
        # البحث عن المستخدم
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            })
        
        # التحقق من العملة
        currency = Currency.query.filter_by(code=currency_code, is_active=True).first()
        if not currency:
            return jsonify({
                'success': False,
                'message': 'العملة المحددة غير متاحة'
            })
        
        # الحصول على محفظة المستخدم
        user_wallet = get_or_create_wallet(user)
        
        # تحويل المبلغ إلى عملة المحفظة
        if currency_code != user_wallet.currency:
            exchange_rate = convert_currency(1, currency_code, user_wallet.currency)
            amount_in_wallet_currency = amount * Decimal(str(exchange_rate))
        else:
            exchange_rate = 1.0
            amount_in_wallet_currency = amount
        
        # تحويل إلى الدولار للإحصائيات
        if currency_code != 'USD':
            usd_rate = convert_currency(1, currency_code, 'USD')
            amount_usd = amount * Decimal(str(usd_rate))
        else:
            amount_usd = amount
        
        # تحديث المحفظة
        balance_before = user_wallet.balance
        user_wallet.balance += amount_in_wallet_currency
        user_wallet.total_deposits += amount_usd
        user_wallet.updated_at = datetime.utcnow()
        
        # إنشاء معاملة
        transaction = WalletTransaction(
            user_id=user.id,
            transaction_type='deposit',
            amount_usd=amount_usd,
            amount_original=amount,
            currency_code=currency_code,
            exchange_rate=Decimal(str(exchange_rate)),
            description=f'إيداع يدوي من الإدارة - {notes}' if notes else 'إيداع يدوي من الإدارة',
            reference_type='manual_deposit',
            status='completed',
            admin_notes=notes
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم إيداع {amount} {currency_code} في محفظة {user.full_name or user.email} بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في الإيداع اليدوي: {e}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ في معالجة الإيداع'
        })

@admin_wallet_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """إحصائيات المحفظة"""
    try:
        # إحصائيات عامة
        total_deposits = db.session.query(db.func.sum(WalletTransaction.amount_usd)).filter(
            WalletTransaction.transaction_type == 'deposit',
            WalletTransaction.status == 'completed'
        ).scalar() or 0
        
        total_purchases = db.session.query(db.func.sum(WalletTransaction.amount_usd)).filter(
            WalletTransaction.transaction_type == 'purchase',
            WalletTransaction.status == 'completed'
        ).scalar() or 0
        
        total_balance = db.session.query(db.func.sum(UserWallet.balance)).scalar() or 0
        
        # طلبات الإيداع
        pending_requests = WalletDepositRequest.query.filter_by(status='pending').count()
        approved_requests = WalletDepositRequest.query.filter_by(status='approved').count()
        rejected_requests = WalletDepositRequest.query.filter_by(status='rejected').count()
        
        stats = {
            'total_deposits': float(total_deposits),
            'total_purchases': float(total_purchases),
            'total_balance': float(total_balance),
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'rejected_requests': rejected_requests,
        }
        
        return render_template('admin/wallet_statistics.html', stats=stats)
        
    except Exception as e:
        print(f"خطأ في عرض الإحصائيات: {e}")
        flash('حدث خطأ في عرض الإحصائيات', 'error')
        return redirect(url_for('admin.dashboard'))
