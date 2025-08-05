from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, extract, desc
from models import db, User, Order, OrderItem, Product, ProductCode, Invoice, Currency, PaymentGateway, Article, Category, Subcategory
from employee_utils import requires_page_access
import calendar

class ReportsService:
    """خدمة التقارير والإحصائيات"""
    
    @staticmethod
    def get_date_range(period, start_date=None, end_date=None):
        """حساب نطاق التاريخ حسب الفترة المحددة"""
        end = datetime.now()
        
        if period == 'today':
            start = end.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start = end - timedelta(days=7)
        elif period == 'month':
            start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'year':
            start = end.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'custom' and start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            # آخر 30 يوم كافتراضي
            start = end - timedelta(days=30)
        
        return start, end
    
    @staticmethod
    def get_reseller_stats(period='month', start_date=None, end_date=None):
        """احصائيات الموزعين"""
        start, end = ReportsService.get_date_range(period, start_date, end_date)
        
        # عدد الموزعين
        total_resellers = User.query.filter_by(customer_type='reseller').count()
        active_resellers = db.session.query(User).filter(
            User.customer_type == 'reseller'
        ).join(Order).filter(
            Order.created_at >= start,
            Order.created_at <= end
        ).distinct().count()
        
        # إحصائيات الطلبات
        reseller_orders = Order.query.join(User).filter(
            User.customer_type == 'reseller',
            Order.created_at >= start,
            Order.created_at <= end
        )
        
        total_orders = reseller_orders.count()
        completed_orders = reseller_orders.filter(Order.order_status == 'completed').count()
        pending_orders = reseller_orders.filter(Order.order_status == 'pending').count()
        
        # الإيرادات
        revenue_data = reseller_orders.filter(Order.payment_status == 'paid').with_entities(
            func.sum(Order.total_amount).label('total_revenue'),
            func.avg(Order.total_amount).label('avg_order_value'),
            func.count(Order.id).label('paid_orders')
        ).first()
        
        total_revenue = float(revenue_data.total_revenue or 0)
        avg_order_value = float(revenue_data.avg_order_value or 0)
        paid_orders = revenue_data.paid_orders or 0
        
        # حساب الأرباح (الفرق بين سعر الموزع وسعر الشراء)
        profit_data = db.session.query(
            func.sum((OrderItem.price - Product.purchase_price) * OrderItem.quantity).label('total_profit')
        ).join(Order).join(User).join(Product).filter(
            User.customer_type == 'reseller',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).first()
        
        total_profit = float(profit_data.total_profit or 0)
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # المنتجات الأكثر مبيعاً
        top_products = db.session.query(
            Product.name,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
        ).join(OrderItem).join(Order).join(User).filter(
            User.customer_type == 'reseller',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).group_by(Product.id, Product.name).order_by(desc('total_sold')).limit(10).all()
        
        # الموزعين الأكثر نشاطاً
        top_resellers = db.session.query(
            User.full_name,
            User.email,
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_spent')
        ).join(Order).filter(
            User.customer_type == 'reseller',
            Order.created_at >= start,
            Order.created_at <= end
        ).group_by(User.id, User.full_name, User.email).order_by(desc('total_spent')).limit(10).all()
        
        # بيانات الرسوم البيانية - المبيعات الشهرية
        monthly_sales = db.session.query(
            extract('month', Order.created_at).label('month'),
            extract('year', Order.created_at).label('year'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('orders')
        ).join(User).filter(
            User.customer_type == 'reseller',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).group_by(
            extract('month', Order.created_at),
            extract('year', Order.created_at)
        ).order_by('year', 'month').all()
        
        return {
            'period': period,
            'date_range': {'start': start, 'end': end},
            'total_resellers': total_resellers,
            'active_resellers': active_resellers,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'profit_margin': profit_margin,
            'avg_order_value': avg_order_value,
            'paid_orders': paid_orders,
            'top_products': top_products,
            'top_resellers': top_resellers,
            'monthly_sales': monthly_sales
        }
    
    @staticmethod
    def get_regular_kyc_stats(period='month', start_date=None, end_date=None):
        """احصائيات المستخدمين العاديين والموثقين"""
        start, end = ReportsService.get_date_range(period, start_date, end_date)
        
        # عدد المستخدمين
        total_regular = User.query.filter_by(customer_type='regular').count()
        total_kyc = User.query.filter_by(customer_type='kyc').count()
        
        active_regular = db.session.query(User).filter(
            User.customer_type == 'regular'
        ).join(Order).filter(
            Order.created_at >= start,
            Order.created_at <= end
        ).distinct().count()
        
        active_kyc = db.session.query(User).filter(
            User.customer_type == 'kyc'
        ).join(Order).filter(
            Order.created_at >= start,
            Order.created_at <= end
        ).distinct().count()
        
        # إحصائيات الطلبات للعاديين
        regular_orders = Order.query.join(User).filter(
            User.customer_type == 'regular',
            Order.created_at >= start,
            Order.created_at <= end
        )
        
        # إحصائيات الطلبات للموثقين
        kyc_orders = Order.query.join(User).filter(
            User.customer_type == 'kyc',
            Order.created_at >= start,
            Order.created_at <= end
        )
        
        # الإيرادات للعاديين
        regular_revenue = regular_orders.filter(Order.payment_status == 'paid').with_entities(
            func.sum(Order.total_amount).label('total_revenue'),
            func.avg(Order.total_amount).label('avg_order_value'),
            func.count(Order.id).label('total_orders')
        ).first()
        
        # الإيرادات للموثقين
        kyc_revenue = kyc_orders.filter(Order.payment_status == 'paid').with_entities(
            func.sum(Order.total_amount).label('total_revenue'),
            func.avg(Order.total_amount).label('avg_order_value'),
            func.count(Order.id).label('total_orders')
        ).first()
        
        # أرباح العاديين
        regular_profit = db.session.query(
            func.sum((OrderItem.price - Product.purchase_price) * OrderItem.quantity).label('total_profit')
        ).join(Order).join(User).join(Product).filter(
            User.customer_type == 'regular',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).first()
        
        # أرباح الموثقين
        kyc_profit = db.session.query(
            func.sum((OrderItem.price - Product.purchase_price) * OrderItem.quantity).label('total_profit')
        ).join(Order).join(User).join(Product).filter(
            User.customer_type == 'kyc',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).first()
        
        # المنتجات الأكثر مبيعاً للعاديين
        top_products_regular = db.session.query(
            Product.name,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
        ).join(OrderItem).join(Order).join(User).filter(
            User.customer_type == 'regular',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).group_by(Product.id, Product.name).order_by(desc('total_sold')).limit(10).all()
        
        # المنتجات الأكثر مبيعاً للموثقين
        top_products_kyc = db.session.query(
            Product.name,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
        ).join(OrderItem).join(Order).join(User).filter(
            User.customer_type == 'kyc',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).group_by(Product.id, Product.name).order_by(desc('total_sold')).limit(10).all()
        
        # المبيعات الشهرية للعاديين
        monthly_sales_regular = db.session.query(
            extract('month', Order.created_at).label('month'),
            extract('year', Order.created_at).label('year'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('orders')
        ).join(User).filter(
            User.customer_type == 'regular',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).group_by(
            extract('month', Order.created_at),
            extract('year', Order.created_at)
        ).order_by('year', 'month').all()
        
        # المبيعات الشهرية للموثقين
        monthly_sales_kyc = db.session.query(
            extract('month', Order.created_at).label('month'),
            extract('year', Order.created_at).label('year'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('orders')
        ).join(User).filter(
            User.customer_type == 'kyc',
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).group_by(
            extract('month', Order.created_at),
            extract('year', Order.created_at)
        ).order_by('year', 'month').all()
        
        return {
            'period': period,
            'date_range': {'start': start, 'end': end},
            'regular': {
                'total_users': total_regular,
                'active_users': active_regular,
                'total_orders': regular_orders.count(),
                'completed_orders': regular_orders.filter(Order.order_status == 'completed').count(),
                'total_revenue': float(regular_revenue.total_revenue or 0),
                'total_profit': float(regular_profit.total_profit or 0),
                'avg_order_value': float(regular_revenue.avg_order_value or 0),
                'paid_orders': regular_revenue.total_orders or 0,
                'top_products': top_products_regular,
                'monthly_sales': monthly_sales_regular
            },
            'kyc': {
                'total_users': total_kyc,
                'active_users': active_kyc,
                'total_orders': kyc_orders.count(),
                'completed_orders': kyc_orders.filter(Order.order_status == 'completed').count(),
                'total_revenue': float(kyc_revenue.total_revenue or 0),
                'total_profit': float(kyc_profit.total_profit or 0),
                'avg_order_value': float(kyc_revenue.avg_order_value or 0),
                'paid_orders': kyc_revenue.total_orders or 0,
                'top_products': top_products_kyc,
                'monthly_sales': monthly_sales_kyc
            }
        }
    
    @staticmethod
    def get_comparison_stats(period='month', start_date=None, end_date=None):
        """مقارنة بين جميع أنواع المستخدمين"""
        start, end = ReportsService.get_date_range(period, start_date, end_date)
        
        comparison_data = []
        user_types = ['regular', 'kyc', 'reseller']
        
        for user_type in user_types:
            orders = Order.query.join(User).filter(
                User.customer_type == user_type,
                Order.created_at >= start,
                Order.created_at <= end,
                Order.payment_status == 'paid'
            )
            
            revenue_data = orders.with_entities(
                func.sum(Order.total_amount).label('total_revenue'),
                func.count(Order.id).label('total_orders'),
                func.avg(Order.total_amount).label('avg_order_value')
            ).first()
            
            comparison_data.append({
                'user_type': user_type,
                'user_type_name': {
                    'regular': 'العادي',
                    'kyc': 'الموثق', 
                    'reseller': 'الموزع'
                }[user_type],
                'total_revenue': float(revenue_data.total_revenue or 0),
                'total_orders': revenue_data.total_orders or 0,
                'avg_order_value': float(revenue_data.avg_order_value or 0)
            })
        
        return comparison_data

    @staticmethod
    def get_basic_stats():
        """إحصائيات أساسية للتقارير الرئيسية"""
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
        
        # إحصائيات المستخدمين
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
            
            monthly_data.append({
                'month': month_date.strftime('%Y-%m'),
                'month_name': month_date.strftime('%B %Y'),
                'revenue': float(month_revenue),
                'orders': month_orders
            })
        
        # أفضل المنتجات مبيعاً
        top_products = db.session.query(
            Product.name,
            Product.regular_price.label('price'),
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
        
        # إحصائيات يومية للأسبوع الماضي
        daily_data = []
        for i in range(6, -1, -1):
            day_date = datetime.now().date() - timedelta(days=i)
            
            day_orders = db.session.query(func.count(Order.id)).filter(
                Order.order_status == 'completed',
                func.date(Order.created_at) == day_date
            ).scalar() or 0
            
            daily_data.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'day_name': day_date.strftime('%A'),
                'orders': day_orders
            })
        
        # إعداد بيانات الرسوم البيانية
        chart_data = {
            # البيانات الشهرية
            'monthly_labels': [item['month_name'] for item in monthly_data],
            'monthly_revenue': [item['revenue'] for item in monthly_data],
            'monthly_orders': [item['orders'] for item in monthly_data],
            
            # البيانات اليومية
            'daily_labels': [item['day_name'] for item in daily_data],
            'daily_orders': [item['orders'] for item in daily_data],
            
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
            
            # إحصائيات المنتجات
            'products_status_labels': ['نشطة', 'غير نشطة'],
            'products_status_data': [active_products, inactive_products],
            
            # إحصائيات الأكواد
            'codes_labels': ['متاحة', 'مستخدمة'],
            'codes_data': [available_codes, used_codes],
            
            # فئات وهمية للتوافق
            'categories_labels': ['فئة 1', 'فئة 2', 'فئة 3'],
            'categories_revenue': [10000, 15000, 8000],
            'gateways_labels': ['Visa', 'MasterCard', 'PayPal'],
            'gateways_revenue': [25000, 20000, 15000],
            'kyc_labels': ['معلق', 'مقبول', 'مرفوض'],
            'kyc_data': [10, 50, 5]
        }
        
        return {
            # الإحصائيات الأساسية
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'cancelled_orders': cancelled_orders,
            'avg_order_value': float(total_revenue / max(completed_orders, 1)),
            
            # إحصائيات المستخدمين
            'total_users': total_users,
            'regular_users': regular_users,
            'kyc_users': kyc_users,
            'reseller_users': reseller_users,
            
            # إحصائيات المنتجات
            'active_products': active_products,
            'inactive_products': inactive_products,
            'available_codes': available_codes,
            'used_codes': used_codes,
            
            # البيانات التفصيلية
            'monthly_data': monthly_data,
            'daily_data': daily_data,
            'top_products': top_products,
            'customer_performance': customer_performance,
            
            # بيانات الرسوم البيانية
            'chart_data': chart_data,
            'now': datetime.now()
        }
