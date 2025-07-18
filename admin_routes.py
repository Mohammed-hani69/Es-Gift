from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import extract, func
import os
import json
import requests
from werkzeug.security import generate_password_hash
import matplotlib
matplotlib.use('Agg')  # استخدام backend غير تفاعلي
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from urllib.parse import quote

from models import *
from utils import send_email

# إنشاء Blueprint للمسارات الإدارية
admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/')
@login_required
def dashboard():
    if not current_user.is_admin:
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
def products():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@admin.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

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
        
        if request.method == 'POST':
            return jsonify({'success': True, 'message': 'تم الموافقة على طلب التحقق'})
        
        flash('تم الموافقة على طلب التحقق', 'success')
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
    
    user.customer_type = customer_type
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم تحديث نوع العميل بنجاح'})

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
def orders():
    if not current_user.is_admin:
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
    quick_categories = QuickCategory.query.filter_by(is_active=True).order_by(QuickCategory.display_order).all()
    gift_card_sections = GiftCardSection.query.filter_by(is_active=True).order_by(GiftCardSection.display_order).all()
    other_brands = OtherBrand.query.filter_by(is_active=True).order_by(OtherBrand.display_order).all()
    
    return render_template('admin/homepage_management.html',
                         main_offers=main_offers,
                         quick_categories=quick_categories,
                         gift_card_sections=gift_card_sections,
                         other_brands=other_brands)

@admin.route('/homepage/main-offers/add', methods=['POST'])
@login_required
def add_main_offer():
    """إضافة عرض رئيسي جديد"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        title = request.form.get('title')
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
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads' , 'main-offers')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # حفظ الصورة
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            
            # إنشاء العرض الجديد
            new_offer = MainOffer(
                title=title,
                image_url=filename,
                link_url=link_url,
                display_order=int(display_order),
                is_active=True
            )
            
            db.session.add(new_offer)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'تم إضافة العرض بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'يرجى اختيار صورة'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage/main-offers/delete/<int:offer_id>', methods=['DELETE'])
@login_required
def delete_main_offer(offer_id):
    """حذف عرض رئيسي"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        offer = MainOffer.query.get_or_404(offer_id)
        
        # حذف ملف الصورة
        if offer.image_url:
            image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'main-offers',offer.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(offer)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف العرض بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage/main-offers/edit/<int:offer_id>', methods=['POST'])
@login_required
def edit_main_offer(offer_id):
    """تعديل عرض رئيسي"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        offer = MainOffer.query.get_or_404(offer_id)
        
        # تحديث البيانات النصية
        offer.title = request.form.get('title')
        offer.link_url = request.form.get('link_url')
        offer.display_order = request.form.get('display_order', 0)
        
        # تحديث الصورة إذا تم رفع صورة جديدة
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            if file and file.filename != '':
                # حذف الصورة القديمة
                if offer.image_url:
                    old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'main-offers', offer.image_url)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # حفظ الصورة الجديدة
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                # إنشاء مجلد uploads إذا لم يكن موجوداً
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads' ,'main-offers')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                offer.image_url = filename
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم تحديث العرض بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage/quick-categories/add', methods=['POST'])
@login_required
def add_quick_category():
    """إضافة فئة مختصرة جديدة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        name = request.form.get('name')
        icon_class = request.form.get('icon_class')
        link_url = request.form.get('link_url')
        display_order = request.form.get('display_order', 0)
        
        if not name or not icon_class or not link_url:
            return jsonify({'success': False, 'message': 'جميع الحقول مطلوبة'})
        
        # إنشاء الفئة الجديدة
        new_category = QuickCategory(
            name=name,
            icon_class=icon_class,
            link_url=link_url,
            display_order=int(display_order),
            is_active=True
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم إضافة الفئة بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage/quick-categories/delete/<int:category_id>', methods=['DELETE'])
@login_required
def delete_quick_category(category_id):
    """حذف فئة مختصرة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        category = QuickCategory.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حذف الفئة بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@admin.route('/homepage/gift-cards/add', methods=['POST'])
@login_required
def add_gift_card():
    """إضافة بطاقة هدايا جديدة"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    try:
        title = request.form.get('title')
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
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads' , 'gift-cards')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # حفظ الصورة
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            
            # إنشاء بطاقة الهدايا الجديدة
            new_card = GiftCardSection(
                title=title,
                image_url=filename,
                link_url=link_url,
                display_order=int(display_order),
                is_active=True
            )
            
            db.session.add(new_card)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'تم إضافة بطاقة الهدايا بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'يرجى اختيار صورة'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

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

@admin.route('/currencies')
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
    """إعدادات API"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
    return render_template('admin/api_settings.html')

# ...existing code...

@admin.route('/reports')
@login_required
def reports():
    """التقارير والإحصائيات المتقدمة"""
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    
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
