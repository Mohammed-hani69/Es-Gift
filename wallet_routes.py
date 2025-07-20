#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
routes المحفظة ونظام الحدود
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
import json

from models import db, UserWallet, WalletTransaction, UserBalance, UserLimits, Currency, GlobalLimits, PaymentGateway
from utils import convert_currency

# إنشاء Blueprint للمحفظة
wallet_bp = Blueprint('wallet', __name__, url_prefix='/wallet')

def get_or_create_wallet(user):
    """الحصول على محفظة المستخدم أو إنشاؤها"""
    wallet = UserWallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        # تحديد نوع المستخدم للحصول على الحدود الافتراضية
        if hasattr(user, 'user_type') and user.user_type == 'distributor':
            user_type = 'distributor'
        elif hasattr(user, 'user_type') and user.user_type == 'reseller':
            user_type = 'reseller'
        elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
            user_type = 'reseller'
        elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
            user_type = 'kyc'
        elif hasattr(user, 'customer_type') and user.customer_type == 'regular':
            user_type = 'regular'
        else:
            user_type = 'regular'
        
        # الحصول على الحدود الافتراضية من GlobalLimits
        global_limit = GlobalLimits.query.filter_by(user_type=user_type, is_active=True).first()
        
        if not global_limit:
            # إنشاء الحدود الافتراضية إذا لم تكن موجودة
            create_default_limit_settings()
            global_limit = GlobalLimits.query.filter_by(user_type=user_type, is_active=True).first()
        
        if global_limit:
            wallet = UserWallet(
                user_id=user.id,
                daily_limit=global_limit.daily_limit_usd,
                monthly_limit=global_limit.monthly_limit_usd
            )
        else:
            # حدود افتراضية آمنة
            wallet = UserWallet(
                user_id=user.id,
                daily_limit=Decimal('3000.00'),
                monthly_limit=Decimal('90000.00')
            )
        
        db.session.add(wallet)
        db.session.commit()
    
    return wallet

def create_default_limit_settings():
    """إنشاء إعدادات الحدود الافتراضية"""
    default_settings = [
        {
            'user_type': 'regular',
            'display_name': 'عميل عادي',
            'daily_limit_usd': Decimal('3000.00'),
            'monthly_limit_usd': Decimal('90000.00'),
            'description': 'عميل عادي'
        },
        {
            'user_type': 'kyc',
            'display_name': 'عميل موثق',
            'daily_limit_usd': Decimal('6000.00'),
            'monthly_limit_usd': Decimal('180000.00'),
            'description': 'عميل موثق'
        },
        {
            'user_type': 'reseller',
            'display_name': 'موزع',
            'daily_limit_usd': Decimal('10000.00'),
            'monthly_limit_usd': Decimal('300000.00'),
            'description': 'موزع'
        }
    ]
    
    for setting in default_settings:
        existing = GlobalLimits.query.filter_by(user_type=setting['user_type']).first()
        if not existing:
            limit_setting = GlobalLimits(**setting)
            db.session.add(limit_setting)
    
    db.session.commit()

def reset_daily_limits_if_needed(wallet):
    """إعادة تعيين الحدود اليومية إذا لزم الأمر"""
    today = date.today()
    if wallet.last_daily_reset != today:
        wallet.daily_spent_today = Decimal('0.00')
        wallet.last_daily_reset = today
        db.session.commit()

def reset_monthly_limits_if_needed(wallet):
    """إعادة تعيين الحدود الشهرية إذا لزم الأمر"""
    today = date.today()
    first_of_month = today.replace(day=1)
    if wallet.last_monthly_reset != first_of_month:
        wallet.monthly_spent = Decimal('0.00')
        wallet.last_monthly_reset = first_of_month
        db.session.commit()

def convert_amount_for_display(amount, from_currency, to_currency):
    """تحويل المبلغ للعرض"""
    if from_currency == to_currency:
        return amount
    
    try:
        converted = convert_currency(float(amount), from_currency, to_currency)
        return Decimal(str(converted))
    except:
        return amount

def get_currency_display(amount, currency_code):
    """الحصول على عرض المبلغ مع رمز العملة"""
    currency = Currency.query.filter_by(code=currency_code).first()
    if currency:
        return {
            'amount': f"{amount:,.2f}",
            'symbol': currency.symbol,
            'currency': currency_code
        }
    return {
        'amount': f"{amount:,.2f}",
        'symbol': currency_code,
        'currency': currency_code
    }

@wallet_bp.route('/')
@login_required
def wallet_dashboard():
    """لوحة تحكم المحفظة"""
    try:
        # الحصول على المحفظة
        wallet = get_or_create_wallet(current_user)
        
        # إعادة تعيين الحدود إذا لزم الأمر
        reset_daily_limits_if_needed(wallet)
        reset_monthly_limits_if_needed(wallet)
        
        # الحصول على العملات المتاحة
        currencies = Currency.query.filter_by(is_active=True).all()
        
        # الحصول على بوابات الدفع
        payment_gateways = PaymentGateway.query.filter_by(is_active=True).all()
        
        # عملة العرض (افتراضي USD)
        display_currency = request.args.get('currency', 'USD')
        
        # تحويل المبالغ للعملة المطلوبة
        wallet_balance_display = get_currency_display(
            convert_amount_for_display(wallet.balance, wallet.currency, display_currency),
            display_currency
        )
        
        total_deposits_display = get_currency_display(
            convert_amount_for_display(wallet.total_deposits, 'USD', display_currency),
            display_currency
        )
        
        total_purchases_display = get_currency_display(
            convert_amount_for_display(wallet.total_purchases, 'USD', display_currency),
            display_currency
        )
        
        daily_spent_display = get_currency_display(
            convert_amount_for_display(wallet.daily_spent_today, 'USD', display_currency),
            display_currency
        )
        
        daily_limit_display = get_currency_display(
            convert_amount_for_display(wallet.daily_limit, 'USD', display_currency),
            display_currency
        )
        
        monthly_limit_display = get_currency_display(
            convert_amount_for_display(wallet.monthly_limit, 'USD', display_currency),
            display_currency
        )
        
        monthly_spent_display = get_currency_display(
            convert_amount_for_display(wallet.monthly_spent, 'USD', display_currency),
            display_currency
        )
        
        # حساب المتبقي
        daily_remaining = max(Decimal('0'), wallet.daily_limit - wallet.daily_spent_today)
        monthly_remaining = max(Decimal('0'), wallet.monthly_limit - wallet.monthly_spent)
        
        daily_remaining_display = get_currency_display(
            convert_amount_for_display(daily_remaining, 'USD', display_currency),
            display_currency
        )
        
        monthly_remaining_display = get_currency_display(
            convert_amount_for_display(monthly_remaining, 'USD', display_currency),
            display_currency
        )
        
        # حساب النسب المئوية
        daily_percentage = min(100, (float(wallet.daily_spent_today) / float(wallet.daily_limit)) * 100) if wallet.daily_limit > 0 else 0
        monthly_percentage = min(100, (float(wallet.monthly_spent) / float(wallet.monthly_limit)) * 100) if wallet.monthly_limit > 0 else 0
        
        # الحصول على آخر المعاملات
        recent_transactions = WalletTransaction.query.filter_by(
            user_id=current_user.id
        ).order_by(WalletTransaction.created_at.desc()).limit(5).all()
        
        return render_template('wallet.html',
                             wallet=wallet,
                             currencies=currencies,
                             payment_gateways=payment_gateways,
                             wallet_balance_display=wallet_balance_display,
                             total_deposits_display=total_deposits_display,
                             total_purchases_display=total_purchases_display,
                             daily_spent_display=daily_spent_display,
                             daily_limit_display=daily_limit_display,
                             monthly_limit_display=monthly_limit_display,
                             monthly_spent_display=monthly_spent_display,
                             daily_remaining_display=daily_remaining_display,
                             monthly_remaining_display=monthly_remaining_display,
                             daily_percentage=daily_percentage,
                             monthly_percentage=monthly_percentage,
                             recent_transactions=recent_transactions)
                             
    except Exception as e:
        flash(f'خطأ في تحميل المحفظة: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@wallet_bp.route('/convert-display')
@login_required
def convert_display():
    """تحويل عرض المحفظة لعملة مختلفة"""
    try:
        currency = request.args.get('currency', 'USD')
        wallet = get_or_create_wallet(current_user)
        
        # إعادة تعيين الحدود إذا لزم الأمر
        reset_daily_limits_if_needed(wallet)
        reset_monthly_limits_if_needed(wallet)
        
        # تحويل جميع المبالغ
        balance_converted = convert_amount_for_display(wallet.balance, wallet.currency, currency)
        total_deposits_converted = convert_amount_for_display(wallet.total_deposits, 'USD', currency)
        total_purchases_converted = convert_amount_for_display(wallet.total_purchases, 'USD', currency)
        daily_spent_converted = convert_amount_for_display(wallet.daily_spent_today, 'USD', currency)
        daily_limit_converted = convert_amount_for_display(wallet.daily_limit, 'USD', currency)
        monthly_limit_converted = convert_amount_for_display(wallet.monthly_limit, 'USD', currency)
        monthly_spent_converted = convert_amount_for_display(wallet.monthly_spent, 'USD', currency)
        
        # حساب المتبقي
        daily_remaining = max(Decimal('0'), wallet.daily_limit - wallet.daily_spent_today)
        monthly_remaining = max(Decimal('0'), wallet.monthly_limit - wallet.monthly_spent)
        
        daily_remaining_converted = convert_amount_for_display(daily_remaining, 'USD', currency)
        monthly_remaining_converted = convert_amount_for_display(monthly_remaining, 'USD', currency)
        
        # حساب النسب المئوية
        daily_percentage = min(100, (float(wallet.daily_spent_today) / float(wallet.daily_limit)) * 100) if wallet.daily_limit > 0 else 0
        monthly_percentage = min(100, (float(wallet.monthly_spent) / float(wallet.monthly_limit)) * 100) if wallet.monthly_limit > 0 else 0
        
        return jsonify({
            'success': True,
            'balance': get_currency_display(balance_converted, currency),
            'total_deposits': get_currency_display(total_deposits_converted, currency),
            'total_purchases': get_currency_display(total_purchases_converted, currency),
            'daily_spent': get_currency_display(daily_spent_converted, currency),
            'daily_limit': get_currency_display(daily_limit_converted, currency),
            'monthly_limit': get_currency_display(monthly_limit_converted, currency),
            'monthly_spent': get_currency_display(monthly_spent_converted, currency),
            'daily_remaining': get_currency_display(daily_remaining_converted, currency),
            'monthly_remaining': get_currency_display(monthly_remaining_converted, currency),
            'daily_percentage': daily_percentage,
            'monthly_percentage': monthly_percentage
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في التحويل: {str(e)}'
        }), 500

@wallet_bp.route('/deposit', methods=['POST'])
@login_required
def deposit():
    """إيداع في المحفظة"""
    try:
        data = request.get_json()
        amount = Decimal(str(data.get('amount', 0)))
        currency = data.get('currency', 'USD')
        payment_method = data.get('payment_method')
        notes = data.get('notes', '')
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': 'يجب أن يكون المبلغ أكبر من صفر'
            }), 400
        
        # التحقق من بوابة الدفع
        gateway = PaymentGateway.query.filter_by(id=payment_method, is_active=True).first()
        if not gateway:
            return jsonify({
                'success': False,
                'message': 'بوابة دفع غير صالحة'
            }), 400
        
        # الحصول على المحفظة
        wallet = get_or_create_wallet(current_user)
        
        # تحويل المبلغ إلى الدولار للإحصائيات
        amount_usd = Decimal(str(convert_currency(float(amount), currency, 'USD')))
        
        # تحويل المبلغ إلى عملة المحفظة
        if currency != wallet.currency:
            amount_wallet_currency = Decimal(str(convert_currency(float(amount), currency, wallet.currency)))
        else:
            amount_wallet_currency = amount
        
        # حفظ الرصيد السابق
        balance_before = wallet.balance
        
        # تحديث الرصيد
        wallet.balance += amount_wallet_currency
        wallet.total_deposits += amount_usd
        wallet.updated_at = datetime.utcnow()
        
        # إنشاء معاملة
        transaction = WalletTransaction(
            user_id=current_user.id,
            transaction_type='deposit',
            amount=amount,
            currency=currency,
            amount_usd=amount_usd,
            description=f'إيداع عبر {gateway.name}',
            reference_id=f'DEP_{datetime.now().strftime("%Y%m%d%H%M%S")}_{current_user.id}',
            balance_before=balance_before,
            balance_after=wallet.balance,
            notes=notes
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم إيداع {amount} {currency} بنجاح',
            'new_balance': f"{wallet.balance} {wallet.currency}",
            'transaction_id': transaction.reference_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في الإيداع: {str(e)}'
        }), 500

@wallet_bp.route('/transactions')
@login_required
def wallet_transactions():
    """صفحة جميع معاملات المحفظة"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        transactions = WalletTransaction.query.filter_by(
            user_id=current_user.id
        ).order_by(WalletTransaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('wallet_transactions.html', transactions=transactions)
        
    except Exception as e:
        flash(f'خطأ في تحميل المعاملات: {str(e)}', 'error')
        return redirect(url_for('wallet.wallet_dashboard'))

def check_spending_limits(user, amount_usd):
    """التحقق من حدود الإنفاق"""
    wallet = get_or_create_wallet(user)
    
    # إعادة تعيين الحدود إذا لزم الأمر
    reset_daily_limits_if_needed(wallet)
    reset_monthly_limits_if_needed(wallet)
    
    # التحقق من الحد اليومي
    if wallet.daily_spent_today + amount_usd > wallet.daily_limit:
        remaining_daily = wallet.daily_limit - wallet.daily_spent_today
        return False, f'تجاوز الحد اليومي. المتبقي: ${remaining_daily:.2f}'
    
    # التحقق من الحد الشهري
    if wallet.monthly_spent + amount_usd > wallet.monthly_limit:
        remaining_monthly = wallet.monthly_limit - wallet.monthly_spent
        return False, f'تجاوز الحد الشهري. المتبقي: ${remaining_monthly:.2f}'
    
    return True, 'OK'

def record_purchase(user, amount, currency, order_id=None, description=''):
    """تسجيل عملية شراء"""
    try:
        wallet = get_or_create_wallet(user)
        
        # تحويل المبلغ إلى الدولار
        amount_usd = Decimal(str(convert_currency(float(amount), currency, 'USD')))
        
        # التحقق من حدود الإنفاق
        can_spend, message = check_spending_limits(user, amount_usd)
        if not can_spend:
            return False, message
        
        # تحويل المبلغ إلى عملة المحفظة
        if currency != wallet.currency:
            amount_wallet_currency = Decimal(str(convert_currency(float(amount), currency, wallet.currency)))
        else:
            amount_wallet_currency = amount
        
        # التحقق من الرصيد
        if wallet.balance < amount_wallet_currency:
            return False, f'رصيد غير كافي. الرصيد الحالي: {wallet.balance} {wallet.currency}'
        
        # حفظ الرصيد السابق
        balance_before = wallet.balance
        
        # تحديث المحفظة
        wallet.balance -= amount_wallet_currency
        wallet.total_purchases += amount_usd
        wallet.daily_spent_today += amount_usd
        wallet.monthly_spent += amount_usd
        wallet.total_orders += 1
        wallet.updated_at = datetime.utcnow()
        
        # إنشاء معاملة
        transaction = WalletTransaction(
            user_id=user.id,
            transaction_type='purchase',
            amount=amount,
            currency=currency,
            amount_usd=amount_usd,
            description=description or f'عملية شراء',
            order_id=order_id,
            balance_before=balance_before,
            balance_after=wallet.balance
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return True, f'تمت عملية الشراء بنجاح. الرصيد الجديد: {wallet.balance} {wallet.currency}'
        
    except Exception as e:
        db.session.rollback()
        return False, f'خطأ في تسجيل الشراء: {str(e)}'
