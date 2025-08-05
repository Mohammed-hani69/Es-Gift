from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, extract, desc
from models import db, User, Order, OrderItem, Product, ProductCode, Invoice
from employee_utils import requires_page_access

class ReportsService:
    """خدمة التقارير والإحصائيات"""
    
    @staticmethod
    def get_date_range(period, start_date=None, end_date=None):
        """حساب نطاق التاريخ حسب الفترة المحددة"""
        end = datetime.now()
        
        if period == 'today':
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start = end - timedelta(days=7)
        elif period == 'month':
            start = end - timedelta(days=30)
        elif period == 'year':
            start = end - timedelta(days=365)
        elif period == 'custom' and start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            start = end - timedelta(days=30)  # افتراضي: شهر واحد
        
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
            Order.payment_status == 'paid',
            Product.purchase_price.isnot(None)
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
        monthly_sales = []
        for i in range(6):  # آخر 6 شهور
            month_start = (datetime.now() - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            month_revenue = db.session.query(func.sum(Order.total_amount)).join(User).filter(
                User.customer_type == 'reseller',
                Order.created_at >= month_start,
                Order.created_at <= month_end,
                Order.payment_status == 'paid'
            ).scalar() or 0
            
            monthly_sales.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%B %Y'),
                'revenue': float(month_revenue)
            })
        
        monthly_sales.reverse()  # ترتيب تصاعدي
        
        return {
            'total_resellers': total_resellers,
            'active_resellers': active_resellers,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'avg_order_value': avg_order_value,
            'paid_orders': paid_orders,
            'total_profit': total_profit,
            'profit_margin': profit_margin,
            'top_products': top_products,
            'top_resellers': top_resellers,
            'monthly_sales': monthly_sales,
            'period': period,
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d')
        }
    
    @staticmethod
    def get_regular_kyc_stats(period='month', start_date=None, end_date=None):
        """احصائيات العملاء العاديين والموثقين"""
        start, end = ReportsService.get_date_range(period, start_date, end_date)
        
        # إحصائيات العملاء العاديين
        regular_stats = ReportsService._get_customer_type_stats('regular', start, end)
        
        # إحصائيات العملاء الموثقين
        kyc_stats = ReportsService._get_customer_type_stats('kyc', start, end)
        
        # مقارنة الأداء
        comparison = {
            'revenue_growth': ReportsService._calculate_growth(regular_stats['total_revenue'], kyc_stats['total_revenue']),
            'order_growth': ReportsService._calculate_growth(regular_stats['total_orders'], kyc_stats['total_orders']),
            'avg_order_growth': ReportsService._calculate_growth(regular_stats['avg_order_value'], kyc_stats['avg_order_value'])
        }
        
        return {
            'regular': regular_stats,
            'kyc': kyc_stats,
            'comparison': comparison,
            'period': period,
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d')
        }
    
    @staticmethod
    def _get_customer_type_stats(customer_type, start, end):
        """الحصول على إحصائيات نوع محدد من العملاء"""
        # عدد العملاء
        total_customers = User.query.filter_by(customer_type=customer_type).count()
        active_customers = db.session.query(User).filter(
            User.customer_type == customer_type
        ).join(Order).filter(
            Order.created_at >= start,
            Order.created_at <= end
        ).distinct().count()
        
        # إحصائيات الطلبات
        customer_orders = Order.query.join(User).filter(
            User.customer_type == customer_type,
            Order.created_at >= start,
            Order.created_at <= end
        )
        
        total_orders = customer_orders.count()
        completed_orders = customer_orders.filter(Order.order_status == 'completed').count()
        
        # الإيرادات
        revenue_data = customer_orders.filter(Order.payment_status == 'paid').with_entities(
            func.sum(Order.total_amount).label('total_revenue'),
            func.avg(Order.total_amount).label('avg_order_value')
        ).first()
        
        total_revenue = float(revenue_data.total_revenue or 0)
        avg_order_value = float(revenue_data.avg_order_value or 0)
        
        # المنتجات الأكثر شراءً
        top_products = db.session.query(
            Product.name,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
        ).join(OrderItem).join(Order).join(User).filter(
            User.customer_type == customer_type,
            Order.created_at >= start,
            Order.created_at <= end,
            Order.payment_status == 'paid'
        ).group_by(Product.id, Product.name).order_by(desc('total_sold')).limit(5).all()
        
        # بيانات شهرية
        monthly_data = []
        for i in range(6):
            month_start = (datetime.now() - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            month_revenue = db.session.query(func.sum(Order.total_amount)).join(User).filter(
                User.customer_type == customer_type,
                Order.created_at >= month_start,
                Order.created_at <= month_end,
                Order.payment_status == 'paid'
            ).scalar() or 0
            
            month_orders = db.session.query(func.count(Order.id)).join(User).filter(
                User.customer_type == customer_type,
                Order.created_at >= month_start,
                Order.created_at <= month_end
            ).scalar() or 0
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%B %Y'),
                'revenue': float(month_revenue),
                'orders': month_orders
            })
        
        monthly_data.reverse()
        
        return {
            'total_customers': total_customers,
            'active_customers': active_customers,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
            'avg_order_value': avg_order_value,
            'top_products': top_products,
            'monthly_data': monthly_data
        }
    
    @staticmethod
    def _calculate_growth(value1, value2):
        """حساب نسبة النمو بين قيمتين"""
        if value1 == 0:
            return 100 if value2 > 0 else 0
        return ((value2 - value1) / value1) * 100
    
    @staticmethod
    def get_comparison_stats(period='month', start_date=None, end_date=None):
        """مقارنة شاملة بين جميع أنواع المستخدمين"""
        start, end = ReportsService.get_date_range(period, start_date, end_date)
        
        # جلب الإحصائيات لكل نوع
        regular_stats = ReportsService._get_customer_type_stats('regular', start, end)
        kyc_stats = ReportsService._get_customer_type_stats('kyc', start, end)
        reseller_stats = ReportsService._get_customer_type_stats('reseller', start, end)
        
        # إجمالي الإحصائيات
        total_stats = {
            'total_customers': regular_stats['total_customers'] + kyc_stats['total_customers'] + reseller_stats['total_customers'],
            'total_orders': regular_stats['total_orders'] + kyc_stats['total_orders'] + reseller_stats['total_orders'],
            'total_revenue': regular_stats['total_revenue'] + kyc_stats['total_revenue'] + reseller_stats['total_revenue']
        }
        
        # النسب المئوية
        def safe_percentage(part, total):
            return (part / total * 100) if total > 0 else 0
        
        percentages = {
            'regular': {
                'customers': safe_percentage(regular_stats['total_customers'], total_stats['total_customers']),
                'orders': safe_percentage(regular_stats['total_orders'], total_stats['total_orders']),
                'revenue': safe_percentage(regular_stats['total_revenue'], total_stats['total_revenue'])
            },
            'kyc': {
                'customers': safe_percentage(kyc_stats['total_customers'], total_stats['total_customers']),
                'orders': safe_percentage(kyc_stats['total_orders'], total_stats['total_orders']),
                'revenue': safe_percentage(kyc_stats['total_revenue'], total_stats['total_revenue'])
            },
            'reseller': {
                'customers': safe_percentage(reseller_stats['total_customers'], total_stats['total_customers']),
                'orders': safe_percentage(reseller_stats['total_orders'], total_stats['total_orders']),
                'revenue': safe_percentage(reseller_stats['total_revenue'], total_stats['total_revenue'])
            }
        }
        
        return {
            'regular': regular_stats,
            'kyc': kyc_stats,
            'reseller': reseller_stats,
            'total': total_stats,
            'percentages': percentages,
            'period': period,
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d')
        }
