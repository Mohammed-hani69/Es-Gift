from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file, render_template_string
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy import extract, func
import os
import json
import requests
import zipfile
import tempfile
import matplotlib
matplotlib.use('Agg')  # استخدام backend غير تفاعلي
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from urllib.parse import quote

from models import *
from utils import send_email
from employee_utils import requires_permission, requires_page_access, log_activity
from admin_pages import get_pages_for_js, ADMIN_PAGES

# إنشاء Blueprint للمسارات الإدارية
admin = Blueprint('admin', __name__, url_prefix='/admin')
admin_bp = admin  # إضافة alias للـ blueprint

@admin.route('/')
@login_required
@requires_page_access('admin.dashboard')
def dashboard():
    if not current_user.is_admin:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return redirect(url_for('main.index'))
    
    # إحصائيات
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    pending_kyc = User.query.filter_by(kyc_status='pending').count()
    
    # أحدث الطلبات (آخر 5)
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # أحدث المستخدمين (آخر 5)
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         pending_kyc=pending_kyc,
                         recent_orders=recent_orders,
                         recent_users=recent_users)

@admin.route('/products')
@login_required
@requires_page_access('admin.products')
def products():
    if not current_user.is_admin:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return redirect(url_for('main.index'))
    
    # فلتر حالة المنتجات
    status_filter = request.args.get('status', 'active')
    
    if status_filter == 'all':
        products = Product.query.all()
    elif status_filter == 'inactive':
        products = Product.query.filter_by(is_active=False).all()
    else:  # active or default
        products = Product.query.filter_by(is_active=True).all()
    
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order, Category.name).all()
    subcategories = Subcategory.query.filter_by(is_active=True).order_by(Subcategory.display_order, Subcategory.name).all()
    
    return render_template('admin/products.html', 
                         products=products, 
                         categories=categories, 
                         subcategories=subcategories,
                         status_filter=status_filter)

@admin.route('/users')
@login_required
@requires_page_access('admin.users')
def users():
    if not current_user.is_admin:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/create-user', methods=['GET', 'POST'])
@login_required
def admin_create_user():
    """إنشاء مستخدم جديد بواسطة الأدمن بدون الحاجة لرمز التحقق"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'GET':
        return render_template('admin/create_user.html')
    
    try:
        # جلب البيانات من النموذج
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        customer_type = request.form.get('customer_type', 'regular')
        is_admin = 'is_admin' in request.form
        
        # التحقق من صحة البيانات
        if not email or not password:
            flash('البريد الإلكتروني وكلمة المرور مطلوبان', 'error')
            return render_template('admin/create_user.html')
        
        # التحقق من صحة البريد الإلكتروني
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('البريد الإلكتروني غير صحيح', 'error')
            return render_template('admin/create_user.html')
        
        # التحقق من طول كلمة المرور
        if len(password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error')
            return render_template('admin/create_user.html')
        
        # التحقق من عدم وجود المستخدم مسبقاً
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('البريد الإلكتروني مسجل مسبقاً', 'error')
            return render_template('admin/create_user.html')
        
        # إنشاء المستخدم الجديد
        from werkzeug.security import generate_password_hash
        
        # إنشاء username فريد من البريد الإلكتروني
        username = email.split('@')[0]
        counter = 1
        original_username = username
        while User.query.filter_by(username=username).first():
            username = f"{original_username}{counter}"
            counter += 1
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name if full_name else None,
            phone=phone if phone else None,
            customer_type=customer_type,
            is_admin=is_admin,
            is_verified=True,  # تفعيل الحساب مباشرة بدون رمز التحقق
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.flush()  # للحصول على user.id قبل commit
        
        # إنشاء حدود المستخدم والمحفظة
        try:
            from wallet_utils import create_user_limits, get_or_create_wallet
            
            # إنشاء حدود المستخدم
            user_limits = create_user_limits(new_user)
            
            # إنشاء محفظة المستخدم
            wallet = get_or_create_wallet(new_user)
            
            db.session.commit()
            
            success_message = f'تم إنشاء حساب المستخدم "{email}" بنجاح!'
            if is_admin:
                success_message += ' (صلاحيات مدير)'
            
            flash(success_message, 'success')
            
            # في حالة طلب JSON (AJAX)
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({
                    'success': True,
                    'message': success_message,
                    'user': {
                        'id': new_user.id,
                        'email': new_user.email,
                        'full_name': new_user.full_name,
                        'customer_type': new_user.customer_type,
                        'is_admin': new_user.is_admin
                    }
                })
            
            return redirect(url_for('admin.users'))
            
        except Exception as wallet_error:
            db.session.rollback()
            error_msg = f'تم إنشاء المستخدم ولكن فشل في إعداد المحفظة: {str(wallet_error)}'
            flash(error_msg, 'warning')
            
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            
            return render_template('admin/create_user.html')
    
    except Exception as e:
        db.session.rollback()
        error_msg = f'حدث خطأ أثناء إنشاء المستخدم: {str(e)}'
        
        if request.headers.get('Content-Type') == 'application/json' or request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        
        flash(error_msg, 'error')
        return render_template('admin/create_user.html')

@admin.route('/kyc-requests')
@login_required
def kyc_requests():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    pending_kyc = User.query.filter_by(kyc_status='pending').all()
    return render_template('admin/kyc_requests.html', pending_kyc=pending_kyc)

@admin.route('/approve-kyc/<int:user_id>', methods=['GET', 'POST'])
@login_required
def approve_kyc(user_id):
    if not current_user.is_admin:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'غير مصرح'})
        return redirect(url_for('main.index'))
    
    try:
        user = User.query.get_or_404(user_id)
        user.kyc_status = 'approved'
        user.customer_type = 'kyc'
        db.session.commit()
        
        # تحديث أسعار المنتجات للمستخدم بعد الترقية
        from utils import refresh_user_data
        refresh_user_data(user)
        
        if request.method == 'POST':
            return jsonify({'success': True, 'message': 'تم الموافقة على طلب التحقق وتحديث الأسعار'})
        
        flash('تم الموافقة على طلب التحقق وتحديث الأسعار', 'success')
        return redirect(url_for('admin.kyc_requests'))
        
    except Exception as e:
        db.session.rollback()
        if request.method == 'POST':
            return jsonify({'success': False, 'message': str(e)})
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.kyc_requests'))

@admin.route('/reject-kyc/<int:user_id>', methods=['GET', 'POST'])
@login_required
def reject_kyc(user_id):
    if not current_user.is_admin:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'غير مصرح'})
        return redirect(url_for('main.index'))
    
    try:
        user = User.query.get_or_404(user_id)
        user.kyc_status = 'rejected'
        db.session.commit()
        
        if request.method == 'POST':
            return jsonify({'success': True, 'message': 'تم رفض طلب التحقق'})
        
        flash('تم رفض طلب التحقق', 'success')
        return redirect(url_for('admin.kyc_requests'))
        
    except Exception as e:
        db.session.rollback()
        if request.method == 'POST':
            return jsonify({'success': False, 'message': str(e)})
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.kyc_requests'))

@admin.route('/kyc-details/<int:user_id>')
@login_required
def kyc_details(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        user = User.query.get_or_404(user_id)
        
        user_data = {
            'id': user.id,
            'full_name': user.full_name,
            'email': user.email,
            'phone': user.phone,
            'birth_date': user.birth_date.strftime('%Y-%m-%d') if user.birth_date else None,
            'nationality': user.nationality,
            'kyc_status': user.kyc_status,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else None,
            'document_type': user.document_type,
            
            # Traditional document images (for backward compatibility)
            'id_front_image': user.id_front_image,
            'id_back_image': user.id_back_image,
            'selfie_image': user.selfie_image,
            
            # New KYC document images
            'passport_image': user.passport_image,
            'driver_license_image': user.driver_license_image,
            
            # Face verification photos
            'face_photo_front': user.face_photo_front,
            'face_photo_right': user.face_photo_right,
            'face_photo_left': user.face_photo_left
        }
        
        return jsonify({'success': True, 'user': user_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin.route('/system-test')
@login_required
def system_test():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    # جمع الإحصائيات
    products_count = Product.query.count()
    codes_count = ProductCode.query.count()
    available_codes = ProductCode.query.filter_by(is_used=False).count()
    sold_codes = ProductCode.query.filter_by(is_used=True).count()
    users_count = User.query.filter_by(is_admin=False).count()
    pending_kyc = User.query.filter_by(kyc_status='pending').count()
    verified_users = User.query.filter_by(kyc_status='approved').count()
    resellers = User.query.filter_by(customer_type='reseller').count()
    
    return render_template('admin/system_test.html',
                         mail_server=current_app.config.get('MAIL_SERVER'),
                         mail_port=current_app.config.get('MAIL_PORT'),
                         mail_use_tls=current_app.config.get('MAIL_USE_TLS'),
                         mail_username=current_app.config.get('MAIL_USERNAME'),
                         products_count=products_count,
                         codes_count=codes_count,
                         available_codes=available_codes,
                         sold_codes=sold_codes,
                         users_count=users_count,
                         pending_kyc=pending_kyc,
                         verified_users=verified_users,
                         resellers=resellers)

@admin.route('/test-email', methods=['POST'])
@login_required
def test_email():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'البريد الإلكتروني مطلوب'})
    
    # إنشاء إيميل تجريبي
    test_body = f"""
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
            <h1>اختبار نظام البريد الإلكتروني</h1>
            <p>Es-Gift - نظام بيع الفاوتشرز والكروت الرقمية</p>
        </div>
        
        <div style="padding: 30px; background: #f8f9fa;">
            <h2 style="color: #333;">مرحباً!</h2>
            <p style="font-size: 16px; line-height: 1.6; color: #666;">
                هذا إيميل تجريبي للتأكد من أن نظام البريد الإلكتروني يعمل بشكل صحيح.
            </p>
            
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                <h3 style="color: #667eea; margin-top: 0;">معلومات الاختبار:</h3>
                <ul style="color: #666;">
                    <li>نظام إرسال الإيميلات: <strong>Gmail SMTP</strong></li>
                    <li>حالة النظام: <strong>يعمل بنجاح</strong></li>
                    <li>وقت الإرسال: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></li>
                    <li>نوع الاختبار: <strong>اختبار إداري</strong></li>
                </ul>
            </div>
            
            <p style="color: #666;">
                إذا كنت ترى هذا الإيميل، فهذا يعني أن نظام البريد الإلكتروني يعمل بشكل مثالي!
            </p>
        </div>
        
        <div style="background: #333; color: white; padding: 20px; text-align: center;">
            <p style="margin: 0;">
                © 2024 Es-Gift. جميع الحقوق محفوظة.
            </p>
        </div>
    </div>
    """
    
    success = send_email(
        to_email=email,
        subject="اختبار نظام البريد الإلكتروني - Es-Gift",
        body=test_body
    )
    
    if success:
        return jsonify({'success': True, 'message': 'تم إرسال الإيميل التجريبي بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'فشل في إرسال الإيميل. تحقق من إعدادات البريد الإلكتروني'})

@admin.route('/update-customer-type', methods=['POST'])
@login_required
def update_customer_type():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    data = request.get_json()
    user_id = data.get('user_id')
    customer_type = data.get('customer_type')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'المستخدم غير موجود'})
    
    old_customer_type = user.customer_type
    user.customer_type = customer_type
    db.session.commit()
    
    # تحديث أسعار المنتجات للمستخدم بعد تغيير النوع
    from utils import refresh_user_data
    refresh_user_data(user)
    
    return jsonify({
        'success': True, 
        'message': f'تم تحديث نوع العميل من {old_customer_type} إلى {customer_type} وتحديث الأسعار بنجاح'
    })

@admin.route('/delete-user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'المستخدم غير موجود'})
        
        # منع حذف المدير الحالي
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'لا يمكن حذف حسابك الخاص'})
        
        # منع حذف المدراء
        if user.is_admin:
            return jsonify({'success': False, 'message': 'لا يمكن حذف حساب مدير'})
        
        # حذف البيانات المرتبطة أولاً
        try:
            # حذف الطلبات والعناصر المرتبطة
            orders = Order.query.filter_by(user_id=user_id).all()
            for order in orders:
                OrderItem.query.filter_by(order_id=order.id).delete()
                ProductCode.query.filter_by(order_id=order.id).update({'order_id': None, 'is_used': False})
                db.session.delete(order)
            
            # حذف المستخدم
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'تم حذف المستخدم بنجاح'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'خطأ في حذف البيانات المرتبطة: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/user/<int:user_id>')
@login_required
def user_detail(user_id):
    """عرض تفاصيل مستخدم محدد"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    # حساب إجمالي قيمة الطلبات للمستخدم
    total_spent = sum(order.total_amount for order in orders if order.total_amount)
    
    return render_template('admin/user_detail.html', user=user, orders=orders, total_spent=total_spent)

@admin.route('/orders')
@login_required
@requires_page_access('admin.orders')
def orders():
    if not current_user.is_admin:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return redirect(url_for('main.index'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@admin.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """عرض تفاصيل طلب محدد"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    order = Order.query.get_or_404(order_id)
    
    return render_template('admin/order_detail.html', order=order)

@admin.route('/order/<int:order_id>/json')
@login_required
def get_order_json(order_id):
    """جلب بيانات الطلب بصيغة JSON"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        order = Order.query.get_or_404(order_id)
        
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'total_amount': float(order.total_amount),
            'currency': order.currency,
            'order_status': order.order_status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'id': order.user.id,
                'full_name': order.user.full_name,
                'email': order.user.email
            },
            'items': []
        }
        
        for item in order.items:
            # جلب الأكواد المرتبطة بالطلب لهذا المنتج
            product_codes = ProductCode.query.filter_by(
                product_id=item.product.id,
                order_id=order.id
            ).all()
            
            order_data['items'].append({
                'id': item.id,
                'quantity': item.quantity,
                'price': float(item.price),
                'product': {
                    'id': item.product.id,
                    'name': item.product.name,
                    'codes': [{'id': code.id, 'code': code.code, 'order_id': code.order_id} for code in product_codes]
                }
            })
        
        return jsonify({'success': True, 'order': order_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/update-order-status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        order = Order.query.get_or_404(order_id)
        
        if new_status in ['pending', 'completed', 'cancelled', 'processing']:
            order.order_status = new_status
            db.session.commit()
            return jsonify({'success': True, 'message': 'تم تحديث حالة الطلب بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'حالة غير صحيحة'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/update-order-status-form/<int:order_id>', methods=['POST'])
@login_required
def update_order_status_form(order_id):
    """تحديث حالة الطلب من النموذج مع إمكانية إضافة الأكواد"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        
        if new_status not in ['pending', 'completed', 'cancelled', 'processing']:
            flash('حالة غير صحيحة', 'error')
            return redirect(url_for('admin.order_detail', order_id=order_id))
        
        # إذا كانت الحالة الجديدة "مكتمل" نحتاج للتحقق من الأكواد
        if new_status == 'completed':
            # التحقق من وجود أكواد للمنتجات التي تحتاجها
            codes_added = False
            missing_codes = False
            
            for item in order.items:
                # حساب الأكواد الموجودة لهذا المنتج
                existing_codes_count = ProductCode.query.filter_by(
                    product_id=item.product_id,
                    order_id=order_id
                ).count()
                
                # التحقق من الأكواد الجديدة المرسلة
                codes_field = f'product_{item.product_id}_codes'
                new_codes_text = request.form.get(codes_field, '').strip()
                
                if new_codes_text:
                    # إضافة الأكواد الجديدة
                    codes_list = [code.strip() for code in new_codes_text.split('\n') if code.strip()]
                    
                    for code_text in codes_list:
                        # التحقق من عدم تكرار الكود
                        existing_code = ProductCode.query.filter_by(code=code_text).first()
                        if not existing_code:
                            new_code = ProductCode(
                                product_id=item.product_id,
                                code=code_text,
                                order_id=order_id,
                                is_used=True,
                                used_at=datetime.utcnow()
                            )
                            db.session.add(new_code)
                            codes_added = True
                        else:
                            flash(f'الكود {code_text} موجود مسبقاً', 'warning')
                
                # التحقق من اكتمال الأكواد
                total_codes_after = ProductCode.query.filter_by(
                    product_id=item.product_id,
                    order_id=order_id
                ).count() + len([code.strip() for code in new_codes_text.split('\n') if code.strip()]) if new_codes_text else existing_codes_count
                if total_codes_after < item.quantity:
                    missing_codes = True
            
            # إذا كانت هناك أكواد ناقصة، تغيير الحالة إلى معلق
            if missing_codes:
                order.order_status = 'pending_codes'
                flash('تم حفظ الأكواد المتاحة. الطلب لا يزال معلقاً لوجود أكواد ناقصة', 'warning')
            else:
                order.order_status = new_status
                
                # إرسال البريد الإلكتروني مع الأكواد إذا كان الطلب مكتملاً
                if codes_added:
                    try:
                        from order_email_service import ProductCodeEmailService
                        email_service = ProductCodeEmailService()
                        
                        order_data = {
                            'order_number': order.order_number,
                            'customer_name': order.user.full_name or order.user.email,
                            'customer_email': order.user.email,
                            'order_date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'product_name': 'منتجات رقمية متنوعة',
                            'quantity': sum(item.quantity for item in order.items),
                            'total_amount': float(order.total_amount),
                            'currency': order.currency
                        }
                        
                        # جمع جميع الأكواد للطلب
                        product_codes = ProductCode.query.filter_by(order_id=order_id).all()
                        codes_list = [code.code for code in product_codes]
                        
                        success, message, excel_file_path = email_service.send_product_codes_email(order_data, codes_list)
                        
                        if success and excel_file_path:
                            order.excel_file_path = excel_file_path
                            flash('تم تحديث حالة الطلب وإرسال الأكواد بالبريد الإلكتروني بنجاح', 'success')
                        else:
                            flash(f'تم تحديث حالة الطلب ولكن فشل إرسال البريد: {message}', 'warning')
                            
                    except Exception as e:
                        flash(f'تم تحديث حالة الطلب ولكن فشل إرسال البريد: {str(e)}', 'warning')
                else:
                    flash('تم تحديث حالة الطلب بنجاح', 'success')
        else:
            # للحالات الأخرى (معلق، ملغي)
            order.order_status = new_status
            flash('تم تحديث حالة الطلب بنجاح', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin.route('/pending-orders')
@login_required
@requires_page_access('admin.orders')
def pending_orders():
    """عرض الطلبات المعلقة التي تحتاج أكواد"""
    if not current_user.is_admin:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return redirect(url_for('main.index'))
    
    # جلب الطلبات المعلقة
    pending_orders = Order.query.filter(
        Order.order_status.in_(['pending_codes', 'partial_codes'])
    ).order_by(Order.created_at.desc()).all()
    
    return render_template('admin/pending_orders.html', pending_orders=pending_orders)

@admin.route('/order/<int:order_id>/add-codes', methods=['POST'])
@login_required
def add_codes_to_order(order_id):
    """إضافة أكواد لطلب معلق"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        codes_data = data.get('codes', [])  # قائمة بالأكواد مع معرف المنتج
        
        if not codes_data:
            return jsonify({'success': False, 'message': 'لم يتم إرسال أكواد'})
        
        added_codes = []
        
        # إضافة الأكواد للمنتجات
        for code_info in codes_data:
            product_id = code_info.get('product_id')
            codes_list = code_info.get('codes', [])
            
            if not product_id or not codes_list:
                continue
                
            # التحقق من وجود المنتج في الطلب
            order_item = OrderItem.query.filter_by(order_id=order_id, product_id=product_id).first()
            if not order_item:
                continue
            
            # إضافة الأكواد
            for code_text in codes_list[:order_item.quantity]:  # فقط بعدد المطلوب
                # التحقق من عدم وجود الكود مسبقاً
                existing_code = ProductCode.query.filter_by(code=code_text.strip()).first()
                if existing_code:
                    continue
                
                # إنشاء كود جديد
                new_code = ProductCode(
                    product_id=product_id,
                    code=code_text.strip(),
                    order_id=order_id,
                    is_used=True,
                    used_at=datetime.utcnow()
                )
                db.session.add(new_code)
                added_codes.append(new_code)
        
        if added_codes:
            db.session.commit()
            
            # التحقق من اكتمال جميع الأكواد المطلوبة
            all_codes_complete = True
            for item in order.items:
                required_codes = item.quantity
                available_codes = ProductCode.query.filter_by(
                    product_id=item.product_id,
                    order_id=order_id
                ).count()
                
                if available_codes < required_codes:
                    all_codes_complete = False
                    break
            
            if all_codes_complete:
                # إرسال الإيميل مع الأكواد
                try:
                    from order_email_service import ProductCodeEmailService
                    email_service = ProductCodeEmailService()
                    
                    order_data = {
                        'order_number': order.order_number,
                        'customer_name': order.user.full_name or order.user.email,
                        'customer_email': order.user.email,
                        'order_date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'product_name': 'منتجات رقمية متنوعة',
                        'quantity': sum(item.quantity for item in order.items),
                        'total_amount': float(order.total_amount),
                        'currency': order.currency
                    }
                    
                    # جلب جميع أكواد الطلب
                    product_codes = [code.code for code in ProductCode.query.filter_by(order_id=order.id)]
                    
                    success, message, excel_file_path = email_service.send_product_codes_email(order_data, product_codes)
                    
                    if success and excel_file_path:
                        order.excel_file_path = excel_file_path
                        order.order_status = 'completed'
                        db.session.commit()
                        
                        return jsonify({
                            'success': True, 
                            'message': f'تم إضافة {len(added_codes)} كود وإرسال البريد الإلكتروني بنجاح',
                            'codes_sent': True
                        })
                    else:
                        order.order_status = 'partial_codes'
                        db.session.commit()
                        return jsonify({
                            'success': True, 
                            'message': f'تم إضافة {len(added_codes)} كود ولكن فشل إرسال البريد: {message}',
                            'codes_sent': False
                        })
                except Exception as e:
                    return jsonify({
                        'success': True, 
                        'message': f'تم إضافة {len(added_codes)} كود ولكن فشل إرسال البريد: {str(e)}',
                        'codes_sent': False
                    })
            else:
                order.order_status = 'partial_codes'
                db.session.commit()
                return jsonify({
                    'success': True, 
                    'message': f'تم إضافة {len(added_codes)} كود. الطلب يحتاج المزيد من الأكواد',
                    'codes_sent': False
                })
        else:
            return jsonify({'success': False, 'message': 'لم يتم إضافة أي أكواد صالحة'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/order/<int:order_id>/resend-email', methods=['POST'])
@login_required
def resend_order_email(order_id):
    """إعادة إرسال البريد الإلكتروني للطلب"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        order = Order.query.get_or_404(order_id)
        
        # التحقق من وجود أكواد للطلب
        product_codes = ProductCode.query.filter_by(order_id=order_id).all()
        if not product_codes:
            return jsonify({'success': False, 'message': 'لا توجد أكواد لهذا الطلب'})
        
        from order_email_service import ProductCodeEmailService
        email_service = ProductCodeEmailService()
        
        order_data = {
            'order_number': order.order_number,
            'customer_name': order.user.full_name or order.user.email,
            'customer_email': order.user.email,
            'order_date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'product_name': 'منتجات رقمية متنوعة',
            'quantity': sum(item.quantity for item in order.items),
            'total_amount': float(order.total_amount),
            'currency': order.currency
        }
        
        codes_list = [code.code for code in product_codes]
        success, message, excel_file_path = email_service.send_product_codes_email(order_data, codes_list)
        
        if success and excel_file_path:
            order.excel_file_path = excel_file_path
            if order.order_status in ['pending_codes', 'partial_codes']:
                order.order_status = 'completed'
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'تم إعادة إرسال البريد الإلكتروني بنجاح'})
        else:
            return jsonify({'success': False, 'message': f'فشل في إرسال البريد: {message}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/invoices')
@login_required
@requires_page_access('admin.invoices')
def invoices():
    """عرض جميع الفواتير في النظام"""
    if not current_user.is_admin:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    customer_type_filter = request.args.get('customer_type', '')
    search_query = request.args.get('search', '')
    
    query = Invoice.query
    
    # تطبيق الفلاتر
    if status_filter:
        query = query.filter(Invoice.payment_status == status_filter)
    
    if customer_type_filter:
        if customer_type_filter == 'regular_kyc':
            query = query.filter(Invoice.customer_type.in_(['regular', 'kyc']))
        else:
            query = query.filter(Invoice.customer_type == customer_type_filter)
    
    if search_query:
        query = query.filter(
            db.or_(
                Invoice.invoice_number.contains(search_query),
                Invoice.customer_name.contains(search_query),
                Invoice.customer_email.contains(search_query)
            )
        )
    
    invoices = query.order_by(Invoice.created_at.desc())\
                   .paginate(page=page, per_page=20, error_out=False)
    
    # إحصائيات الفواتير
    stats = {
        'total_invoices': Invoice.query.count(),
        'completed_invoices': Invoice.query.filter_by(payment_status='completed').count(),
        'pending_invoices': Invoice.query.filter_by(payment_status='pending').count(),
        'failed_invoices': Invoice.query.filter_by(payment_status='failed').count(),
        'total_revenue': db.session.query(func.sum(Invoice.total_amount))\
                                  .filter(Invoice.payment_status == 'completed').scalar() or 0
    }
    
    return render_template('admin/invoices.html', 
                         invoices=invoices, 
                         stats=stats,
                         status_filter=status_filter,
                         customer_type_filter=customer_type_filter,
                         search_query=search_query)

@admin.route('/invoice/<int:invoice_id>')
@login_required
@requires_page_access('admin.invoices')
def invoice_detail(invoice_id):
    """عرض تفاصيل فاتورة محددة"""
    if not current_user.is_admin:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return redirect(url_for('main.index'))
    
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('admin/invoice_detail.html', invoice=invoice)

@admin.route('/invoice/<int:invoice_id>/regenerate-pdf', methods=['POST'])
@login_required
@requires_page_access('admin.invoices')
def regenerate_invoice_pdf(invoice_id):
    """إعادة توليد ملف PDF للفاتورة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        from premium_english_invoice_service import PremiumEnglishInvoiceService as ModernInvoiceService
        
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # إعادة توليد ملف PDF بتصميم حديث
        pdf_path = ModernInvoiceService.generate_enhanced_pdf(invoice)
        if pdf_path:
            invoice.pdf_file_path = pdf_path
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'تم إعادة توليد ملف PDF للفاتورة بنجاح'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'فشل في إعادة توليد ملف PDF'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/invoice/<int:invoice_id>/send-email', methods=['POST'])
@login_required
@requires_page_access('admin.invoices')
def send_invoice_email(invoice_id):
    """إرسال الفاتورة عبر البريد الإلكتروني"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        data = request.get_json()
        email = data.get('email') if data else None
        
        from premium_english_invoice_service import PremiumEnglishInvoiceService as ModernInvoiceService
        
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # استخدام الإيميل المرسل من الواجهة أو إيميل العميل الافتراضي
        target_email = email or invoice.customer_email
        
        if not target_email:
            return jsonify({
                'success': False, 
                'message': 'لا يوجد بريد إلكتروني محدد للإرسال'
            })
        
        # إرسال الفاتورة عبر البريد الإلكتروني
        success = ModernInvoiceService.send_invoice_email(invoice, target_email)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'تم إرسال الفاتورة بنجاح إلى {target_email}'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'فشل في إرسال الفاتورة. تحقق من إعدادات البريد الإلكتروني'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/invoices/bulk-download', methods=['POST'])
@login_required
@requires_page_access('admin.invoices')
def bulk_download_invoices():
    """تحميل ملفات PDF للفواتير المحددة في ملف ZIP"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        import tempfile
        import zipfile
        import os
        from datetime import datetime
        from flask import send_file, after_this_request
        
        data = request.get_json()
        invoice_ids = data.get('invoice_ids', [])
        
        if not invoice_ids:
            return jsonify({'success': False, 'message': 'لم يتم تحديد أي فواتير'}), 400
        
        from premium_english_invoice_service import PremiumEnglishInvoiceService as ModernInvoiceService
        
        # إنشاء ملف ZIP مؤقت
        temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip')
        
        try:
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                added_files = 0
                
                for invoice_id in invoice_ids:
                    try:
                        invoice = Invoice.query.get(invoice_id)
                        if invoice:
                            # التأكد من وجود ملف PDF أو إنشاؤه
                            if not invoice.pdf_file_path:
                                pdf_path = ModernInvoiceService.generate_enhanced_pdf(invoice)
                                if pdf_path:
                                    invoice.pdf_file_path = pdf_path
                                    db.session.commit()
                            
                            # إضافة الملف إلى ZIP
                            if invoice.pdf_file_path:
                                # بناء المسار الكامل للملف
                                pdf_full_path = os.path.join(current_app.static_folder, invoice.pdf_file_path)
                                
                                if os.path.exists(pdf_full_path):
                                    filename = f"invoice_{invoice.invoice_number}.pdf"
                                    zipf.write(pdf_full_path, filename)
                                    added_files += 1
                                    print(f"✅ Added file: {filename}")
                                else:
                                    # إعادة إنشاء الملف إذا لم يكن موجوداً
                                    pdf_path = ModernInvoiceService.generate_enhanced_pdf(invoice)
                                    if pdf_path:
                                        invoice.pdf_file_path = pdf_path
                                        db.session.commit()
                                        pdf_full_path = os.path.join(current_app.static_folder, pdf_path)
                                        if os.path.exists(pdf_full_path):
                                            filename = f"invoice_{invoice.invoice_number}.pdf"
                                            zipf.write(pdf_full_path, filename)
                                            added_files += 1
                                            print(f"✅ Regenerated and added: {filename}")
                    except Exception as e:
                        current_app.logger.error(f"خطأ في معالجة الفاتورة {invoice_id}: {str(e)}")
                        print(f"❌ Error processing invoice {invoice_id}: {e}")
                        continue
                
                if added_files == 0:
                    os.close(temp_zip_fd)
                    os.unlink(temp_zip_path)
                    return jsonify({'success': False, 'message': 'لا توجد ملفات PDF متاحة'}), 400
            
            os.close(temp_zip_fd)
            
            # إرسال ملف ZIP
            zip_filename = f'ES-GIFT_Invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
            
            @after_this_request
            def cleanup(response):
                try:
                    if os.path.exists(temp_zip_path):
                        os.unlink(temp_zip_path)
                        print(f"🗑️ Cleaned up temporary ZIP file")
                except:
                    pass
                return response
            
            response = send_file(
                temp_zip_path,
                as_attachment=True,
                download_name=zip_filename,
                mimetype='application/zip'
            )
            
            print(f"✅ ZIP file created with {added_files} invoices: {zip_filename}")
            return response
            
        except Exception as zip_error:
            try:
                os.close(temp_zip_fd)
            except:
                pass
            if os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
            raise zip_error
            
    except Exception as e:
        current_app.logger.error(f"خطأ في تحميل الفواتير المجمع: {str(e)}")
        print(f"❌ Bulk download error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@admin.route('/invoices/bulk-email', methods=['POST'])
@login_required
@requires_page_access('admin.invoices')
def bulk_email_invoices():
    """إرسال الفواتير المحددة عبر البريد الإلكتروني"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        data = request.get_json()
        invoice_ids = data.get('invoice_ids', [])
        target_email = data.get('email')  # الإيميل المحدد من المستخدم
        
        if not invoice_ids:
            return jsonify({'success': False, 'message': 'لم يتم تحديد أي فواتير'}), 400
        
        if not target_email:
            return jsonify({'success': False, 'message': 'لم يتم تحديد بريد إلكتروني للإرسال'}), 400
        
        from premium_english_invoice_service import PremiumEnglishInvoiceService as ModernInvoiceService
        
        sent_count = 0
        failed_count = 0
        
        for invoice_id in invoice_ids:
            try:
                invoice = Invoice.query.get(invoice_id)
                if invoice:
                    # التأكد من وجود ملف PDF
                    if not invoice.pdf_file_path:
                        pdf_path = ModernInvoiceService.generate_enhanced_pdf(invoice)
                        if pdf_path:
                            invoice.pdf_file_path = pdf_path
                            db.session.commit()
                    elif invoice.pdf_file_path:
                        # التحقق من وجود الملف
                        pdf_full_path = os.path.join(current_app.static_folder, invoice.pdf_file_path)
                        if not os.path.exists(pdf_full_path):
                            # إعادة إنشاء الملف إذا لم يكن موجوداً
                            pdf_path = ModernInvoiceService.generate_enhanced_pdf(invoice)
                            if pdf_path:
                                invoice.pdf_file_path = pdf_path
                                db.session.commit()
                    
                    # إرسال الفاتورة
                    success = ModernInvoiceService.send_invoice_email(invoice, target_email)
                    
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                        
                else:
                    failed_count += 1
            except Exception as e:
                current_app.logger.error(f"خطأ في إرسال الفاتورة {invoice_id}: {str(e)}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'message': f'تم إرسال {sent_count} فاتورة بنجاح',
            'sent_count': sent_count,
            'failed_count': failed_count
        })
        
    except Exception as e:
        current_app.logger.error(f"خطأ في الإرسال المجمع للفواتير: {str(e)}")
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500

@admin.route('/articles')
@login_required
def articles():
    """إدارة المقالات"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    # جلب جميع المقالات مرتبة حسب تاريخ الإنشاء
    articles = Article.query.order_by(Article.created_at.desc()).all()
    
    return render_template('admin/articles.html', articles=articles)

@admin.route('/articles/new', methods=['GET', 'POST'])
@login_required
def new_article():
    """إضافة مقال جديد"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            author = request.form.get('author')
            is_published = request.form.get('is_published') == 'on'
            
            if not title or not content:
                flash('العنوان والمحتوى مطلوبان', 'error')
                return render_template('admin/article_form.html')
            
            # التعامل مع رفع الصورة
            image_url = None
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                # إضافة timestamp لجعل اسم الملف فريد
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                # التأكد من وجود مجلد الرفع
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads' , 'articles')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                # حفظ الصورة
                image_path = os.path.join(upload_folder, filename)
                image_file.save(image_path)
                image_url = filename
            
            # إنشاء المقال الجديد
            new_article = Article(
                title=title,
                content=content,
                author=author or current_user.full_name,
                image_url=image_url,
                is_published=is_published
            )
            
            db.session.add(new_article)
            db.session.commit()
            
            flash('تم إضافة المقال بنجاح', 'success')
            return redirect(url_for('admin.articles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            return render_template('admin/article_form.html')
    
    return render_template('admin/article_form.html')

@admin.route('/articles/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    """تعديل مقال"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    article = Article.query.get_or_404(article_id)
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            author = request.form.get('author')
            is_published = request.form.get('is_published') == 'on'
            
            if not title or not content:
                flash('العنوان والمحتوى مطلوبان', 'error')
                return render_template('admin/article_form.html', article=article)
            
            # التعامل مع رفع الصورة الجديدة
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                # حذف الصورة القديمة إذا كانت موجودة
                if article.image_url:
                    old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', article.image_url)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # حفظ الصورة الجديدة
                filename = secure_filename(image_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                image_path = os.path.join(upload_folder, filename)
                image_file.save(image_path)
                article.image_url = filename
            
            # تحديث المقال
            article.title = title
            article.content = content
            article.author = author or current_user.full_name
            article.is_published = is_published
            
            db.session.commit()
            
            flash('تم تحديث المقال بنجاح', 'success')
            return redirect(url_for('admin.articles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            return render_template('admin/article_form.html', article=article)
    
    return render_template('admin/article_form.html', article=article)

@admin.route('/articles/delete/<int:article_id>', methods=['POST'])
@login_required
def delete_article(article_id):
    """حذف مقال"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        article = Article.query.get_or_404(article_id)
        
        # حذف ملف الصورة إذا كان موجود
        if article.image_url:
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', article.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف المقال بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage-management')
@login_required
def homepage_management():
    """إدارة محتوى الصفحة الرئيسية"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    # جلب جميع العناصر من قاعدة البيانات
    main_offers = MainOffer.query.filter_by(is_active=True).order_by(MainOffer.display_order).all()
    gift_card_sections = GiftCardSection.query.filter_by(is_active=True).order_by(GiftCardSection.display_order).all()
    other_brands = OtherBrand.query.filter_by(is_active=True).order_by(OtherBrand.display_order).all()
    
    return render_template('admin/homepage_management.html',
                         main_offers=main_offers,
                         gift_card_sections=gift_card_sections,
                         other_brands=other_brands)

@admin.route('/homepage/main-offers/add', methods=['POST'])
@login_required
def add_main_offer():
    """إضافة عرض رئيسي جديد"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    try:
        title = request.form.get('title')
        link_url = request.form.get('link_url')
        display_order = request.form.get('display_order', 0)
        
        # التحقق من البيانات المطلوبة
        if not title or not link_url:
            flash('جميع الحقول مطلوبة', 'error')
            return redirect(url_for('admin.homepage_management'))
        
        # التعامل مع رفع الصورة
        image_file = request.files.get('image')
        if not image_file or not image_file.filename:
            flash('يرجى اختيار صورة', 'error')
            return redirect(url_for('admin.homepage_management'))
        
        # التحقق من نوع الملف
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        filename = secure_filename(image_file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_extension not in allowed_extensions:
            flash('نوع الملف غير مدعوم. يرجى استخدام PNG, JPG, JPEG, GIF, أو WEBP', 'error')
            return redirect(url_for('admin.homepage_management'))
        
        # إنشاء اسم ملف فريد
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        # التأكد من وجود مجلد الرفع
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'main-offers')
        os.makedirs(upload_folder, exist_ok=True)
        
        # حفظ الصورة
        image_path = os.path.join(upload_folder, filename)
        image_file.save(image_path)
        
        # إنشاء العرض الجديد
        new_offer = MainOffer(
            title=title,
            image_url=filename,  # حفظ اسم الملف فقط
            link_url=link_url,
            display_order=int(display_order),
            is_active=True
        )
        
        db.session.add(new_offer)
        db.session.commit()
        
        flash('تم إضافة العرض بنجاح', 'success')
        return redirect(url_for('admin.homepage_management'))
        
    except Exception as e:
        db.session.rollback()
        # حذف الصورة إذا تم رفعها ولكن فشل في حفظ البيانات
        if 'filename' in locals() and 'image_path' in locals() and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.homepage_management'))

@admin.route('/homepage/main-offers/edit/<int:offer_id>', methods=['POST'])
@login_required
def edit_main_offer(offer_id):
    """تعديل عرض رئيسي"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    try:
        offer = MainOffer.query.get_or_404(offer_id)
        
        # تحديث البيانات النصية
        title = request.form.get('title')
        link_url = request.form.get('link_url')
        display_order = request.form.get('display_order', 0)
        
        # التحقق من البيانات المطلوبة
        if not title or not link_url:
            flash('جميع الحقول مطلوبة', 'error')
            return redirect(url_for('admin.homepage_management'))
        
        offer.title = title
        offer.link_url = link_url
        offer.display_order = int(display_order)
        
        # تحديث الصورة إذا تم رفع صورة جديدة
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            if file and file.filename != '':
                # التحقق من نوع الملف
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                if file_extension not in allowed_extensions:
                    flash('نوع الملف غير مدعوم. يرجى استخدام PNG, JPG, JPEG, GIF, أو WEBP', 'error')
                    return redirect(url_for('admin.homepage_management'))
                

                
                # حذف الصورة القديمة
                if offer.image_url:
                    old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'main-offers', offer.image_url)
                    if os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except:
                            pass  # تجاهل خطأ حذف الملف القديم
                
                # حفظ الصورة الجديدة
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                # إنشاء مجلد uploads إذا لم يكن موجوداً
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'main-offers')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                offer.image_url = filename
        
        db.session.commit()
        
        flash('تم تحديث العرض بنجاح', 'success')
        return redirect(url_for('admin.homepage_management'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.homepage_management'))

@admin.route('/homepage/main-offers/<int:offer_id>/edit', methods=['GET'])
@login_required
def edit_main_offer_form(offer_id):
    """عرض نموذج تعديل العرض"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    try:
        offer = MainOffer.query.get_or_404(offer_id)
        
        # جلب جميع العناصر من قاعدة البيانات
        main_offers = MainOffer.query.filter_by(is_active=True).order_by(MainOffer.display_order).all()
        gift_card_sections = GiftCardSection.query.filter_by(is_active=True).order_by(GiftCardSection.display_order).all()
        other_brands = OtherBrand.query.filter_by(is_active=True).order_by(OtherBrand.display_order).all()
        
        return render_template('admin/homepage_management.html',
                             main_offers=main_offers,
                             gift_card_sections=gift_card_sections,
                             other_brands=other_brands,
                             edit_offer=offer)
        
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.homepage_management'))

@admin.route('/homepage/main-offers/<int:offer_id>/delete', methods=['POST'])
@login_required
def delete_main_offer(offer_id):
    """حذف عرض رئيسي من خلال نموذج"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    try:
        offer = MainOffer.query.get_or_404(offer_id)
        
        # حذف ملف الصورة
        if offer.image_url:
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'main-offers', offer.image_url)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass  # تجاهل خطأ حذف الملف
        
        db.session.delete(offer)
        db.session.commit()
        
        flash('تم حذف العرض بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
        
    return redirect(url_for('admin.homepage_management'))


@admin.route('/homepage/gift-cards/add', methods=['POST'])
@login_required
def add_gift_card():
    """إضافة بطاقة هدايا جديدة"""
    if not current_user.is_admin:
        flash('غير مصرح', 'error')
        return redirect(url_for('admin.homepage_management'))
    
    try:
        title = request.form.get('title')
        link_url = request.form.get('link_url')
        card_type = request.form.get('card_type', 'gift')
        display_order = request.form.get('display_order', 0)
        
        # التعامل مع رفع الصورة
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            
            # التحقق من صحة الملف
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                # إضافة timestamp لجعل اسم الملف فريد
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                # التأكد من وجود مجلد الرفع
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'gift-cards')
                os.makedirs(upload_folder, exist_ok=True)
                
                # حفظ الصورة
                image_path = os.path.join(upload_folder, filename)
                image_file.save(image_path)
                
                # إنشاء بطاقة الهدايا الجديدة
                new_card = GiftCardSection(
                    title=title,
                    image_url=filename,
                    link_url=link_url,
                    card_type=card_type,
                    display_order=int(display_order),
                    is_active=True
                )
                
                db.session.add(new_card)
                db.session.commit()
                
                flash('تم إضافة بطاقة الهدايا بنجاح', 'success')
            else:
                flash('نوع الملف غير مدعوم. يرجى اختيار صورة (PNG, JPG, JPEG, GIF, WEBP)', 'error')
        else:
            flash('يرجى اختيار صورة', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('admin.homepage_management'))

@admin.route('/homepage/gift-cards/delete/<int:card_id>', methods=['DELETE'])
@login_required
def delete_gift_card(card_id):
    """حذف بطاقة هدايا"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        card = GiftCardSection.query.get_or_404(card_id)
        
        # حذف ملف الصورة
        if card.image_url:
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', card.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(card)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف بطاقة الهدايا بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage/gift-cards/<int:card_id>')
@login_required
def get_gift_card(card_id):
    """جلب بيانات بطاقة هدايا للتعديل"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        card = GiftCardSection.query.get_or_404(card_id)
        
        return jsonify({
            'success': True,
            'card': {
                'id': card.id,
                'title': card.title,
                'image_url': card.image_url,
                'link_url': card.link_url,
                'card_type': getattr(card, 'card_type', 'gift'),
                'display_order': card.display_order,
                'is_active': card.is_active
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage/gift-cards/<int:card_id>/edit', methods=['POST'])
@login_required
def edit_gift_card(card_id):
    """تعديل بطاقة هدايا"""
    if not current_user.is_admin:
        flash('غير مصرح', 'error')
        return redirect(url_for('admin.homepage_management'))
    
    try:
        card = GiftCardSection.query.get_or_404(card_id)
        
        # تحديث البيانات الأساسية
        card.title = request.form.get('title')
        card.link_url = request.form.get('link_url')
        card.card_type = request.form.get('card_type', 'gift')
        card.display_order = int(request.form.get('display_order', 0))
        
        # التعامل مع الصورة الجديدة إذا تم رفعها
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            
            # التحقق من صحة الملف
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                # حذف الصورة القديمة
                if card.image_url:
                    old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'gift-cards', card.image_url)
                    if os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except:
                            pass  # تجاهل خطأ حذف الملف القديم
                
                # حفظ الصورة الجديدة
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                # إنشاء مجلد uploads إذا لم يكن موجوداً
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'gift-cards')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                card.image_url = filename
        
        db.session.commit()
        flash('تم تحديث بطاقة الهدايا بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
        
    return redirect(url_for('admin.homepage_management'))

@admin.route('/homepage/other-brands/add', methods=['POST'])
@login_required
def add_other_brand():
    """إضافة ماركة أخرى جديدة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        name = request.form.get('name')
        link_url = request.form.get('link_url')
        display_order = request.form.get('display_order', 0)
        
        # التعامل مع رفع الصورة
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            # إضافة timestamp لجعل اسم الملف فريد
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            # التأكد من وجود مجلد الرفع
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads' ,'other-brands')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # حفظ الصورة
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            
            # إنشاء الماركة الجديدة
            new_brand = OtherBrand(
                name=name,
                image_url=filename,
                link_url=link_url,
                display_order=int(display_order),
                is_active=True
            )
            
            db.session.add(new_brand)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'تم إضافة الماركة بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'يرجى اختيار صورة'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage/other-brands/delete/<int:brand_id>', methods=['DELETE'])
@login_required
def delete_other_brand(brand_id):
    """حذف ماركة أخرى"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        brand = OtherBrand.query.get_or_404(brand_id)
        
        # حذف ملف الصورة
        if brand.image_url:
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', brand.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(brand)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف الماركة بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/categories')
@login_required
def categories():
    """إدارة الأقسام والفئات"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    categories = Category.query.order_by(Category.display_order, Category.name).all()
    subcategories = Subcategory.query.order_by(Subcategory.display_order, Subcategory.name).all()
    
    return render_template('admin/categories.html', 
                         categories=categories, 
                         subcategories=subcategories)

@admin.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    """إضافة قسم رئيسي جديد"""
    if not current_user.is_admin:
        flash('غير مصرح', 'error')
        return redirect(url_for('admin.categories'))
    
    try:
        name = request.form.get('name')
        name_en = request.form.get('name_en')
        description = request.form.get('description')
        icon_class = request.form.get('icon_class')
        display_order = request.form.get('display_order', 0)
        is_active = 'is_active' in request.form
        
        if not name:
            flash('اسم القسم مطلوب', 'error')
            return redirect(url_for('admin.categories'))
        
        # التعامل مع رفع الصورة
        image_filename = None
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            # فحص حجم الملف (5 ميجابايت كحد أقصى)
            image_file.seek(0, os.SEEK_END)
            file_size = image_file.tell()
            image_file.seek(0)  # إعادة تعيين المؤشر
            
            if file_size > 5 * 1024 * 1024:  # 5 ميجابايت
                flash('حجم الصورة كبير جداً. الحد الأقصى المسموح 5 ميجابايت', 'error')
                return redirect(url_for('admin.categories'))
            
            filename = secure_filename(image_file.filename)
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                image_filename = timestamp + filename
                
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'categories')
                os.makedirs(upload_folder, exist_ok=True)
                
                image_path = os.path.join(upload_folder, image_filename)
                image_file.save(image_path)
            else:
                flash('نوع الملف غير مدعوم. يرجى اختيار صورة (PNG, JPG, JPEG, GIF, WEBP)', 'error')
                return redirect(url_for('admin.categories'))
        
        # إنشاء القسم الجديد
        new_category = Category(
            name=name,
            name_en=name_en,
            description=description,
            icon_class=icon_class,
            image_url=image_filename,
            display_order=int(display_order),
            is_active=is_active
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        flash(f'تم إضافة القسم "{name}" بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('admin.categories'))

@admin.route('/categories/<int:category_id>')
@login_required
def get_category(category_id):
    """جلب بيانات قسم للتعديل"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        category = Category.query.get_or_404(category_id)
        
        return jsonify({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'name_en': category.name_en,
                'description': category.description,
                'icon_class': category.icon_class,
                'image_url': category.image_url,
                'display_order': category.display_order,
                'is_active': category.is_active
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/categories/<int:category_id>/edit', methods=['POST'])
@login_required
def edit_category(category_id):
    """تعديل قسم رئيسي"""
    if not current_user.is_admin:
        flash('غير مصرح', 'error')
        return redirect(url_for('admin.categories'))
    
    try:
        category = Category.query.get_or_404(category_id)
        
        # تحديث البيانات الأساسية
        category.name = request.form.get('name')
        category.name_en = request.form.get('name_en')
        category.description = request.form.get('description')
        category.icon_class = request.form.get('icon_class')
        category.display_order = int(request.form.get('display_order', 0))
        category.is_active = 'is_active' in request.form
        
        # التعامل مع الصورة الجديدة إذا تم رفعها
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            # فحص حجم الملف (5 ميجابايت كحد أقصى)
            image_file.seek(0, os.SEEK_END)
            file_size = image_file.tell()
            image_file.seek(0)  # إعادة تعيين المؤشر
            
            if file_size > 5 * 1024 * 1024:  # 5 ميجابايت
                flash('حجم الصورة كبير جداً. الحد الأقصى المسموح 5 ميجابايت', 'error')
                return redirect(url_for('admin.categories'))
            
            filename = secure_filename(image_file.filename)
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                # حذف الصورة القديمة
                if category.image_url:
                    old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'categories', category.image_url)
                    if os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except:
                            pass
                
                # حفظ الصورة الجديدة
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                new_filename = timestamp + filename
                
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'categories')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, new_filename)
                image_file.save(file_path)
                category.image_url = new_filename
        
        db.session.commit()
        flash(f'تم تحديث القسم "{category.name}" بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('admin.categories'))

@admin.route('/categories/<int:category_id>/delete', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """حذف قسم رئيسي"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        category = Category.query.get_or_404(category_id)
        
        category_name = category.name
        
        # حذف الصورة إذا كانت موجودة
        if category.image_url:
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'categories', category.image_url)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم حذف القسم "{category_name}" بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/subcategories/add', methods=['POST'])
@login_required
def add_subcategory():
    """إضافة قسم فرعي جديد"""
    if not current_user.is_admin:
        flash('غير مصرح', 'error')
        return redirect(url_for('admin.categories'))
    
    try:
        name = request.form.get('name')
        name_en = request.form.get('name_en')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        icon_class = request.form.get('icon_class')
        display_order = request.form.get('display_order', 0)
        is_active = 'is_active' in request.form
        
        if not name or not category_id:
            flash('اسم القسم الفرعي والقسم الرئيسي مطلوبان', 'error')
            return redirect(url_for('admin.categories'))
        
        # التعامل مع رفع الصورة
        image_filename = None
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            # فحص حجم الملف (5 ميجابايت كحد أقصى)
            image_file.seek(0, os.SEEK_END)
            file_size = image_file.tell()
            image_file.seek(0)  # إعادة تعيين المؤشر
            
            if file_size > 5 * 1024 * 1024:  # 5 ميجابايت
                flash('حجم الصورة كبير جداً. الحد الأقصى المسموح 5 ميجابايت', 'error')
                return redirect(url_for('admin.categories'))
            
            filename = secure_filename(image_file.filename)
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                image_filename = timestamp + filename
                
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'subcategories')
                os.makedirs(upload_folder, exist_ok=True)
                
                image_path = os.path.join(upload_folder, image_filename)
                image_file.save(image_path)
        
        # إنشاء القسم الفرعي الجديد
        new_subcategory = Subcategory(
            name=name,
            name_en=name_en,
            description=description,
            category_id=int(category_id),
            icon_class=icon_class,
            image_url=image_filename,
            display_order=int(display_order),
            is_active=is_active
        )
        
        db.session.add(new_subcategory)
        db.session.commit()
        
        flash(f'تم إضافة القسم الفرعي "{name}" بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('admin.categories'))

@admin.route('/subcategories/<int:subcategory_id>')
@login_required
def get_subcategory(subcategory_id):
    """جلب بيانات قسم فرعي للتعديل"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        subcategory = Subcategory.query.get_or_404(subcategory_id)
        
        return jsonify({
            'success': True,
            'subcategory': {
                'id': subcategory.id,
                'name': subcategory.name,
                'name_en': subcategory.name_en,
                'description': subcategory.description,
                'category_id': subcategory.category_id,
                'icon_class': subcategory.icon_class,
                'image_url': subcategory.image_url,
                'display_order': subcategory.display_order,
                'is_active': subcategory.is_active
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/categories/<int:category_id>/subcategories')
@login_required
def get_subcategories_by_category(category_id):
    """جلب الأقسام الفرعية لقسم رئيسي معين"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        subcategories = Subcategory.query.filter_by(
            category_id=category_id, 
            is_active=True
        ).order_by(Subcategory.display_order, Subcategory.name).all()
        
        subcategories_data = []
        for subcategory in subcategories:
            subcategories_data.append({
                'id': subcategory.id,
                'name': subcategory.name,
                'name_en': subcategory.name_en,
                'description': subcategory.description,
                'category_id': subcategory.category_id,
                'is_active': subcategory.is_active
            })
        
        return jsonify({
            'success': True,
            'subcategories': subcategories_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/subcategories/<int:subcategory_id>/edit', methods=['POST'])
@login_required
def edit_subcategory(subcategory_id):
    """تعديل قسم فرعي"""
    if not current_user.is_admin:
        flash('غير مصرح', 'error')
        return redirect(url_for('admin.categories'))
    
    try:
        subcategory = Subcategory.query.get_or_404(subcategory_id)
        
        # تحديث البيانات الأساسية
        subcategory.name = request.form.get('name')
        subcategory.name_en = request.form.get('name_en')
        subcategory.description = request.form.get('description')
        subcategory.category_id = int(request.form.get('category_id'))
        subcategory.icon_class = request.form.get('icon_class')
        subcategory.display_order = int(request.form.get('display_order', 0))
        subcategory.is_active = 'is_active' in request.form
        
        # التعامل مع الصورة الجديدة إذا تم رفعها
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            # فحص حجم الملف (5 ميجابايت كحد أقصى)
            image_file.seek(0, os.SEEK_END)
            file_size = image_file.tell()
            image_file.seek(0)  # إعادة تعيين المؤشر
            
            if file_size > 5 * 1024 * 1024:  # 5 ميجابايت
                flash('حجم الصورة كبير جداً. الحد الأقصى المسموح 5 ميجابايت', 'error')
                return redirect(url_for('admin.categories'))
            
            filename = secure_filename(image_file.filename)
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                # حذف الصورة القديمة
                if subcategory.image_url:
                    old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'subcategories', subcategory.image_url)
                    if os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except:
                            pass
                
                # حفظ الصورة الجديدة
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                new_filename = timestamp + filename
                
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'subcategories')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, new_filename)
                image_file.save(file_path)
                subcategory.image_url = new_filename
        
        db.session.commit()
        flash(f'تم تحديث القسم الفرعي "{subcategory.name}" بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('admin.categories'))

@admin.route('/subcategories/<int:subcategory_id>/delete', methods=['DELETE'])
@login_required
def delete_subcategory(subcategory_id):
    """حذف قسم فرعي"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        subcategory = Subcategory.query.get_or_404(subcategory_id)
        subcategory_name = subcategory.name
        
        # حذف الصورة إذا كانت موجودة
        if subcategory.image_url:
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'subcategories', subcategory.image_url)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass
        
        db.session.delete(subcategory)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم حذف القسم الفرعي "{subcategory_name}" بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/employees')
@login_required
@requires_page_access('admin.employees')
def employees():
    """صفحة إدارة الموظفين"""
    if not current_user.is_admin:
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
            return redirect(url_for('main.index'))
    
    try:
        # جلب جميع الموظفين مع بياناتهم
        employees = Employee.query.join(User).join(Role).all()
        
        # جلب الأدوار المتاحة
        roles = Role.query.filter_by(is_active=True).all()
        
        # جلب المستخدمين غير الموظفين (متاحين للإضافة)
        employed_user_ids = [emp.user_id for emp in employees]
        available_users = User.query.filter(~User.id.in_(employed_user_ids)).all()
        
        # الحصول على قائمة الأقسام المختلفة
        departments = list(set([emp.department for emp in employees if emp.department]))
        
        # تمرير قائمة الصفحات للقالب
        admin_pages = get_pages_for_js()
        
        return render_template('admin/employees.html',
                             employees=employees,
                             roles=roles,
                             available_users=available_users,
                             departments=departments,
                             admin_pages=admin_pages)
                             
    except Exception as e:
        current_app.logger.error(f"Error in employees route: {e}")
        flash('حدث خطأ أثناء تحميل بيانات الموظفين', 'error')
        return redirect(url_for('admin.dashboard'))

@admin.route('/employees/add', methods=['POST'])
@login_required
def add_employee():
    """إضافة موظف جديد"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        data = request.get_json()
        
        # التحقق من صحة البيانات
        from employee_utils import validate_employee_data, generate_employee_id
        errors = validate_employee_data(data)
        if errors:
            return jsonify({'success': False, 'message': ', '.join(errors)})
        
        # التحقق من أن المستخدم ليس موظفاً بالفعل
        existing = Employee.query.filter_by(user_id=data['user_id']).first()
        if existing:
            return jsonify({'success': False, 'message': 'هذا المستخدم موظف بالفعل'})
        
        # إنشاء رقم موظف جديد
        employee_id = generate_employee_id()
        
        # إنشاء الموظف الجديد
        employee = Employee(
            user_id=data['user_id'],
            role_id=data['role_id'],
            employee_id=employee_id,
            department=data['department'],
            position=data['position'],
            hire_date=datetime.strptime(data['hire_date'], '%Y-%m-%d').date() if data.get('hire_date') else None,
            salary=float(data['salary']) if data.get('salary') else None,
            manager_id=data.get('manager_id') if data.get('manager_id') else None,
            work_location=data.get('work_location'),
            can_access_reports=data.get('can_access_reports', False),
            can_manage_currencies=data.get('can_manage_currencies', False),
            can_manage_categories=data.get('can_manage_categories', False),
            max_discount_percent=int(data.get('max_discount_percent', 0))
        )
        
        db.session.add(employee)
        db.session.commit()
        
        # تسجيل النشاط
        from employee_utils import log_activity
        log_activity(employee, 'employee_created', f'تم إنشاء حساب موظف جديد: {employee.user.email}')
        
        return jsonify({'success': True, 'message': f'تم إضافة الموظف بنجاح برقم {employee_id}'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding employee: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء إضافة الموظف'})

@admin.route('/employees/<int:employee_id>')
@login_required
def get_employee_details(employee_id):
    """جلب تفاصيل موظف محدد"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # تحضير HTML للعرض
        html_content = f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h4 style="color: #ff0033; margin-bottom: 15px;">المعلومات الشخصية</h4>
                <div style="background: #333; padding: 15px; border-radius: 8px;">
                    <p><strong>الاسم:</strong> {employee.user.full_name or 'غير محدد'}</p>
                    <p><strong>البريد الإلكتروني:</strong> {employee.user.email}</p>
                    <p><strong>الهاتف:</strong> {employee.user.phone or 'غير محدد'}</p>
                    <p><strong>رقم الموظف:</strong> <span style="color: #ff0033;">{employee.employee_id}</span></p>
                    <p><strong>تاريخ التسجيل:</strong> {employee.user.created_at.strftime('%Y-%m-%d') if employee.user.created_at else 'غير محدد'}</p>
                </div>
            </div>
            
            <div>
                <h4 style="color: #ff0033; margin-bottom: 15px;">معلومات الوظيفة</h4>
                <div style="background: #333; padding: 15px; border-radius: 8px;">
                    <p><strong>القسم:</strong> {employee.department}</p>
                    <p><strong>المنصب:</strong> {employee.position}</p>
                    <p><strong>الدور:</strong> <span class="badge badge-{'danger' if employee.role.is_admin else 'primary'}">{employee.role.display_name}</span></p>
                    <p><strong>المدير المباشر:</strong> {employee.manager.user.full_name if employee.manager else 'لا يوجد'}</p>
                    <p><strong>تاريخ التوظيف:</strong> {employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else 'غير محدد'}</p>
                    <p><strong>مكان العمل:</strong> {employee.work_location or 'غير محدد'}</p>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <h4 style="color: #ff0033; margin-bottom: 15px;">الصلاحيات الإضافية</h4>
            <div style="background: #333; padding: 15px; border-radius: 8px;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                    <p>الوصول للتقارير: <span class="badge badge-{'success' if employee.can_access_reports else 'secondary'}">{'نعم' if employee.can_access_reports else 'لا'}</span></p>
                    <p>إدارة العملات: <span class="badge badge-{'success' if employee.can_manage_currencies else 'secondary'}">{'نعم' if employee.can_manage_currencies else 'لا'}</span></p>
                    <p>إدارة التصنيفات: <span class="badge badge-{'success' if employee.can_manage_categories else 'secondary'}">{'نعم' if employee.can_manage_categories else 'لا'}</span></p>
                    <p>أقصى نسبة خصم: <span style="color: #ff0033;">{employee.max_discount_percent}%</span></p>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <h4 style="color: #ff0033; margin-bottom: 15px;">حالة الحساب</h4>
            <div style="background: #333; padding: 15px; border-radius: 8px;">
                <p><strong>حالة الموظف:</strong> <span class="badge badge-{'success' if employee.status == 'active' else 'warning' if employee.status == 'suspended' else 'danger'}">{'نشط' if employee.status == 'active' else 'معلق' if employee.status == 'suspended' else 'منتهي الخدمة'}</span></p>
                <p><strong>تاريخ الإنشاء:</strong> {employee.created_at.strftime('%Y-%m-%d %H:%M') if employee.created_at else 'غير محدد'}</p>
                <p><strong>آخر تحديث:</strong> {employee.updated_at.strftime('%Y-%m-%d %H:%M') if employee.updated_at else 'غير محدد'}</p>
            </div>
        </div>
        """
        
        return jsonify({'success': True, 'html': html_content})
        
    except Exception as e:
        current_app.logger.error(f"Error getting employee details: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء جلب بيانات الموظف'})

@admin.route('/employees/<int:employee_id>/permissions')
@login_required
def get_employee_permissions(employee_id):
    """جلب صلاحيات الموظف"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # جلب جميع الصلاحيات مجمعة حسب الفئة
        from employee_utils import get_permissions_by_category, get_user_permissions
        permissions_by_category = get_permissions_by_category()
        user_permissions = get_user_permissions(employee.user_id)
        user_permission_names = [perm['name'] for perm in user_permissions]
        
        html_content = f"""
        <div style="margin-bottom: 20px;">
            <h4 style="color: #ff0033;">إدارة صلاحيات: {employee.user.full_name or employee.user.email}</h4>
            <p style="color: #ccc;">الدور الحالي: <span class="badge badge-{'danger' if employee.role.is_admin else 'primary'}">{employee.role.display_name}</span></p>
        </div>
        """
        
        for category, permissions in permissions_by_category.items():
            category_names = {
                'users': 'إدارة المستخدمين',
                'products': 'إدارة المنتجات',
                'orders': 'إدارة الطلبات',
                'categories': 'إدارة التصنيفات',
                'currencies': 'إدارة العملات',
                'reports': 'التقارير',
                'employees': 'إدارة الموظفين',
                'roles': 'إدارة الأدوار',
                'system': 'إعدادات النظام',
                'content': 'إدارة المحتوى'
            }
            
            category_display = category_names.get(category, category)
            
            html_content += f"""
            <div style="margin-bottom: 20px; background: #333; padding: 15px; border-radius: 8px;">
                <h5 style="color: #ff0033; margin-bottom: 15px; border-bottom: 1px solid #444; padding-bottom: 8px;">
                    <i class="fas fa-folder"></i> {category_display}
                </h5>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px;">
            """
            
            for permission in permissions:
                is_checked = permission['name'] in user_permission_names
                html_content += f"""
                <label style="display: flex; align-items: center; gap: 8px; padding: 8px; background: #444; border-radius: 5px; cursor: pointer;">
                    <input type="checkbox" data-permission-id="{permission['id']}" {'checked' if is_checked else ''} 
                           style="transform: scale(1.2);">
                    <div>
                        <div style="color: #fff; font-weight: 500;">{permission['display_name']}</div>
                        <div style="color: #ccc; font-size: 0.8em;">{permission['description']}</div>
                    </div>
                </label>
                """
            
            html_content += """
                </div>
            </div>
            """
        
        return jsonify({'success': True, 'html': html_content})
        
    except Exception as e:
        current_app.logger.error(f"Error getting employee permissions: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء جلب الصلاحيات'})

@admin.route('/employees/<int:employee_id>/permissions', methods=['POST'])
@login_required  
def update_employee_permissions(employee_id):
    """تحديث صلاحيات الموظف"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        employee = Employee.query.get_or_404(employee_id)
        data = request.get_json()
        permissions = data.get('permissions', [])
        
        # حذف الصلاحيات الحالية للموظف
        EmployeePermission.query.filter_by(employee_id=employee_id).delete()
        
        # إضافة الصلاحيات الجديدة
        for perm_data in permissions:
            if perm_data.get('granted'):
                emp_permission = EmployeePermission(
                    employee_id=employee_id,
                    permission_id=perm_data['permission_id'],
                    granted=True,
                    granted_by=current_user.id,
                    reason='تحديث من لوحة التحكم'
                )
                db.session.add(emp_permission)
        
        db.session.commit()
        
        # تسجيل النشاط
        from employee_utils import log_activity
        log_activity(employee, 'permissions_updated', f'تم تحديث صلاحيات الموظف من قبل {current_user.email}')
        
        return jsonify({'success': True, 'message': 'تم تحديث الصلاحيات بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating employee permissions: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء تحديث الصلاحيات'})

@admin.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    """تعديل بيانات موظف"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'GET':
        # إرجاع بيانات الموظف للتعديل
        employee_data = {
            'user_id': employee.user_id,
            'role_id': employee.role_id,
            'department': employee.department,
            'position': employee.position,
            'hire_date': employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else '',
            'salary': float(employee.salary) if employee.salary else '',
            'manager_id': employee.manager_id,
            'work_location': employee.work_location,
            'can_access_reports': employee.can_access_reports,
            'can_manage_currencies': employee.can_manage_currencies,
            'can_manage_categories': employee.can_manage_categories,
            'max_discount_percent': employee.max_discount_percent
        }
        return jsonify({'success': True, 'employee': employee_data})
    
    try:
        data = request.get_json()
        
        # التحقق من صحة البيانات
        from employee_utils import validate_employee_data
        errors = validate_employee_data(data, employee_id)
        if errors:
            return jsonify({'success': False, 'message': ', '.join(errors)})
        
        # تحديث البيانات
        employee.role_id = data['role_id']
        employee.department = data['department']
        employee.position = data['position']
        employee.hire_date = datetime.strptime(data['hire_date'], '%Y-%m-%d').date() if data.get('hire_date') else None
        employee.salary = float(data['salary']) if data.get('salary') else None
        employee.manager_id = data.get('manager_id') if data.get('manager_id') else None
        employee.work_location = data.get('work_location')
        employee.can_access_reports = data.get('can_access_reports', False)
        employee.can_manage_currencies = data.get('can_manage_currencies', False)
        employee.can_manage_categories = data.get('can_manage_categories', False)
        employee.max_discount_percent = int(data.get('max_discount_percent', 0))
        
        db.session.commit()
        
        # تسجيل النشاط
        from employee_utils import log_activity
        log_activity(employee, 'employee_updated', f'تم تحديث بيانات الموظف من قبل {current_user.email}')
        
        return jsonify({'success': True, 'message': 'تم تحديث بيانات الموظف بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing employee: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء تحديث بيانات الموظف'})

@admin.route('/employees/<int:employee_id>/status', methods=['POST'])
@login_required
def update_employee_status(employee_id):
    """تحديث حالة الموظف"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        employee = Employee.query.get_or_404(employee_id)
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['active', 'suspended', 'terminated']:
            return jsonify({'success': False, 'message': 'حالة غير صالحة'})
        
        old_status = employee.status
        employee.status = new_status
        db.session.commit()
        
        # تسجيل النشاط
        from employee_utils import log_activity
        status_names = {'active': 'نشط', 'suspended': 'معلق', 'terminated': 'منتهي الخدمة'}
        log_activity(employee, 'status_changed', 
                    f'تم تغيير الحالة من {status_names.get(old_status, old_status)} إلى {status_names.get(new_status, new_status)}')
        
        return jsonify({'success': True, 'message': f'تم تحديث حالة الموظف إلى {status_names.get(new_status, new_status)}'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating employee status: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء تحديث حالة الموظف'})

@admin.route('/employees/<int:employee_id>/delete', methods=['DELETE'])
@login_required
def delete_employee(employee_id):
    """حذف موظف"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # منع حذف الموظف الحالي
        if employee.user_id == current_user.id:
            return jsonify({'success': False, 'message': 'لا يمكن حذف حسابك الخاص'})
        
        # حذف البيانات المرتبطة
        EmployeePermission.query.filter_by(employee_id=employee_id).delete()
        ActivityLog.query.filter_by(employee_id=employee_id).delete()
        
        # تسجيل النشاط قبل الحذف
        employee_name = employee.user.full_name or employee.user.email
        
        # حذف الموظف
        db.session.delete(employee)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم حذف الموظف {employee_name} بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting employee: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف الموظف'})

@admin.route('/currencies')
@login_required
@login_required
def currencies():
    """إدارة العملات"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    currencies = Currency.query.all()
    return render_template('admin/currencies.html', currencies=currencies)

@admin.route('/add-currency', methods=['GET', 'POST'])
@login_required
def add_currency():
    """إضافة عملة جديدة"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            code = request.form.get('code', '').upper().strip()
            name = request.form.get('name', '').strip()
            symbol = request.form.get('symbol', '').strip()
            exchange_rate = request.form.get('exchange_rate')
            
            # التحقق من البيانات المطلوبة
            if not all([code, name, symbol, exchange_rate]):
                flash('جميع الحقول مطلوبة', 'error')
                return render_template('admin/add_currency.html')
            
            # التحقق من أن رمز العملة مكون من 3 أحرف
            if len(code) != 3:
                flash('رمز العملة يجب أن يكون مكون من 3 أحرف', 'error')
                return render_template('admin/add_currency.html')
            
            # التحقق من وجود العملة مسبقاً
            existing_currency = Currency.query.filter_by(code=code).first()
            if existing_currency:
                flash(f'العملة {code} موجودة مسبقاً', 'error')
                return render_template('admin/add_currency.html')
            
            # التحقق من صحة سعر الصرف
            try:
                exchange_rate = float(exchange_rate)
                if exchange_rate <= 0:
                    flash('سعر الصرف يجب أن يكون أكبر من الصفر', 'error')
                    return render_template('admin/add_currency.html')
            except ValueError:
                flash('سعر الصرف يجب أن يكون رقم صحيح', 'error')
                return render_template('admin/add_currency.html')
            
            # إنشاء العملة الجديدة
            new_currency = Currency(
                code=code,
                name=name,
                symbol=symbol,
                exchange_rate=exchange_rate,
                is_active=True
            )
            
            db.session.add(new_currency)
            db.session.commit()
            
            flash(f'تم إضافة العملة {name} ({code}) بنجاح', 'success')
            return redirect(url_for('admin.currencies'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            return render_template('admin/add_currency.html')
    
    return render_template('admin/add_currency.html')

@admin.route('/toggle-currency/<int:currency_id>', methods=['POST'])
@login_required
def toggle_currency_status(currency_id):
    """تفعيل/إلغاء تفعيل العملة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        currency = Currency.query.get_or_404(currency_id)
        
        # لا يمكن إلغاء تفعيل الريال السعودي
        if currency.code == 'SAR':
            return jsonify({'success': False, 'message': 'لا يمكن إلغاء تفعيل الريال السعودي'})
        
        currency.is_active = not currency.is_active
        db.session.commit()
        
        status = 'تم تفعيل' if currency.is_active else 'تم إلغاء تفعيل'
        return jsonify({
            'success': True, 
            'message': f'{status} العملة {currency.name}',
            'is_active': currency.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/delete-currency/<int:currency_id>', methods=['POST'])
@login_required
def delete_currency(currency_id):
    """حذف العملة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        currency = Currency.query.get_or_404(currency_id)
        
        # لا يمكن حذف الريال السعودي
        if currency.code == 'SAR':
            return jsonify({'success': False, 'message': 'لا يمكن حذف الريال السعودي'})
        
        db.session.delete(currency)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'تم حذف العملة {currency.name} بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/payment-gateways')
@login_required
def payment_gateways():
    """إدارة بوابات الدفع"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    gateways = PaymentGateway.query.all()
    return render_template('admin/payment_gateways.html', gateways=gateways)

@admin.route('/payment-gateways/update-fee/<int:gateway_id>', methods=['POST'])
@login_required
def update_gateway_fee(gateway_id):
    """تحديث عمولة بوابة الدفع"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        gateway = PaymentGateway.query.get_or_404(gateway_id)
        
        fee_percentage = request.form.get('fee_percentage')
        if fee_percentage is None:
            return jsonify({'success': False, 'message': 'نسبة العمولة مطلوبة'})
        
        # التحقق من صحة نسبة العمولة
        try:
            fee_percentage = float(fee_percentage)
            if fee_percentage < 0 or fee_percentage > 100:
                return jsonify({'success': False, 'message': 'نسبة العمولة يجب أن تكون بين 0 و 100'})
        except ValueError:
            return jsonify({'success': False, 'message': 'نسبة العمولة يجب أن تكون رقم صحيح'})
        
        # تحديث نسبة العمولة
        gateway.fee_percentage = fee_percentage
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'تم تحديث عمولة {gateway.name} إلى {fee_percentage}%'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/payment-gateways/toggle-status/<int:gateway_id>', methods=['POST'])
@login_required
def toggle_gateway_status(gateway_id):
    """تفعيل/إلغاء تفعيل بوابة الدفع"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        gateway = PaymentGateway.query.get_or_404(gateway_id)
        
        # تبديل حالة التفعيل
        gateway.is_active = not gateway.is_active
        db.session.commit()
        
        status_text = 'تم تفعيل' if gateway.is_active else 'تم إلغاء تفعيل'
        
        return jsonify({
            'success': True,
            'message': f'{status_text} بوابة {gateway.name}',
            'is_active': gateway.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/payment-gateways/add', methods=['POST'])
@login_required
def add_payment_gateway():
    """إضافة بوابة دفع جديدة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        gateway_name = request.form.get('gateway_name')
        fee_percentage = request.form.get('fee_percentage')
        
        if not gateway_name or not fee_percentage:
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'})
        
        # التحقق من عدم وجود بوابة بنفس الاسم
        existing_gateway = PaymentGateway.query.filter_by(name=gateway_name).first()
        if existing_gateway:
            return jsonify({'success': False, 'message': 'يوجد بوابة دفع بنفس الاسم'})
        
        # التحقق من صحة نسبة العمولة
        try:
            fee_percentage = float(fee_percentage)
            if fee_percentage < 0 or fee_percentage > 100:
                return jsonify({'success': False, 'message': 'نسبة العمولة يجب أن تكون بين 0 و 100'})
        except ValueError:
            return jsonify({'success': False, 'message': 'نسبة العمولة يجب أن تكون رقم صحيح'})
        
        # إنشاء بوابة دفع جديدة
        new_gateway = PaymentGateway(
            name=gateway_name,
            fee_percentage=fee_percentage,
            is_active=True
        )
        
        db.session.add(new_gateway)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'تم إضافة بوابة {gateway_name} بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/api-settings')
@login_required
def api_settings():
    """إعدادات API - إعادة توجيه للوحة تحكم API الجديدة"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    return redirect(url_for('api_admin.api_settings'))

# ...existing code...

@admin.route('/reports')
@login_required
def reports():
    """إعادة توجيه إلى نظام التقارير الجديد"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    # إعادة توجيه إلى نظام التقارير الجديد
    return redirect(url_for('reports.reports_dashboard'))
    
    try:
        # الإحصائيات الأساسية
        total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.order_status == 'completed'
        ).scalar() or 0
        
        total_orders = db.session.query(func.count(Order.id)).scalar() or 0
        completed_orders = db.session.query(func.count(Order.id)).filter(
            Order.order_status == 'completed'
        ).scalar() or 0
        pending_orders = db.session.query(func.count(Order.id)).filter(
            Order.order_status == 'pending'
        ).scalar() or 0
        cancelled_orders = db.session.query(func.count(Order.id)).filter(
            Order.order_status == 'cancelled'
        ).scalar() or 0
        
        # إحصائيات المستخدمين المحسنة
        total_users = db.session.query(func.count(User.id)).scalar() or 0
        regular_users = db.session.query(func.count(User.id)).filter(
            User.customer_type == 'regular'
        ).scalar() or 0
        kyc_users = db.session.query(func.count(User.id)).filter(
            User.customer_type == 'kyc'
        ).scalar() or 0
        reseller_users = db.session.query(func.count(User.id)).filter(
            User.customer_type == 'reseller'
        ).scalar() or 0
        
        # إحصائيات KYC
        kyc_pending = db.session.query(func.count(User.id)).filter(
            User.kyc_status == 'pending'
        ).scalar() or 0
        kyc_approved = db.session.query(func.count(User.id)).filter(
            User.kyc_status == 'approved'
        ).scalar() or 0
        kyc_rejected = db.session.query(func.count(User.id)).filter(
            User.kyc_status == 'rejected'
        ).scalar() or 0
        
        # إحصائيات المنتجات والأكواد
        active_products = db.session.query(func.count(Product.id)).filter(
            Product.is_active == True
        ).scalar() or 0
        inactive_products = db.session.query(func.count(Product.id)).filter(
            Product.is_active == False
        ).scalar() or 0
        
        available_codes = db.session.query(func.count(ProductCode.id)).filter(
            ProductCode.is_used == False
        ).scalar() or 0
        used_codes = db.session.query(func.count(ProductCode.id)).filter(
            ProductCode.is_used == True
        ).scalar() or 0
        
        # إحصائيات العملات
        active_currencies = db.session.query(func.count(Currency.id)).filter(
            Currency.is_active == True
        ).scalar() or 0
        total_currencies = db.session.query(func.count(Currency.id)).scalar() or 0
        
        # إحصائيات بوابات الدفع
        active_gateways = db.session.query(func.count(PaymentGateway.id)).filter(
            PaymentGateway.is_active == True
        ).scalar() or 0
        total_gateways = db.session.query(func.count(PaymentGateway.id)).scalar() or 0
        
        # إحصائيات الفئات والفئات الفرعية
        total_categories = db.session.query(func.count(Category.id)).scalar() or 0
        total_subcategories = db.session.query(func.count(Subcategory.id)).scalar() or 0
        
        
        
        total_articles = db.session.query(func.count(Article.id)).scalar() or 0
        published_articles = db.session.query(func.count(Article.id)).filter(
            Article.is_published == True
        ).scalar() or 0
        
        # البيانات الشهرية للـ 12 شهر الماضية
        monthly_data = []
        for i in range(11, -1, -1):
            month_date = datetime.now().replace(day=1) - timedelta(days=30 * i)
            
            # الإيرادات الشهرية
            month_revenue = db.session.query(func.sum(Order.total_amount)).filter(
                Order.order_status == 'completed',
                extract('month', Order.created_at) == month_date.month,
                extract('year', Order.created_at) == month_date.year
            ).scalar() or 0
            
            # الطلبات الشهرية
            month_orders = db.session.query(func.count(Order.id)).filter(
                Order.order_status == 'completed',
                extract('month', Order.created_at) == month_date.month,
                extract('year', Order.created_at) == month_date.year
            ).scalar() or 0
            
            # المستخدمين الجدد شهرياً
            month_users = db.session.query(func.count(User.id)).filter(
                extract('month', User.created_at) == month_date.month,
                extract('year', User.created_at) == month_date.year
            ).scalar() or 0
            
            # المنتجات الجديدة شهرياً
            month_products = db.session.query(func.count(Product.id)).filter(
                extract('month', Product.created_at) == month_date.month,
                extract('year', Product.created_at) == month_date.year
            ).scalar() or 0
            
            monthly_data.append({
                'month': month_date.strftime('%Y-%m'),
                'month_name': month_date.strftime('%B %Y'),
                'revenue': float(month_revenue),
                'orders': month_orders,
                'users': month_users,
                'products': month_products
            })
        
        # أفضل المنتجات مبيعاً
        top_products = db.session.query(
            Product.name,
            Product.regular_price.label('price'),  # استخدام السعر العادي كسعر أساسي
            func.count(OrderItem.id).label('total_sold'),
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
        ).select_from(Product).join(OrderItem, Product.id == OrderItem.product_id).join(Order, OrderItem.order_id == Order.id).filter(
            Order.order_status == 'completed'
        ).group_by(Product.id, Product.name, Product.regular_price).order_by(
            func.count(OrderItem.id).desc()
        ).limit(10).all()
        
        # أداء العملاء حسب النوع
        customer_performance = db.session.query(
            User.customer_type,
            func.count(Order.id).label('orders'),
            func.sum(Order.total_amount).label('revenue')
        ).select_from(User).join(Order, User.id == Order.user_id).filter(
            Order.order_status == 'completed'
        ).group_by(User.customer_type).all()
        
        # أداء الفئات (بناءً على حقل category في Product)
        categories_performance = db.session.query(
            Product.category.label('name'),
            func.count(OrderItem.id).label('total_sold'),
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
        ).select_from(Product).join(
            OrderItem, Product.id == OrderItem.product_id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.order_status == 'completed',
            Product.category.isnot(None)
        ).group_by(Product.category).all()
        
        # أداء بوابات الدفع (بناءً على payment_method في Order)
        payment_gateways_performance = db.session.query(
            Order.payment_method.label('gateway_name'),
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_revenue'),
            func.avg(Order.total_amount).label('avg_order_value')
        ).filter(
            Order.order_status == 'completed',
            Order.payment_method.isnot(None)
        ).group_by(Order.payment_method).all()
        
        # إحصائيات يومية للأسبوع الماضي
        daily_data = []
        for i in range(6, -1, -1):
            day_date = datetime.now().date() - timedelta(days=i)
            
            day_revenue = db.session.query(func.sum(Order.total_amount)).filter(
                Order.order_status == 'completed',
                func.date(Order.created_at) == day_date
            ).scalar() or 0
            
            day_orders = db.session.query(func.count(Order.id)).filter(
                Order.order_status == 'completed',
                func.date(Order.created_at) == day_date
            ).scalar() or 0
            
            day_users = db.session.query(func.count(User.id)).filter(
                func.date(User.created_at) == day_date
            ).scalar() or 0
            
            daily_data.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'day_name': day_date.strftime('%A'),
                'revenue': float(day_revenue),
                'orders': day_orders,
                'users': day_users
            })
        
        # إعداد بيانات الرسوم البيانية
        chart_data = {
            # البيانات الشهرية
            'monthly_labels': [item['month_name'] for item in monthly_data],
            'monthly_revenue': [item['revenue'] for item in monthly_data],
            'monthly_orders': [item['orders'] for item in monthly_data],
            'monthly_users': [item['users'] for item in monthly_data],
            'monthly_products': [item['products'] for item in monthly_data],
            
            # البيانات اليومية
            'daily_labels': [item['day_name'] for item in daily_data],
            'daily_revenue': [item['revenue'] for item in daily_data],
            'daily_orders': [item['orders'] for item in daily_data],
            'daily_users': [item['users'] for item in daily_data],
            
            # أفضل المنتجات
            'products_labels': [product.name for product in top_products],
            'products_sales': [int(product.total_sold) for product in top_products],
            'products_revenue': [float(product.total_revenue) for product in top_products],
            
            # أنواع العملاء
            'customer_types_labels': [
                'عملاء عاديون' if perf.customer_type == 'regular' 
                else 'عملاء موثقون' if perf.customer_type == 'kyc' 
                else 'موزعون' for perf in customer_performance
            ],
            'customer_types_orders': [int(perf.orders) for perf in customer_performance],
            'customer_types_revenue': [float(perf.revenue) for perf in customer_performance],
            
            # الفئات
            'categories_labels': [cat.name for cat in categories_performance],
            'categories_sales': [int(cat.total_sold) for cat in categories_performance],
            'categories_revenue': [float(cat.total_revenue) for cat in categories_performance],
            
            # بوابات الدفع
            'gateways_labels': [gw.gateway_name for gw in payment_gateways_performance],
            'gateways_orders': [int(gw.total_orders) for gw in payment_gateways_performance],
            'gateways_revenue': [float(gw.total_revenue) for gw in payment_gateways_performance],
            
            # إحصائيات KYC
            'kyc_labels': ['معلق', 'مقبول', 'مرفوض'],
            'kyc_data': [kyc_pending, kyc_approved, kyc_rejected],
            
            # إحصائيات المنتجات
            'products_status_labels': ['نشطة', 'غير نشطة'],
            'products_status_data': [active_products, inactive_products],
            
            # إحصائيات الأكواد
            'codes_labels': ['متاحة', 'مستخدمة'],
            'codes_data': [available_codes, used_codes],
            
            # إحصائيات العملات
            'currencies_labels': ['نشطة', 'غير نشطة'],
            'currencies_data': [active_currencies, total_currencies - active_currencies],
        }
        
        return render_template('admin/reports.html',
            # الإحصائيات الأساسية
            total_revenue=total_revenue,
            total_orders=total_orders,
            completed_orders=completed_orders,
            pending_orders=pending_orders,
            cancelled_orders=cancelled_orders,
            avg_order_value=float(total_revenue / max(completed_orders, 1)),
            
            # إحصائيات المستخدمين
            total_users=total_users,
            regular_users=regular_users,
            kyc_users=kyc_users,
            reseller_users=reseller_users,
            
            # إحصائيات KYC
            kyc_pending=kyc_pending,
            kyc_approved=kyc_approved,
            kyc_rejected=kyc_rejected,
            
            # إحصائيات المنتجات
            active_products=active_products,
            inactive_products=inactive_products,
            available_codes=available_codes,
            used_codes=used_codes,
            low_stock_count=0,  # يمكن حسابها لاحقاً
            
            # إحصائيات النظام
            total_categories=total_categories,
            total_subcategories=total_subcategories,
            total_offers=0,
            active_offers=0,
            total_articles=total_articles,
            published_articles=published_articles,
            active_currencies=active_currencies,
            total_currencies=total_currencies,
            active_gateways=active_gateways,
            total_gateways=total_gateways,
            
            # البيانات التفصيلية
            monthly_data=monthly_data,
            daily_data=daily_data,
            top_products=top_products,
            customer_performance=customer_performance,
            categories_performance=categories_performance,
            payment_gateways_performance=payment_gateways_performance,
            
            # بيانات الرسوم البيانية
            chart_data=chart_data,
            now=datetime.now()
        )
        
    except Exception as e:
        print(f"Error in reports: {e}")
        flash('حدث خطأ في تحميل التقارير', 'error')
        return redirect(url_for('admin.dashboard'))

# ...existing code...

@admin.route('/update-currency-rate/<int:currency_id>', methods=['POST'])
@login_required
def update_currency_rate(currency_id):
    """تحديث سعر صرف العملة"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    try:
        currency = Currency.query.get_or_404(currency_id)
        
        exchange_rate = request.form.get('exchange_rate')
        if not exchange_rate:
            flash('سعر الصرف مطلوب', 'error')
            return redirect(url_for('admin.currencies'))
        
        # التحقق من صحة سعر الصرف
        try:
            exchange_rate = float(exchange_rate)
            if exchange_rate <= 0:
                flash('سعر الصرف يجب أن يكون أكبر من الصفر', 'error')
                return redirect(url_for('admin.currencies'))
        except ValueError:
            flash('سعر الصرف يجب أن يكون رقم صحيح', 'error')
            return redirect(url_for('admin.currencies'))
        
        # تحديث سعر الصرف
        currency.exchange_rate = exchange_rate
        db.session.commit()
        
        flash(f'تم تحديث سعر صرف {currency.name} إلى {exchange_rate} بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('admin.currencies'))

@admin.route('/test-currency/<currency_code>')
@login_required
def test_currency(currency_code):
    """اختبار تحويل العملة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        from utils import convert_currency
        
        # تحويل 100 ريال إلى العملة المحددة
        converted_amount = convert_currency(100, 'SAR', currency_code)
        
        return jsonify({
            'success': True, 
            'message': f'100 ريال سعودي = {converted_amount} {currency_code}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/convert-currency', methods=['POST'])
@login_required
def convert_currency_route():
    """تحويل العملة عبر Ajax"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        from_currency = data.get('from_currency', 'SAR')
        to_currency = data.get('to_currency', 'SAR')
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'المبلغ يجب أن يكون أكبر من الصفر'})
        
        from utils import convert_currency
        converted_amount = convert_currency(amount, from_currency, to_currency)
        
        # الحصول على معلومات العملات
        from_currency_obj = Currency.query.filter_by(code=from_currency).first()
        to_currency_obj = Currency.query.filter_by(code=to_currency).first()
        
        return jsonify({
            'success': True,
            'converted_amount': float(converted_amount),
            'from_currency': {
                'code': from_currency,
                'symbol': from_currency_obj.symbol if from_currency_obj else from_currency,
                'name': from_currency_obj.name if from_currency_obj else from_currency
            },
            'to_currency': {
                'code': to_currency,
                'symbol': to_currency_obj.symbol if to_currency_obj else to_currency,
                'name': to_currency_obj.name if to_currency_obj else to_currency
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

# ===== روتات إدارة المنتجات =====

@admin.route('/products', methods=['POST'])
@login_required
def add_product():
    """إضافة منتج جديد"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # جلب البيانات من النموذج
        name = request.form.get('name')
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')  # القسم الرئيسي الجديد
        subcategory_id = request.form.get('subcategory_id')  # القسم الفرعي الجديد
        category = request.form.get('category')  # الفئة القديمة للتوافق
        region = request.form.get('region', '')
        value = request.form.get('value', '')
        purchase_price = request.form.get('purchase_price')
        regular_price = request.form.get('regular_price')
        kyc_price = request.form.get('kyc_price') or regular_price
        reseller_price = request.form.get('reseller_price') or regular_price
        stock_quantity = request.form.get('stock_quantity', '0')
        instructions = request.form.get('instructions', '')
        expiry_date = request.form.get('expiry_date')
        is_active = request.form.get('is_active') == 'on'
        
        # جلب أنواع المستخدمين المختارة
        user_type_visibility = request.form.get('user_type_visibility', 'regular,kyc,reseller')
        
        # التحقق من البيانات المطلوبة
        if not name or not regular_price or not purchase_price:
            flash('الحقول المطلوبة: اسم المنتج، سعر الشراء، السعر العادي', 'error')
            return redirect(url_for('admin.products'))
        
        # التحقق من وجود قسم رئيسي أو فئة قديمة
        if not category_id and not category:
            flash('يجب اختيار قسم رئيسي أو فئة', 'error')
            return redirect(url_for('admin.products'))
        
        # التحقق من صحة الأسعار
        try:
            purchase_price_float = float(purchase_price)
            regular_price_float = float(regular_price)
            kyc_price_float = float(kyc_price) if kyc_price else regular_price_float
            reseller_price_float = float(reseller_price) if reseller_price else regular_price_float
            stock_quantity_int = int(stock_quantity) if stock_quantity else 0
        except ValueError:
            flash('يرجى إدخال أسعار وكميات صحيحة', 'error')
            return redirect(url_for('admin.products'))
        
        # التعامل مع رفع الصورة
        image_url = None
        image_file = request.files.get('product_image')
        if image_file and image_file.filename:
            # التحقق من نوع الملف
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            filename = secure_filename(image_file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_extension not in allowed_extensions:
                flash('نوع الملف غير مدعوم. يرجى استخدام PNG, JPG, JPEG, GIF, أو WEBP', 'error')
                return redirect(url_for('admin.products'))
            
            # التحقق من حجم الملف (5 ميجابايت كحد أقصى)
            image_file.seek(0, 2)
            file_size = image_file.tell()
            image_file.seek(0)
            
            if file_size > 5 * 1024 * 1024:  # 5 ميجابايت
                flash('حجم الصورة كبير جداً. الحد الأقصى 5 ميجابايت', 'error')
                return redirect(url_for('admin.products'))
            
            # إنشاء اسم ملف فريد
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            # التأكد من وجود مجلد الرفع
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'gift-cards')
            os.makedirs(upload_folder, exist_ok=True)
            
            # حفظ الصورة
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            image_url = filename
        
        # تحويل التاريخ إذا تم إدخاله
        expiry_date_obj = None
        if expiry_date:
            try:
                expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # إنشاء المنتج الجديد
        new_product = Product(
            name=name,
            description=description,
            category_id=int(category_id) if category_id else None,  # القسم الرئيسي الجديد
            subcategory_id=int(subcategory_id) if subcategory_id else None,  # القسم الفرعي الجديد
            category=category,  # الفئة القديمة للتوافق
            region=region,
            value=value,
            purchase_price=purchase_price_float,
            regular_price=regular_price_float,
            kyc_price=kyc_price_float,
            reseller_price=reseller_price_float,
            stock_quantity=stock_quantity_int,
            instructions=instructions,
            expiry_date=expiry_date_obj,
            image_url=image_url,
            is_active=is_active,
            user_type_visibility=user_type_visibility
        )
        
        # معالجة البيانات المتقدمة
        visibility = request.form.get('visibility', 'public')  # public, restricted
        restricted_emails_json = request.form.get('restricted_emails', '[]')
        custom_prices_json = request.form.get('custom_prices', '[]')
        
        new_product.visibility = visibility
        
        db.session.add(new_product)
        db.session.flush()  # للحصول على ID المنتج
        
        # معالجة قائمة البريد الإلكتروني المحدود
        if visibility == 'restricted':
            try:
                restricted_emails = json.loads(restricted_emails_json)
                for email in restricted_emails:
                    user = User.query.filter_by(email=email).first()
                    if user:
                        access = ProductUserAccess(
                            product_id=new_product.id,
                            user_id=user.id
                        )
                        db.session.add(access)
            except (json.JSONDecodeError, KeyError):
                pass
        
        # معالجة الأسعار المخصصة
        try:
            custom_prices = json.loads(custom_prices_json)
            for price_data in custom_prices:
                user = User.query.filter_by(email=price_data['email']).first()
                if user:
                    custom_price = ProductCustomPrice(
                        product_id=new_product.id,
                        user_id=user.id,
                        regular_price=float(price_data['regular_price']),
                        kyc_price=float(price_data['kyc_price']),
                        note=price_data.get('note', '')
                    )
                    db.session.add(custom_price)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        db.session.commit()
        
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('admin.products'))
        
    except Exception as e:
        db.session.rollback()
        # حذف الصورة إذا تم رفعها ولكن فشل في حفظ البيانات
        if 'filename' in locals() and 'image_path' in locals() and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.products'))

@admin.route('/products/<int:product_id>/edit', methods=['POST'])
@login_required
def update_product(product_id):
    """تحديث منتج موجود"""
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('main.index'))
    
    try:
        product = Product.query.get_or_404(product_id)
        
        # تحديث البيانات الأساسية
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        
        # تحديث الأقسام الجديدة
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id')
        if category_id:
            product.category_id = int(category_id)
        if subcategory_id:
            product.subcategory_id = int(subcategory_id)
        
        # الاحتفاظ بالفئة القديمة للتوافق
        if request.form.get('category'):
            product.category = request.form.get('category')
        
        product.region = request.form.get('region')
        product.value = request.form.get('value')
        product.purchase_price = float(request.form.get('purchase_price', 0))
        product.regular_price = float(request.form.get('regular_price', 0))
        product.kyc_price = float(request.form.get('kyc_price', 0))
        product.reseller_price = float(request.form.get('reseller_price', 0))
        product.stock_quantity = int(request.form.get('stock_quantity', 0))
        product.instructions = request.form.get('instructions')
        product.is_active = request.form.get('is_active') == 'on'
        
        # تحديث أنواع المستخدمين المسموح لهم
        user_type_visibility = request.form.get('user_type_visibility', 'regular,kyc,reseller')
        product.user_type_visibility = user_type_visibility
        
        # تحديث تاريخ الانتهاء
        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            try:
                product.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # معالجة البيانات المتقدمة
        visibility = request.form.get('visibility', 'public')
        restricted_emails_json = request.form.get('restricted_emails', '[]')
        custom_prices_json = request.form.get('custom_prices', '[]')
        
        product.visibility = visibility
        
        # حذف صلاحيات الوصول السابقة
        ProductUserAccess.query.filter_by(product_id=product_id).delete()
        
        # معالجة قائمة البريد الإلكتروني المحدود
        if visibility == 'restricted':
            try:
                restricted_emails = json.loads(restricted_emails_json)
                for email in restricted_emails:
                    user = User.query.filter_by(email=email).first()
                    if user:
                        access = ProductUserAccess(
                            product_id=product.id,
                            user_id=user.id
                        )
                        db.session.add(access)
            except (json.JSONDecodeError, KeyError):
                pass
        
        # حذف الأسعار المخصصة السابقة
        ProductCustomPrice.query.filter_by(product_id=product_id).delete()
        
        # معالجة الأسعار المخصصة
        try:
            custom_prices = json.loads(custom_prices_json)
            for price_data in custom_prices:
                user = User.query.filter_by(email=price_data['email']).first()
                if user:
                    custom_price = ProductCustomPrice(
                        product_id=product.id,
                        user_id=user.id,
                        regular_price=float(price_data['regular_price']),
                        kyc_price=float(price_data['kyc_price']),
                        note=price_data.get('note', '')
                    )
                    db.session.add(custom_price)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        # تحديث الصورة إذا تم رفع صورة جديدة
        image_file = request.files.get('product_image')
        if image_file and image_file.filename:
            # التحقق من نوع الملف
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            filename = secure_filename(image_file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_extension not in allowed_extensions:
                flash('نوع الملف غير مدعوم. يرجى استخدام PNG, JPG, JPEG, GIF, أو WEBP', 'error')
                return redirect(url_for('admin.products'))
            
            # التحقق من حجم الملف (5 ميجابايت كحد أقصى)
            image_file.seek(0, 2)
            file_size = image_file.tell()
            image_file.seek(0)
            
            if file_size > 5 * 1024 * 1024:  # 5 ميجابايت
                flash('حجم الصورة كبير جداً. الحد الأقصى 5 ميجابايت', 'error')
                return redirect(url_for('admin.products'))
            
            # حذف الصورة القديمة
            if product.image_url:
                old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'gift-cards', product.image_url)
                if os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                    except:
                        pass
            
            # رفع الصورة الجديدة
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'gift-cards')
            os.makedirs(upload_folder, exist_ok=True)
            
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            product.image_url = filename
        
        db.session.commit()
        
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('admin.products'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.products'))

@admin.route('/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """تعطيل منتج بدلاً من حذفه"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        product = Product.query.get_or_404(product_id)
        
        # تعطيل المنتج بدلاً من حذفه
        product.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم تعطيل المنتج بنجاح وإخفاؤه من الموقع'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/products/<int:product_id>/activate', methods=['POST'])
@login_required
def activate_product(product_id):
    """إعادة تفعيل منتج معطل"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        product = Product.query.get_or_404(product_id)
        
        # إعادة تفعيل المنتج
        product.is_active = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم إعادة تفعيل المنتج بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/products/<int:product_id>')
@login_required
def get_product(product_id):
    """جلب بيانات منتج للتعديل"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        product = Product.query.get_or_404(product_id)
        
        # جلب قائمة البريد الإلكتروني المحدود
        restricted_emails = []
        visibility = getattr(product, 'visibility', 'public')
        
        if visibility == 'restricted':
            access_list = ProductUserAccess.query.filter_by(product_id=product_id).all()
            restricted_emails = [access.user.email for access in access_list if access.user]
        
        # جلب الأسعار المخصصة
        custom_prices = []
        custom_prices_list = ProductCustomPrice.query.filter_by(product_id=product_id).all()
        for custom_price in custom_prices_list:
            if custom_price.user:
                custom_prices.append({
                    'email': custom_price.user.email,
                    'regular_price': custom_price.regular_price,
                    'kyc_price': custom_price.kyc_price,
                    'note': custom_price.note or ''
                })
        
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category,
            'category_id': product.category_id,
            'subcategory_id': product.subcategory_id,
            'region': product.region,
            'value': product.value,
            'purchase_price': product.purchase_price,
            'regular_price': product.regular_price,
            'kyc_price': product.kyc_price,
            'reseller_price': product.reseller_price,
            'stock_quantity': product.stock_quantity,
            'instructions': product.instructions,
            'expiry_date': product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else '',
            'image_url': product.image_url,
            'is_active': product.is_active,
            'visibility': visibility,
            'user_type_visibility': product.user_type_visibility,
            'restricted_emails': restricted_emails,
            'custom_prices': custom_prices
        }
        
        return jsonify({'success': True, 'product': product_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/products/<int:product_id>/codes')
@login_required
def get_product_codes(product_id):
    """جلب أكواد منتج"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        codes = ProductCode.query.filter_by(product_id=product_id).all()
        codes_data = []
        
        for code in codes:
            codes_data.append({
                'id': code.id,
                'code': code.code,
                'is_used': code.is_used,
                'used_by': code.used_by_user.email if code.used_by_user else None,
                'used_at': code.used_at.strftime('%Y-%m-%d %H:%M') if code.used_at else None
            })
        
        return jsonify({'success': True, 'codes': codes_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/products/<int:product_id>/codes', methods=['POST'])
@login_required
def add_product_codes(product_id):
    """إضافة أكواد لمنتج"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        codes_text = request.form.get('codes')
        if not codes_text:
            return jsonify({'success': False, 'message': 'يرجى إدخال الأكواد'})
        
        # تقسيم الأكواد وتنظيفها
        codes_list = [code.strip() for code in codes_text.split('\n') if code.strip()]
        
        if not codes_list:
            return jsonify({'success': False, 'message': 'لم يتم العثور على أكواد صحيحة'})
        
        added_count = 0
        existing_count = 0
        
        for code_text in codes_list:
            # التحقق من عدم وجود الكود مسبقاً
            existing_code = ProductCode.query.filter_by(code=code_text).first()
            if existing_code:
                existing_count += 1
                continue
            
            # إضافة الكود الجديد
            new_code = ProductCode(
                product_id=product_id,
                code=code_text,
                is_used=False
            )
            db.session.add(new_code)
            added_count += 1
        
        db.session.commit()
        
        message = f'تم إضافة {added_count} كود بنجاح'
        if existing_count > 0:
            message += f' (تم تجاهل {existing_count} كود موجود مسبقاً)'
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/products/<int:product_id>/codes/<int:code_id>', methods=['DELETE'])
@login_required
def delete_product_code(product_id, code_id):
    """حذف كود منتج"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        code = ProductCode.query.filter_by(id=code_id, product_id=product_id).first_or_404()
        
        if code.is_used:
            return jsonify({'success': False, 'message': 'لا يمكن حذف كود مستخدم'})
        
        db.session.delete(code)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف الكود بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

# ===== إدارة الأدوار والصلاحيات =====

@admin_bp.route('/roles')
@login_required
@requires_page_access('admin.roles')
@requires_permission('roles.read')
def roles_management():
    """صفحة إدارة الأدوار"""
    try:
        roles = Role.query.all()
        permissions = Permission.query.all()
        employees_count = Employee.query.filter_by(status='active').count()
        
        # تمرير قائمة الصفحات للقالب
        admin_pages = get_pages_for_js()
        
        return render_template('admin/roles.html',
                             roles=roles,
                             permissions=permissions,
                             employees_count=employees_count,
                             admin_pages=admin_pages)
    except Exception as e:
        flash(f'خطأ في تحميل الأدوار: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/roles/add', methods=['POST'])
@login_required
@requires_permission('roles.create')
def add_role():
    """إضافة دور جديد"""
    try:
        data = request.get_json()
        
        # التحقق من عدم وجود دور بنفس الاسم
        existing_role = Role.query.filter_by(name=data['name']).first()
        if existing_role:
            return jsonify({
                'success': False,
                'message': 'يوجد دور بهذا الاسم مسبقاً'
            }), 400
        
        # إنشاء الدور الجديد
        role = Role(
            name=data['name'],
            display_name=data['display_name'],
            description=data.get('description'),
            is_admin=data.get('is_admin', False),
            is_active=True,
            allowed_pages=json.dumps(data.get('allowed_pages', [])) if data.get('allowed_pages') else None
        )
        
        db.session.add(role)
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(
            current_user.id,
            'create_role',
            f'إضافة دور جديد: {role.display_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء الدور بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء الدور: {str(e)}'
        }), 500

@admin_bp.route('/roles/<int:role_id>')
@login_required
@requires_permission('roles.read')
def get_role(role_id):
    """الحصول على بيانات دور"""
    try:
        role = Role.query.get_or_404(role_id)
        
        return jsonify({
            'success': True,
            'role': {
                'id': role.id,
                'name': role.name,
                'display_name': role.display_name,
                'description': role.description,
                'is_admin': role.is_admin,
                'is_active': role.is_active,
                'allowed_pages': json.loads(role.allowed_pages) if role.allowed_pages else []
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تحميل الدور: {str(e)}'
        }), 500

@admin_bp.route('/roles/<int:role_id>/edit', methods=['POST'])
@login_required
@requires_permission('roles.update')
def edit_role(role_id):
    """تعديل دور"""
    try:
        role = Role.query.get_or_404(role_id)
        data = request.get_json()
        
        # التحقق من عدم تعديل الأدوار الأساسية
        if role.name in ['super_admin', 'admin']:
            return jsonify({
                'success': False,
                'message': 'لا يمكن تعديل الأدوار الأساسية للنظام'
            }), 400
        
        # التحقق من عدم وجود دور آخر بنفس الاسم
        existing_role = Role.query.filter(
            Role.name == data['name'],
            Role.id != role_id
        ).first()
        if existing_role:
            return jsonify({
                'success': False,
                'message': 'يوجد دور آخر بهذا الاسم'
            }), 400
        
        # تحديث بيانات الدور
        role.name = data['name']
        role.display_name = data['display_name']
        role.description = data.get('description')
        role.is_admin = data.get('is_admin', False)
        role.allowed_pages = json.dumps(data.get('allowed_pages', [])) if data.get('allowed_pages') else None
        
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(
            current_user.id,
            'update_role',
            f'تعديل الدور: {role.display_name}'
        )
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث الدور بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث الدور: {str(e)}'
        }), 500

@admin_bp.route('/roles/<int:role_id>/status', methods=['POST'])
@login_required
@requires_permission('roles.update')
def toggle_role_status(role_id):
    """تفعيل/إلغاء تفعيل دور"""
    try:
        role = Role.query.get_or_404(role_id)
        data = request.get_json()
        
        # التحقق من عدم تعديل الأدوار الأساسية
        if role.name in ['super_admin', 'admin']:
            return jsonify({
                'success': False,
                'message': 'لا يمكن تعديل حالة الأدوار الأساسية'
            }), 400
        
        role.is_active = data['is_active']
        db.session.commit()
        
        # تسجيل النشاط
        action_text = 'تفعيل' if role.is_active else 'إلغاء تفعيل'
        log_activity(
            current_user.id,
            'toggle_role_status',
            f'{action_text} الدور: {role.display_name}'
        )
        
        return jsonify({
            'success': True,
            'message': f'تم {action_text} الدور بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث حالة الدور: {str(e)}'
        }), 500

@admin_bp.route('/roles/<int:role_id>/delete', methods=['DELETE'])
@login_required
@requires_permission('roles.delete')
def delete_role(role_id):
    """حذف دور"""
    try:
        role = Role.query.get_or_404(role_id)
        
        # التحقق من عدم حذف الأدوار الأساسية
        if role.name in ['super_admin', 'admin']:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الأدوار الأساسية للنظام'
            }), 400
        
        # التحقق من عدم وجود موظفين مرتبطين بهذا الدور
        if role.employees:
            return jsonify({
                'success': False,
                'message': f'لا يمكن حذف الدور لوجود {len(role.employees)} موظف مرتبط به'
            }), 400
        
        # تسجيل النشاط قبل الحذف
        log_activity(
            current_user.id,
            'delete_role',
            f'حذف الدور: {role.display_name}'
        )
        
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف الدور بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف الدور: {str(e)}'
        }), 500

@admin_bp.route('/roles/<int:role_id>/permissions')
@login_required
@requires_permission('roles.update')
def manage_role_permissions(role_id):
    """إدارة صلاحيات الدور"""
    try:
        role = Role.query.get_or_404(role_id)
        all_permissions = Permission.query.order_by(Permission.category, Permission.name).all()
        role_permission_ids = [rp.permission_id for rp in role.role_permissions]
        
        # تجميع الصلاحيات حسب الفئة
        permissions_by_category = {}
        for permission in all_permissions:
            if permission.category not in permissions_by_category:
                permissions_by_category[permission.category] = []
            permissions_by_category[permission.category].append(permission)
        
        html = render_template_string('''
        <div style="text-align: center; margin-bottom: 20px;">
            <h4 style="color: #fff;">إدارة صلاحيات الدور: {{ role.display_name }}</h4>
            <p style="color: #ccc;">اختر الصلاحيات التي تريد منحها لهذا الدور</p>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
            {% for category, permissions in permissions_by_category.items() %}
            <div class="permission-category" style="background: #333; border-radius: 8px; padding: 15px; border: 1px solid #555;">
                <h5 style="color: #ff0033; margin-bottom: 15px; border-bottom: 1px solid #555; padding-bottom: 8px;">
                    <i class="fas fa-{{ category_icons.get(category, 'cog') }}"></i>
                    {{ category_names.get(category, category) }}
                </h5>
                
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    {% for permission in permissions %}
                    <label style="display: flex; align-items: center; gap: 10px; color: #ccc; cursor: pointer; padding: 5px; border-radius: 5px; transition: background 0.3s;" 
                           onmouseover="this.style.background='#444'" 
                           onmouseout="this.style.background='transparent'">
                        <input type="checkbox" 
                               data-permission-id="{{ permission.id }}"
                               {{ 'checked' if permission.id in role_permission_ids else '' }}
                               style="accent-color: #ff0033;">
                        <span>{{ permission.display_name }}</span>
                        {% if permission.description %}
                        <small style="color: #999; font-size: 0.8em;">({{ permission.description }})</small>
                        {% endif %}
                    </label>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        ''', 
        role=role, 
        permissions_by_category=permissions_by_category,
        role_permission_ids=role_permission_ids,
        category_names={
            'users': 'إدارة المستخدمين',
            'products': 'إدارة المنتجات',
            'orders': 'إدارة الطلبات',
            'categories': 'إدارة التصنيفات',
            'currencies': 'إدارة العملات',
            'reports': 'التقارير',
            'employees': 'إدارة الموظفين',
            'roles': 'إدارة الأدوار',
            'system': 'إعدادات النظام',
            'content': 'إدارة المحتوى'
        },
        category_icons={
            'users': 'users',
            'products': 'box',
            'orders': 'shopping-cart',
            'categories': 'tags',
            'currencies': 'dollar-sign',
            'reports': 'chart-bar',
            'employees': 'user-tie',
            'roles': 'user-shield',
            'system': 'cogs',
            'content': 'edit'
        })
        
        return jsonify({
            'success': True,
            'html': html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تحميل الصلاحيات: {str(e)}'
        }), 500

@admin_bp.route('/roles/<int:role_id>/permissions', methods=['POST'])
@login_required
@requires_permission('roles.update')
def save_role_permissions(role_id):
    """حفظ صلاحيات الدور"""
    try:
        role = Role.query.get_or_404(role_id)
        data = request.get_json()
        permission_ids = data.get('permissions', [])
        
        # حذف الصلاحيات الحالية
        RolePermission.query.filter_by(role_id=role_id).delete()
        
        # إضافة الصلاحيات الجديدة
        for permission_id in permission_ids:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id
            )
            db.session.add(role_permission)
        
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(
            current_user.id,
            'update_role_permissions',
            f'تحديث صلاحيات الدور: {role.display_name} ({len(permission_ids)} صلاحية)'
        )
        
        return jsonify({
            'success': True,
            'message': f'تم حفظ صلاحيات الدور بنجاح ({len(permission_ids)} صلاحية)'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حفظ الصلاحيات: {str(e)}'
        }), 500

@admin_bp.route('/roles/<int:role_id>/permissions/view')
@login_required
@requires_permission('roles.read')
def view_role_permissions(role_id):
    """عرض صلاحيات الدور"""
    try:
        role = Role.query.get_or_404(role_id)
        role_permissions = db.session.query(Permission).join(RolePermission).filter(
            RolePermission.role_id == role_id
        ).order_by(Permission.category, Permission.name).all()
        
        # تجميع الصلاحيات حسب الفئة
        permissions_by_category = {}
        for permission in role_permissions:
            if permission.category not in permissions_by_category:
                permissions_by_category[permission.category] = []
            permissions_by_category[permission.category].append(permission)
        
        html = render_template_string('''
        <div style="text-align: center; margin-bottom: 20px;">
            <h4 style="color: #fff;">صلاحيات الدور: {{ role.display_name }}</h4>
            <p style="color: #ccc;">عدد الصلاحيات: {{ role_permissions|length }}</p>
        </div>
        
        {% if permissions_by_category %}
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
            {% for category, permissions in permissions_by_category.items() %}
            <div class="permission-category" style="background: #333; border-radius: 8px; padding: 15px; border: 1px solid #555;">
                <h5 style="color: #ff0033; margin-bottom: 15px; border-bottom: 1px solid #555; padding-bottom: 8px;">
                    <i class="fas fa-{{ category_icons.get(category, 'cog') }}"></i>
                    {{ category_names.get(category, category) }}
                    <span style="color: #ccc; font-size: 0.8em;">({{ permissions|length }})</span>
                </h5>
                
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    {% for permission in permissions %}
                    <div style="display: flex; align-items: center; gap: 10px; color: #ccc; padding: 5px; background: #444; border-radius: 5px;">
                        <i class="fas fa-check" style="color: #28a745;"></i>
                        <span>{{ permission.display_name }}</span>
                        {% if permission.description %}
                        <small style="color: #999; font-size: 0.8em;">({{ permission.description }})</small>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div style="text-align: center; color: #ccc; padding: 40px;">
            <i class="fas fa-info-circle" style="font-size: 3em; margin-bottom: 15px;"></i>
            <p>لا توجد صلاحيات مرتبطة بهذا الدور</p>
        </div>
        {% endif %}
        ''', 
        role=role, 
        role_permissions=role_permissions,
        permissions_by_category=permissions_by_category,
        category_names={
            'users': 'إدارة المستخدمين',
            'products': 'إدارة المنتجات',
            'orders': 'إدارة الطلبات',
            'categories': 'إدارة التصنيفات',
            'currencies': 'إدارة العملات',
            'reports': 'التقارير',
            'employees': 'إدارة الموظفين',
            'roles': 'إدارة الأدوار',
            'system': 'إعدادات النظام',
            'content': 'إدارة المحتوى'
        },
        category_icons={
            'users': 'users',
            'products': 'box',
            'orders': 'shopping-cart',
            'categories': 'tags',
            'currencies': 'dollar-sign',
            'reports': 'chart-bar',
            'employees': 'user-tie',
            'roles': 'user-shield',
            'system': 'cogs',
            'content': 'edit'
        })
        
        return jsonify({
            'success': True,
            'html': html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تحميل الصلاحيات: {str(e)}'
        }), 500
