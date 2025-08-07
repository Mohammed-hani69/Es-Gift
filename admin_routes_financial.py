#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes for financial limits and wallet management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
import logging

from models import db, User, UserLimits, GlobalLimits, WalletTransaction, UserBalance
from employee_utils import requires_permission, log_activity

# إعداد التسجيل
logger = logging.getLogger(__name__)

# إنشاء Blueprint منفصل للحدود المالية
financial_bp = Blueprint('financial', __name__, url_prefix='/admin/financial')

@financial_bp.route('/limits')
@login_required
@requires_permission('users.read')
def user_limits_management():
    """صفحة إدارة الحدود المالية للمستخدمين"""
    try:
        from wallet_utils import get_global_limits, ensure_all_users_have_limits, get_users_with_limits_paginated
        
        # التأكد من وجود حدود مالية لجميع المستخدمين
        try:
            ensure_all_users_have_limits()
        except Exception as e:
            print(f"تحذير: خطأ في تحديث حدود المستخدمين: {str(e)}")
        
        # الحصول على معاملات البحث من URL
        email_filter = request.args.get('email', '').strip()
        user_type_filter = request.args.get('user_type', '')
        limit_type_filter = request.args.get('limit_type', '')
        page = request.args.get('page', 1, type=int)
        
        # جلب الحدود الافتراضية
        global_limits = get_global_limits()
        
        # جلب المستخدمين مع الفلاتر
        users_data, total_users = get_users_with_limits_paginated(
            email_filter, user_type_filter, limit_type_filter, page
        )
        
        # حساب عدد الصفحات
        per_page = 50
        total_pages = (total_users + per_page - 1) // per_page
        
        return render_template('admin/user_limits.html', 
                             global_limits=global_limits,
                             users_data=users_data,
                             current_page=page,
                             total_pages=total_pages,
                             total_users=total_users,
                             email_filter=email_filter,
                             user_type_filter=user_type_filter,
                             limit_type_filter=limit_type_filter)
    except Exception as e:
        flash(f'خطأ في تحميل صفحة الحدود المالية: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@financial_bp.route('/limits/search', methods=['POST'])
@login_required
@requires_permission('users.read')
def search_users_with_limits():
    """البحث عن المستخدمين مع حدودهم المالية"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        user_type = data.get('user_type', '')
        limit_type = data.get('limit_type', '')
        
        # بناء الاستعلام - جلب جميع المستخدمين
        query = User.query
        
        if email:
            query = query.filter(User.email.contains(email))
        
        if user_type:
            if user_type == 'normal':
                query = query.filter(User.kyc_status != 'approved', User.customer_type != 'reseller')
            elif user_type == 'kyc':
                query = query.filter(User.kyc_status == 'approved', User.customer_type != 'reseller')
            elif user_type == 'distributor':
                query = query.filter(User.customer_type == 'reseller')
        
        # جلب المستخدمين
        users = query.limit(100).all()
        
        users_data = []
        for user in users:
            # تحديد نوع المستخدم أولاً
            if user.customer_type == 'reseller':
                user_type_display = 'distributor'
            elif user.kyc_status == 'approved':
                user_type_display = 'kyc'
            else:
                user_type_display = 'normal'
            
            # الحصول على أو إنشاء حدود المستخدم
            user_limits = UserLimits.query.filter_by(user_id=user.id).first()
            if not user_limits:
                try:
                    from wallet_utils import create_user_limits
                    user_limits = create_user_limits(user)
                except Exception as e:
                    print(f"خطأ في إنشاء حدود المستخدم {user.email}: {str(e)}")
                    # إنشاء حدود افتراضية مؤقتة للعرض
                    user_limits = None
            
            # إنشاء قيم افتراضية إذا لم توجد حدود
            if user_limits:
                daily_limit = float(user_limits.daily_limit_usd)
                daily_spent = float(user_limits.daily_spent_usd)
                monthly_limit = float(user_limits.monthly_limit_usd)
                monthly_spent = float(user_limits.monthly_spent_usd)
                is_custom = user_limits.is_custom
                notes = user_limits.notes
            else:
                # قيم افتراضية عند عدم وجود حدود
                daily_limit = 0.00
                daily_spent = 0.00
                monthly_limit = 0.00
                monthly_spent = 0.00
                is_custom = False
                notes = "لم يتم تعيين حدود بعد"
            
            # تطبيق فلتر نوع الحدود إذا كان محدداً
            if limit_type:
                if limit_type == 'custom' and not is_custom:
                    continue
                elif limit_type == 'default' and is_custom:
                    continue
            
            users_data.append({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'user_type': user_type_display,
                'daily_limit': daily_limit,
                'daily_spent': daily_spent,
                'monthly_limit': monthly_limit,
                'monthly_spent': monthly_spent,
                'is_custom': is_custom,
                'notes': notes
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في البحث: {str(e)}'
        }), 500

@financial_bp.route('/limits/global/add', methods=['POST'])
@login_required
@requires_permission('users.create')
def add_global_limit():
    """إضافة نوع عميل جديد مع حدوده الافتراضية"""
    try:
        # التحقق من Content-Type
        if request.content_type != 'application/json':
            return jsonify({
                'success': False,
                'message': 'يجب أن يكون Content-Type هو application/json'
            }), 400
            
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'لم يتم إرسال بيانات'
            }), 400
        
        user_type = data.get('user_type', '').strip().lower()
        display_name = data.get('display_name', '').strip()
        
        # التحقق من وجود البيانات المطلوبة قبل التحويل
        if 'daily_limit' not in data or 'monthly_limit' not in data:
            return jsonify({
                'success': False,
                'message': 'الحد اليومي والشهري مطلوبان'
            }), 400
            
        try:
            daily_limit = float(data['daily_limit'])
            monthly_limit = float(data['monthly_limit'])
        except (ValueError, TypeError) as e:
            print(f"Value conversion error: {e}")
            return jsonify({
                'success': False,
                'message': 'قيم الحدود يجب أن تكون أرقام صحيحة'
            }), 400
            
        description = data.get('description', '').strip()
        is_active = data.get('is_active', True)
        
        # التحقق من صحة البيانات
        if not user_type or not display_name:
            return jsonify({
                'success': False,
                'message': 'نوع العميل والاسم مطلوبان'
            }), 400
        
        if daily_limit <= 0 or monthly_limit <= 0:
            return jsonify({
                'success': False,
                'message': 'الحدود يجب أن تكون أكبر من الصفر'
            }), 400
        
        if monthly_limit < daily_limit:
            return jsonify({
                'success': False,
                'message': 'الحد الشهري يجب أن يكون أكبر من أو يساوي الحد اليومي'
            }), 400
        
        # التحقق من عدم وجود النوع مسبقاً
        existing_limit = GlobalLimits.query.filter_by(user_type=user_type).first()
        if existing_limit:
            print(f"Existing limit found for user_type: {user_type}")
            return jsonify({
                'success': False,
                'message': f'نوع العميل "{user_type}" موجود بالفعل'
            }), 400
        
        # إنشاء الحد الجديد
        new_global_limit = GlobalLimits(
            user_type=user_type,
            display_name=display_name,
            daily_limit_usd=Decimal(str(daily_limit)),
            monthly_limit_usd=Decimal(str(monthly_limit)),
            description=description,
            is_active=is_active
        )
        
        db.session.add(new_global_limit)
        db.session.commit()
        
        # تطبيق الحدود على العملاء الموجودين من نفس النوع
        from wallet_utils import apply_limits_to_existing_users
        applied_count = apply_limits_to_existing_users(user_type, daily_limit, monthly_limit)
        
        # تسجيل النشاط
        log_activity(
            employee_id=current_user.id,
            action='create_global_limits',
            details=f'إضافة نوع عميل جديد: {display_name} ({user_type}) - يومي {daily_limit}$، شهري {monthly_limit}$ - تم تطبيقه على {applied_count} عميل'
        )
        
        message = f'تم إنشاء نوع العميل "{display_name}" بنجاح'
        if applied_count > 0:
            message += f' وتم تطبيق الحدود على {applied_count} عميل موجود'
        
        print(f"Success: {message}")  # Debug log
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Exception in add_global_limit: {str(e)}")  # Debug log
        print(f"Exception type: {type(e)}")  # Debug log
        import traceback
        traceback.print_exc()  # Print full traceback
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء النوع الجديد: {str(e)}'
        }), 500

@financial_bp.route('/limits/global/<string:user_type>')
@login_required
@requires_permission('users.update')
def get_global_limit(user_type):
    """الحصول على الحدود الافتراضية لنوع مستخدم"""
    try:
        global_limit = GlobalLimits.query.filter_by(user_type=user_type).first()
        if not global_limit:
            return jsonify({
                'success': False,
                'message': 'لم يتم العثور على الحدود الافتراضية'
            }), 404
        
        return jsonify({
            'success': True,
            'limit': {
                'user_type': global_limit.user_type,
                'display_name': global_limit.display_name,
                'daily_limit_usd': float(global_limit.daily_limit_usd),
                'monthly_limit_usd': float(global_limit.monthly_limit_usd),
                'description': global_limit.description
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تحميل البيانات: {str(e)}'
        }), 500

@financial_bp.route('/limits/global/<string:user_type>', methods=['POST'])
@login_required
@requires_permission('users.update')
def update_global_limit(user_type):
    """تحديث الحدود الافتراضية لنوع مستخدم وتطبيقها على جميع المستخدمين من نفس النوع"""
    try:
        data = request.get_json()
        
        daily_limit = float(data['daily_limit'])
        monthly_limit = float(data['monthly_limit'])
        description = data.get('description', '')
        apply_to_existing = data.get('apply_to_existing', True)
        
        # التحقق من صحة البيانات
        if daily_limit <= 0 or monthly_limit <= 0:
            return jsonify({
                'success': False,
                'message': 'الحدود يجب أن تكون أكبر من الصفر'
            }), 400
        
        # تحديث الحدود وتطبيقها على المستخدمين
        from wallet_utils import update_global_limits_and_apply_to_users
        result = update_global_limits_and_apply_to_users(
            user_type, daily_limit, monthly_limit, description, apply_to_existing
        )
        
        if result['success']:
            # تسجيل النشاط
            log_activity(
                employee_id=current_user.id,
                action='update_global_limits',
                details=f'تحديث الحدود الافتراضية لـ {user_type}: يومي {daily_limit}$، شهري {monthly_limit}$ - تم تطبيقه على {result["updated_users_count"]} مستخدم'
            )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث الحدود: {str(e)}'
        }), 500

@financial_bp.route('/users/<int:user_id>/limits/update', methods=['POST'])
@login_required
@requires_permission('users.update')
def update_user_limits_route(user_id):
    """تحديث حدود مستخدم معين"""
    try:
        from wallet_utils import update_user_limits
        
        daily_limit = float(request.form.get('daily_limit', 0))
        monthly_limit = float(request.form.get('monthly_limit', 0))
        is_custom = request.form.get('is_custom') == 'true'
        
        if daily_limit <= 0 or monthly_limit <= 0:
            flash('يرجى إدخال حدود صحيحة أكبر من الصفر', 'error')
            return redirect(url_for('financial.user_limits_management'))
        
        # تحديث حدود المستخدم
        success = update_user_limits(user_id, daily_limit, monthly_limit, is_custom)
        
        if success:
            flash('تم تحديث حدود المستخدم بنجاح', 'success')
            
            # تسجيل النشاط
            from employee_utils import log_activity
            log_activity(
                current_user.id,
                'user_limits_update',
                f"تحديث حدود المستخدم {user_id}: يومي {daily_limit}, شهري {monthly_limit}"
            )
        else:
            flash('خطأ في تحديث حدود المستخدم', 'error')
            
    except Exception as e:
        flash(f'خطأ في تحديث حدود المستخدم: {str(e)}', 'error')
    
    return redirect(url_for('financial.user_limits_management'))

@financial_bp.route('/users/<int:user_id>/limits')
@login_required
@requires_permission('users.read')
def get_user_limits_details(user_id):
    """الحصول على تفاصيل حدود المستخدم"""
    try:
        user = User.query.get_or_404(user_id)
        from wallet_utils import get_user_limits, get_user_spending_summary
        user_limits = get_user_limits(user_id)
        
        if not user_limits:
            return jsonify({
                'success': False,
                'message': 'لم يتم العثور على حدود المستخدم'
            }), 404
        
        spending_summary = get_user_spending_summary(user_id)
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name
            },
            'limits': {
                'daily_limit': float(user_limits.daily_limit_usd),
                'monthly_limit': float(user_limits.monthly_limit_usd),
                'daily_spent': float(user_limits.daily_spent_usd),
                'monthly_spent': float(user_limits.monthly_spent_usd),
                'is_custom': user_limits.is_custom,
                'notes': getattr(user_limits, 'notes', '')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تحميل البيانات: {str(e)}'
        }), 500

@financial_bp.route('/users/<int:user_id>/limits', methods=['POST'])
@login_required
@requires_permission('users.update')
def update_user_limits_json(user_id):
    """تحديث حدود المستخدم عبر JSON"""
    try:
        logger.info(f"تحديث حدود المستخدم {user_id} - بدء المعالجة")
        data = request.get_json()
        logger.info(f"البيانات المستلمة: {data}")
        
        # التحقق من وجود البيانات
        if not data:
            logger.warning("لم يتم إرسال بيانات")
            return jsonify({
                'success': False,
                'message': 'لم يتم إرسال بيانات'
            }), 400
        
        # التحقق من وجود الحقول المطلوبة
        if 'daily_limit' not in data or 'monthly_limit' not in data:
            logger.warning(f"الحقول المطلوبة مفقودة. البيانات المرسلة: {list(data.keys())}")
            return jsonify({
                'success': False,
                'message': 'الحقول المطلوبة مفقودة'
            }), 400
        
        try:
            daily_limit = float(data['daily_limit'])
            monthly_limit = float(data['monthly_limit'])
            logger.info(f"الحدود المحولة: يومي={daily_limit}, شهري={monthly_limit}")
        except (ValueError, TypeError) as e:
            logger.error(f"خطأ في تحويل القيم: {e}")
            return jsonify({
                'success': False,
                'message': 'قيم الحدود يجب أن تكون أرقام صحيحة'
            }), 400
            
        notes = data.get('notes', '')
        reset_spending = data.get('reset_spending', False)
        
        # التحقق من صحة البيانات
        if daily_limit <= 0 or monthly_limit <= 0:
            logger.warning(f"قيم حدود غير صحيحة: يومي={daily_limit}, شهري={monthly_limit}")
            return jsonify({
                'success': False,
                'message': 'الحدود يجب أن تكون أكبر من الصفر'
            }), 400
        
        # التحقق من وجود المستخدم
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"المستخدم {user_id} غير موجود")
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            }), 404
        
        # تحديث الحدود
        logger.info(f"استدعاء update_user_limits للمستخدم {user_id}")
        from wallet_utils import update_user_limits
        success = update_user_limits(
            user_id=user_id,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            notes=notes,
            admin_id=current_user.id
        )
        
        if not success:
            logger.error(f"فشل في تحديث الحدود للمستخدم {user_id}")
            return jsonify({
                'success': False,
                'message': 'فشل في تحديث الحدود'
            }), 500

        logger.info(f"تم تحديث الحدود بنجاح للمستخدم {user_id}")
        
        # إعادة تعيين المنفق إذا طُلب ذلك
        if reset_spending:
            logger.info(f"إعادة تعيين المبالغ المنفقة للمستخدم {user_id}")
            user_limits = UserLimits.query.filter_by(user_id=user_id).first()
            if user_limits:
                user_limits.daily_spent_usd = 0.00
                user_limits.monthly_spent_usd = 0.00
                db.session.commit()
                logger.info(f"تم إعادة تعيين المبالغ المنفقة للمستخدم {user_id}")

        # تسجيل النشاط
        try:
            # البحث عن سجل الموظف للمستخدم الحالي
            from models import Employee
            employee = Employee.query.filter_by(user_id=current_user.id).first()
            if employee:
                log_activity(
                    employee_or_id=employee.id,
                    action='update_user_limits',
                    description=f'تحديث حدود المستخدم {user.email}: يومي {daily_limit}$، شهري {monthly_limit}$'
                )
            else:
                logger.warning(f"لم يتم العثور على سجل موظف للمستخدم {current_user.id}")
        except Exception as log_error:
            logger.error(f"خطأ في تسجيل النشاط: {str(log_error)}")
            # لا نريد أن يؤثر خطأ التسجيل على العملية الأساسية
        
        logger.info(f"تم إكمال تحديث حدود المستخدم {user_id} بنجاح")
        return jsonify({
            'success': True,
            'message': 'تم تحديث حدود المستخدم بنجاح'
        })
        
    except Exception as e:
        logger.error(f"خطأ في تحديث حدود المستخدم {user_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث الحدود: {str(e)}'
        }), 500@financial_bp.route('/users/<int:user_id>/limits/reset', methods=['POST'])
@login_required
@requires_permission('users.update')
def reset_user_limits_to_default(user_id):
    """إعادة تعيين حدود المستخدم للقيم الافتراضية"""
    try:
        user = User.query.get_or_404(user_id)
        user_limits = UserLimits.query.filter_by(user_id=user_id).first()
        
        if not user_limits:
            return jsonify({
                'success': False,
                'message': 'لم يتم العثور على حدود المستخدم'
            }), 404
        
        # تحديد نوع المستخدم
        if hasattr(user, 'user_type') and user.user_type == 'distributor':
            user_type = 'distributor'
        elif hasattr(user, 'customer_type') and user.customer_type == 'reseller':
            user_type = 'distributor'
        elif hasattr(user, 'kyc_status') and user.kyc_status == 'approved':
            user_type = 'kyc'
        else:
            user_type = 'normal'
        
        # الحصول على الحدود الافتراضية
        global_limit = GlobalLimits.query.filter_by(user_type=user_type, is_active=True).first()
        
        if global_limit:
            user_limits.daily_limit_usd = global_limit.daily_limit_usd
            user_limits.monthly_limit_usd = global_limit.monthly_limit_usd
            user_limits.is_custom = False
            user_limits.notes = None
            user_limits.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # تسجيل النشاط
            log_activity(
                employee_id=current_user.id,
                action='reset_user_limits',
                details=f'إعادة تعيين حدود المستخدم {user.email} للقيم الافتراضية'
            )
            
            return jsonify({
                'success': True,
                'message': 'تم إعادة تعيين الحدود للقيم الافتراضية بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'لم يتم العثور على الحدود الافتراضية لهذا النوع من المستخدمين'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في إعادة التعيين: {str(e)}'
        }), 500

@financial_bp.route('/users/<int:user_id>/transactions')
@login_required
@requires_permission('users.read')
def view_user_transactions(user_id):
    """عرض معاملات المستخدم"""
    try:
        user = User.query.get_or_404(user_id)
        
        page = request.args.get('page', 1, type=int)
        limit = 20
        offset = (page - 1) * limit
        
        transactions = WalletTransaction.query.filter_by(user_id=user_id).order_by(
            WalletTransaction.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return render_template('admin/user_transactions.html',
                             user=user,
                             transactions=transactions,
                             page=page)
        
    except Exception as e:
        flash(f'خطأ في عرض المعاملات: {str(e)}', 'error')
        return redirect(url_for('financial.user_limits_management'))
