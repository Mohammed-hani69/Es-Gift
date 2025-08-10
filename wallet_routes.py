#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
routes المحفظة ونظام الحدود
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
import json

from models import (db, UserWallet, WalletTransaction, UserBalance, UserLimits, 
                   Currency, GlobalLimits, PaymentGateway, WalletDepositRequest)
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
        
        # الحصول على حدود المستخدم من نظام UserLimits
        from wallet_utils import get_user_limits, get_user_spending_summary
        user_limits = get_user_limits(current_user.id)
        user_spending = get_user_spending_summary(current_user.id)
        
        # تحديد نوع المستخدم للعرض
        if hasattr(current_user, 'user_type') and current_user.user_type == 'distributor':
            user_type_display = 'موزع'
        elif hasattr(current_user, 'user_type') and current_user.user_type == 'reseller':
            user_type_display = 'موزع'
        elif hasattr(current_user, 'customer_type') and current_user.customer_type == 'reseller':
            user_type_display = 'موزع'
        elif hasattr(current_user, 'kyc_status') and current_user.kyc_status == 'approved':
            user_type_display = 'عميل موثق (KYC)'
        elif hasattr(current_user, 'customer_type') and current_user.customer_type == 'regular':
            user_type_display = 'عميل عادي'
        else:
            user_type_display = 'عميل عادي'
        
        # الحصول على العملات المتاحة
        currencies = Currency.query.filter_by(is_active=True).all()
        
        # الحصول على بوابات الدفع
        payment_gateways = PaymentGateway.query.filter_by(is_active=True).all()
        
        # عملة العرض (العملة المفضلة للمستخدم أو USD)
        display_currency = current_user.preferred_currency or 'USD'
        if request.args.get('currency'):
            display_currency = request.args.get('currency')
        
        # التحقق من أن العملة متاحة
        currency_obj = Currency.query.filter_by(code=display_currency, is_active=True).first()
        if not currency_obj:
            display_currency = 'USD'
        
        # استخدام الحدود من نظام UserLimits إذا كانت متاحة، وإلا المحفظة
        if user_limits and user_spending:
            daily_limit_usd = user_spending['daily_limit']
            monthly_limit_usd = user_spending['monthly_limit']
            daily_spent_usd = user_spending['daily_spent']
            monthly_spent_usd = user_spending['monthly_spent']
            daily_remaining_usd = user_spending['daily_remaining']
            monthly_remaining_usd = user_spending['monthly_remaining']
            daily_percentage = user_spending['daily_percentage']
            monthly_percentage = user_spending['monthly_percentage']
        else:
            # استخدام الحدود من المحفظة كنسخة احتياطية
            daily_limit_usd = float(wallet.daily_limit)
            monthly_limit_usd = float(wallet.monthly_limit)
            daily_spent_usd = float(wallet.daily_spent_today)
            monthly_spent_usd = float(wallet.monthly_spent)
            daily_remaining_usd = max(0, daily_limit_usd - daily_spent_usd)
            monthly_remaining_usd = max(0, monthly_limit_usd - monthly_spent_usd)
            daily_percentage = min(100, (daily_spent_usd / daily_limit_usd) * 100) if daily_limit_usd > 0 else 0
            monthly_percentage = min(100, (monthly_spent_usd / monthly_limit_usd) * 100) if monthly_limit_usd > 0 else 0
        
        
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
        
        # تحويل الحدود والمبالغ المنفقة للعملة المطلوبة
        daily_spent_display = get_currency_display(
            convert_amount_for_display(Decimal(str(daily_spent_usd)), 'USD', display_currency),
            display_currency
        )
        
        daily_limit_display = get_currency_display(
            convert_amount_for_display(Decimal(str(daily_limit_usd)), 'USD', display_currency),
            display_currency
        )
        
        monthly_limit_display = get_currency_display(
            convert_amount_for_display(Decimal(str(monthly_limit_usd)), 'USD', display_currency),
            display_currency
        )
        
        monthly_spent_display = get_currency_display(
            convert_amount_for_display(Decimal(str(monthly_spent_usd)), 'USD', display_currency),
            display_currency
        )
        
        # عرض المتبقي
        daily_remaining_display = get_currency_display(
            convert_amount_for_display(Decimal(str(daily_remaining_usd)), 'USD', display_currency),
            display_currency
        )
        
        monthly_remaining_display = get_currency_display(
            convert_amount_for_display(Decimal(str(monthly_remaining_usd)), 'USD', display_currency),
            display_currency
        )
        
        # حساب النسب المئوية
        # (تم حسابها بالفعل في user_spending إذا كانت متاحة)
        
        # الحصول على آخر المعاملات (مع التحقق من وجودها وبياناتها)
        recent_transactions_query = WalletTransaction.query.filter_by(
            user_id=current_user.id
        ).order_by(WalletTransaction.created_at.desc()).limit(10).all()
        
        # التأكد من صحة بيانات المعاملات وعدم التكرار
        seen_transactions = set()
        recent_transactions = []
        
        for transaction in recent_transactions_query:
            # التحقق من صحة البيانات
            if not transaction.amount_original or not transaction.currency_code or not transaction.transaction_type:
                continue
                
            # إنشاء مفتاح فريد للمعاملة لتجنب التكرار
            transaction_key = f"{transaction.id}_{transaction.created_at}_{transaction.amount_original}_{transaction.transaction_type}"
            
            if transaction_key not in seen_transactions and len(recent_transactions) < 5:
                seen_transactions.add(transaction_key)
                recent_transactions.append(transaction)
        
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
                             user_type_display=user_type_display,
                             user_limits=user_limits,
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

@wallet_bp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    """صفحة الإيداع في المحفظة"""
    if request.method == 'GET':
        # عرض صفحة الإيداع
        currencies = Currency.query.filter_by(is_active=True).all()
        payment_gateways = PaymentGateway.query.filter_by(is_active=True).all()
        
        return render_template('wallet/deposit.html', 
                             currencies=currencies,
                             payment_gateways=payment_gateways)
    
    try:
        # استخدام FormData بدلاً من JSON لدعم رفع الملفات
        amount = Decimal(request.form.get('amount', '0'))
        currency_code = request.form.get('currency', 'USD')
        payment_method = request.form.get('payment_method', 'bank_transfer')
        notes = request.form.get('notes', '')
        
        # التحقق من صحة البيانات
        if amount <= 0:
            flash('يجب أن يكون المبلغ أكبر من صفر', 'error')
            return redirect(url_for('wallet.deposit'))
        
        # التحقق من العملة
        currency = Currency.query.filter_by(code=currency_code, is_active=True).first()
        if not currency:
            flash('العملة المحددة غير متاحة', 'error')
            return redirect(url_for('wallet.deposit'))
        
        # التعامل مع رفع ملف إثبات المعاملة
        transaction_proof_filename = None
        if 'transaction_proof' in request.files:
            file = request.files['transaction_proof']
            if file and file.filename:
                # التحقق من نوع الملف
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if file_extension in allowed_extensions:
                    # إنشاء اسم ملف آمن
                    import os
                    from werkzeug.utils import secure_filename
                    import uuid
                    
                    filename = secure_filename(file.filename)
                    # إضافة UUID للتأكد من عدم التكرار
                    name, ext = os.path.splitext(filename)
                    transaction_proof_filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}_{name}{ext}"
                    
                    # إنشاء مجلد التحميل إذا لم يكن موجوداً
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'transaction_proofs')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # حفظ الملف
                    file_path = os.path.join(upload_folder, transaction_proof_filename)
                    file.save(file_path)
                else:
                    flash('نوع الملف غير مدعوم. يرجى رفع صورة (PNG, JPG, JPEG, GIF)', 'error')
                    return redirect(url_for('wallet.deposit'))
        
        # تحويل المبلغ إلى الدولار للإحصائيات
        if currency_code != 'USD':
            exchange_rate = convert_currency(1, currency_code, 'USD')
            amount_usd = amount * Decimal(str(exchange_rate))
        else:
            exchange_rate = 1.0
            amount_usd = amount
        
        # تحديد نوع المستخدم
        user_type = 'regular'
        if hasattr(current_user, 'customer_type') and current_user.customer_type:
            user_type = current_user.customer_type
        elif hasattr(current_user, 'kyc_status') and current_user.kyc_status == 'approved':
            user_type = 'kyc'
        
        # إنشاء طلب الإيداع
        deposit_request = WalletDepositRequest(
            user_id=current_user.id,
            amount=amount,
            currency_code=currency_code,
            amount_usd=amount_usd,
            exchange_rate=Decimal(str(exchange_rate)),
            payment_method=payment_method,
            user_type=user_type,
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            payment_details=notes if notes else None,
            transaction_proof=transaction_proof_filename
        )
        
        db.session.add(deposit_request)
        db.session.commit()
        
        # إنشاء فاتورة PDF فوراً عند إنشاء الطلب
        try:
            from simple_deposit_invoice_service import SimpleDepositInvoiceService
            service = SimpleDepositInvoiceService()
            pdf_path = service.generate_deposit_invoice_pdf(deposit_request)
            if pdf_path:
                deposit_request.invoice_pdf_path = pdf_path
                db.session.commit()
                print(f"✅ تم إنشاء فاتورة PDF فوراً للطلب {deposit_request.id}: {pdf_path}")
        except Exception as e:
            print(f"⚠️ خطأ في إنشاء فاتورة PDF للطلب {deposit_request.id}: {e}")
            # لا نوقف العملية في حالة فشل إنشاء الفاتورة
        
        # رسالة مختلفة حسب طريقة الدفع
        if payment_method == 'bank_transfer':
            message = 'تم إرسال طلب الإيداع بنجاح! يرجى التحويل للحساب البنكي المذكور وسيتم مراجعة طلبك خلال 1-3 أيام عمل.'
        else:
            message = 'تم إرسال طلب الإيداع بنجاح! سيتم مراجعة إثبات التحويل من قبل الإدارة خلال 24 ساعة.'
        
        # إضافة flash message
        flash(message, 'success')
        
        # إعادة توجيه إلى صفحة الملف الشخصي
        return redirect(url_for('main.profile'))
        
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في الإيداع: {e}")
        flash('حدث خطأ في معالجة طلب الإيداع', 'error')
        return redirect(url_for('wallet.deposit'))

@wallet_bp.route('/deposit-requests')
@login_required
def deposit_requests():
    """عرض طلبات الإيداع للمستخدم"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        requests = WalletDepositRequest.query.filter_by(
            user_id=current_user.id
        ).order_by(WalletDepositRequest.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('wallet/deposit_requests.html', 
                             requests=requests)
        
    except Exception as e:
        print(f"خطأ في عرض طلبات الإيداع: {e}")
        flash('حدث خطأ في عرض طلبات الإيداع', 'error')
        return redirect(url_for('wallet.wallet_dashboard'))

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

@wallet_bp.route('/update-currency', methods=['POST'])
@login_required
def update_currency():
    """تحديث عملة المحفظة المفضلة للمستخدم"""
    try:
        data = request.get_json()
        new_currency = data.get('currency')
        
        if not new_currency:
            return jsonify({'success': False, 'message': 'لم يتم تحديد العملة'})
        
        # التحقق من وجود العملة
        currency = Currency.query.filter_by(code=new_currency, is_active=True).first()
        if not currency:
            return jsonify({'success': False, 'message': 'العملة المحددة غير متوفرة'})
        
        # تحديث العملة المفضلة للمستخدم
        current_user.preferred_currency = new_currency
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'تم تحديث العملة إلى {currency.name} بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
