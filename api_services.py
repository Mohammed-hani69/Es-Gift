#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمات API للتعامل مع OneCard وأي APIs أخرى
"""

import requests
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from models import db, APISettings, APIProduct, APITransaction, Product
from flask import current_app

# معرفات المنتجات للاختبار
TEST_PRODUCT_IDS = ["3770", "3771", "3772", "3773", "3774"]

class OnecardAPIService:
    """خدمة API لـ OneCard - متوافق مع Integration API Staging"""
    
    def __init__(self, api_settings):
        self.api_settings = api_settings
        self.base_url = api_settings.api_url or "https://bbapi.ocstaging.net/integration"
        self.reseller_username = api_settings.reseller_username
        self.secret_key = api_settings.secret_key
        
        # URLs للإنتاج والاختبار
        self.production_url = "https://apis.bitaqatybusiness.com/integration"
        self.staging_url = "https://bbapi.ocstaging.net/integration"
    
    def _generate_password(self, *args):
        """توليد كلمة المرور MD5 - متوافق مع OneCard API"""
        # MD5 (resellerUsername + args + secretKey)
        text = self.reseller_username + ''.join(str(arg) for arg in args) + self.secret_key
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _make_request(self, endpoint, data):
        """إجراء طلب API مع معالجة محسنة للأخطاء"""
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ES-Gift-Integration/1.0'
            }
            
            current_app.logger.info(f"Making API request to: {url}")
            current_app.logger.debug(f"Request data: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            current_app.logger.info(f"API Response Status: {response.status_code}")
            
            # معالجة استجابة HTTP
            if response.status_code == 200:
                try:
                    result = response.json()
                    current_app.logger.debug(f"API Response: {json.dumps(result, indent=2)}")
                    return result
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response from API"}
            else:
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {"error": "Request timeout - API did not respond within 30 seconds"}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection error - Unable to connect to API server"}
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"API Request Error: {e}")
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            current_app.logger.error(f"Unexpected error: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def check_balance(self):
        """فحص الرصيد - Check Balance API"""
        password = self._generate_password()
        data = {
            "resellerUsername": self.reseller_username,
            "password": password
        }
        return self._make_request("check-balance", data)
    
    def get_products_list(self, merchant_id=""):
        """جلب قائمة المنتجات المفصلة - Get Detailed Products List API"""
        # إذا لم يتم تمرير merchant_id، استخدم من الإعدادات
        if not merchant_id:
            try:
                if self.api_settings.settings_json:
                    import json
                    settings = json.loads(self.api_settings.settings_json)
                    merchant_id = settings.get('merchant_id', '315325')  # القيمة الافتراضية
                else:
                    merchant_id = '315325'  # fallback
            except Exception as e:
                current_app.logger.warning(f"Could not parse settings_json: {e}")
                merchant_id = '315325'  # fallback
        
        current_app.logger.info(f"Getting products for merchant ID: {merchant_id}")
        
        # MD5 (resellerUsername + merchantId + secretKey)
        password = self._generate_password(merchant_id)
        data = {
            "resellerUsername": self.reseller_username,
            "password": password,
            "merchantId": merchant_id
        }
        return self._make_request("detailed-products-list", data)
    
    def get_product_info(self, product_id):
        """جلب معلومات منتج محدد - Get Product Detailed Info API"""
        password = self._generate_password(product_id)
        data = {
            "resellerUsername": self.reseller_username,
            "password": password,
            "productID": product_id
        }
        return self._make_request("product-detailed-info", data)
    
    def purchase_product(self, product_id, reseller_ref_number, terminal_id=""):
        """شراء منتج - Purchase Product API"""
        password = self._generate_password(product_id, reseller_ref_number)
        data = {
            "resellerUsername": self.reseller_username,
            "password": password,
            "productID": product_id,
            "resellerRefNumber": reseller_ref_number,  # رقم مرجعي فريد
            "terminalId": terminal_id  # غير مطلوب أن يكون فريد
        }
        return self._make_request("purchase-product", data)
    
    def check_transaction_status(self, reseller_ref_number):
        """فحص حالة المعاملة - Check Transaction Status API"""
        password = self._generate_password(reseller_ref_number)
        data = {
            "resellerUsername": self.reseller_username,
            "password": password,
            "resellerRefNumber": reseller_ref_number
        }
        return self._make_request("check-transaction-status", data)
    
    def get_merchant_list(self):
        """جلب قائمة التجار - Get Merchant List API"""
        password = self._generate_password()
        data = {
            "resellerUsername": self.reseller_username,
            "password": password
        }
        return self._make_request("get-merchant-list", data)
    
    def reconcile(self, date_from, date_to, is_successful=True):
        """التسوية - Reconcile API"""
        password = self._generate_password(date_from, date_to, str(is_successful))
        data = {
            "resellerUsername": self.reseller_username,
            "password": password,
            "dateFrom": date_from,  # تنسيق: yyyy-mm-dd hh:mm:ss
            "dateTo": date_to,      # تنسيق: yyyy-mm-dd hh:mm:ss
            "isSuccessful": str(is_successful)  # "True" أو "False"
        }
        return self._make_request("reconcile", data)
    
    def generate_unique_ref_number(self):
        """توليد رقم مرجعي فريد للمعاملات"""
        import time
        import random
        timestamp = str(int(time.time()))
        random_num = str(random.randint(1000, 9999))
        return f"ES{timestamp}{random_num}"
    
    def test_products_availability(self):
        """اختبار توفر المنتجات المحددة للاختبار"""
        results = {}
        for product_id in TEST_PRODUCT_IDS:
            try:
                response = self.get_product_info(product_id)
                if 'error' in response:
                    results[product_id] = {'status': 'error', 'message': response['error']}
                else:
                    name = response.get('name') or response.get('productName', 'غير محدد')
                    price = response.get('price') or response.get('sellingPrice', 0)
                    available = response.get('inStock', True)
                    results[product_id] = {
                        'status': 'success',
                        'name': name,
                        'price': price,
                        'available': available
                    }
            except Exception as e:
                results[product_id] = {'status': 'error', 'message': str(e)}
        return results

class APIManager:
    """مدير عام لجميع APIs مع دعم كامل لـ OneCard"""
    
    @staticmethod
    def get_api_service(api_settings):
        """إرجاع خدمة API المناسبة حسب النوع"""
        if api_settings.api_type == 'onecard':
            return OnecardAPIService(api_settings)
        # يمكن إضافة خدمات API أخرى هنا
        else:
            raise ValueError(f"Unsupported API type: {api_settings.api_type}")
    
    @staticmethod
    def test_api_connection(api_settings):
        """اختبار الاتصال بـ API"""
        try:
            service = APIManager.get_api_service(api_settings)
            response = service.check_balance()
            
            if 'error' in response:
                return False, response['error']
            
            return True, "Connection successful", response
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    @staticmethod
    def sync_products(api_settings_id):
        """مزامنة المنتجات من API مع معالجة محسنة"""
        try:
            api_settings = APISettings.query.get(api_settings_id)
            if not api_settings:
                return False, "API settings not found"
            
            if not api_settings.is_active:
                return False, "API is not active"
            
            service = APIManager.get_api_service(api_settings)
            
            # تحديث حالة البداية
            api_settings.sync_status = 'pending'
            db.session.commit()
            
            # جلب قائمة المنتجات
            response = service.get_products_list()
            
            if 'error' in response:
                api_settings.sync_status = 'error'
                api_settings.error_message = response['error']
                db.session.commit()
                return False, response['error']
            
            # معالجة المنتجات
            products_synced = 0
            products_updated = 0
            products_added = 0
            
            # معالجة بيانات OneCard API
            products_data = []
            if isinstance(response, dict):
                if 'products' in response:
                    products_data = response['products']
                elif 'result' in response and isinstance(response['result'], list):
                    products_data = response['result']
                elif isinstance(response, list):
                    products_data = response
            
            if not products_data:
                api_settings.sync_status = 'success'
                api_settings.last_sync = datetime.utcnow()
                api_settings.error_message = None
                db.session.commit()
                return True, "No products found to sync"
            
            for product_data in products_data:
                try:
                    # استخراج معرف المنتج
                    product_id = str(product_data.get('id') or product_data.get('productId') or product_data.get('ProductId', ''))
                    if not product_id:
                        continue
                    
                    # البحث عن المنتج الموجود
                    api_product = APIProduct.query.filter_by(
                        api_settings_id=api_settings_id,
                        external_product_id=product_id
                    ).first()
                    
                    # استخراج البيانات
                    name = product_data.get('name') or product_data.get('productName') or product_data.get('ProductName', '')
                    description = product_data.get('description') or product_data.get('productDescription', '')
                    category = product_data.get('category') or product_data.get('categoryName', '')
                    price = float(product_data.get('price') or product_data.get('sellingPrice', 0))
                    currency = product_data.get('currency', 'SAR')
                    stock_status = product_data.get('inStock', True)
                    
                    if not api_product:
                        # إنشاء منتج جديد
                        api_product = APIProduct(
                            api_settings_id=api_settings_id,
                            external_product_id=product_id,
                            name=name,
                            description=description,
                            category=category,
                            price=Decimal(str(price)),
                            currency=currency,
                            stock_status=stock_status,
                            raw_data=json.dumps(product_data, ensure_ascii=False)
                        )
                        db.session.add(api_product)
                        products_added += 1
                    else:
                        # تحديث المنتج الموجود
                        api_product.name = name
                        api_product.description = description
                        api_product.category = category
                        api_product.price = Decimal(str(price))
                        api_product.currency = currency
                        api_product.stock_status = stock_status
                        api_product.raw_data = json.dumps(product_data, ensure_ascii=False)
                        api_product.updated_at = datetime.utcnow()
                        products_updated += 1
                    
                    products_synced += 1
                    
                except Exception as e:
                    current_app.logger.error(f"Error processing product {product_data}: {e}")
                    continue
            
            # تحديث حالة المزامنة
            api_settings.sync_status = 'success'
            api_settings.last_sync = datetime.utcnow()
            api_settings.error_message = None
            db.session.commit()
            
            message = f"تمت المزامنة بنجاح - إضافة: {products_added}, تحديث: {products_updated}, إجمالي: {products_synced}"
            return True, message
            
        except Exception as e:
            current_app.logger.error(f"Sync error: {e}")
            if 'api_settings' in locals():
                api_settings.sync_status = 'error'
                api_settings.error_message = str(e)
                db.session.commit()
            return False, f"خطأ في المزامنة: {str(e)}"
    
    @staticmethod
    def import_product_to_local(api_product_id):
        """استيراد منتج API كمنتج محلي"""
        try:
            api_product = APIProduct.query.get(api_product_id)
            if not api_product:
                return False, "API product not found"
            
            if api_product.is_imported:
                return False, "Product already imported"
            
            # إنشاء منتج محلي جديد
            from models import Product, Category, Subcategory
            
            # البحث عن فئة مناسبة أو إنشاء واحدة
            category = Category.query.filter_by(name=api_product.category).first()
            if not category and api_product.category:
                category = Category(
                    name=api_product.category,
                    description=f"Category imported from API",
                    is_active=True
                )
                db.session.add(category)
                db.session.flush()
            
            local_product = Product(
                name=api_product.name,
                description=api_product.description,
                category_id=category.id if category else None,
                price=float(api_product.price),
                is_active=True,
                stock_quantity=100,  # قيمة افتراضية
                image_url='/static/images/default-product.jpg'
            )
            
            db.session.add(local_product)
            db.session.flush()
            
            # ربط المنتج API بالمنتج المحلي
            api_product.product_id = local_product.id
            api_product.is_imported = True
            
            db.session.commit()
            
            return True, f"تم استيراد المنتج '{api_product.name}' بنجاح"
            
        except Exception as e:
            current_app.logger.error(f"Import error: {e}")
            db.session.rollback()
            return False, f"خطأ في الاستيراد: {str(e)}"
    
    @staticmethod
    def purchase_api_product(api_product_id, order_id, quantity=1):
        """شراء منتج من API"""
        try:
            api_product = APIProduct.query.get(api_product_id)
            if not api_product:
                return False, "API product not found", None
            
            service = APIManager.get_api_service(api_product.api_setting)
            ref_number = service.generate_unique_ref_number()
            
            # تسجيل المعاملة
            transaction = APITransaction(
                api_settings_id=api_product.api_settings_id,
                order_id=order_id,
                external_product_id=api_product.external_product_id,
                reseller_ref_number=ref_number,
                transaction_status='pending',
                amount=api_product.price * quantity,
                currency=api_product.currency
            )
            db.session.add(transaction)
            db.session.flush()
            
            # شراء المنتج
            response = service.purchase_product(
                api_product.external_product_id,
                ref_number
            )
            
            if 'error' in response:
                transaction.transaction_status = 'failed'
                transaction.purchase_response = json.dumps(response)
                db.session.commit()
                return False, response['error'], transaction
            
            # تحديث المعاملة
            transaction.transaction_status = 'success'
            transaction.purchase_response = json.dumps(response)
            
            # استخراج أكواد المنتج إذا كانت متوفرة
            product_codes = None
            if 'codes' in response:
                transaction.product_codes = json.dumps(response['codes'])
                product_codes = response['codes']
            elif 'result' in response and isinstance(response['result'], dict):
                result = response['result']
                if 'codes' in result:
                    transaction.product_codes = json.dumps(result['codes'])
                    product_codes = result['codes']
                elif 'serialNumbers' in result:
                    transaction.product_codes = json.dumps(result['serialNumbers'])
                    product_codes = result['serialNumbers']
                elif 'codeDetails' in result:
                    # OneCard format
                    codes_list = []
                    for code_detail in result['codeDetails']:
                        if 'code' in code_detail:
                            codes_list.append(code_detail['code'])
                        elif 'serialNumber' in code_detail:
                            codes_list.append(code_detail['serialNumber'])
                    if codes_list:
                        transaction.product_codes = json.dumps(codes_list)
                        product_codes = codes_list
            elif 'serialNumbers' in response:
                transaction.product_codes = json.dumps(response['serialNumbers'])
                product_codes = response['serialNumbers']
            elif 'codeDetails' in response:
                # OneCard direct format
                codes_list = []
                for code_detail in response['codeDetails']:
                    if 'code' in code_detail:
                        codes_list.append(code_detail['code'])
                    elif 'serialNumber' in code_detail:
                        codes_list.append(code_detail['serialNumber'])
                if codes_list:
                    transaction.product_codes = json.dumps(codes_list)
                    product_codes = codes_list
            
            # تسجيل معلومات الأكواد المستلمة
            if product_codes:
                current_app.logger.info(f"Received {len(product_codes)} product codes for transaction {ref_number}")
            else:
                current_app.logger.warning(f"No product codes received for transaction {ref_number}")
                # محاولة استخراج أي أكواد من الاستجابة الكاملة
                response_str = json.dumps(response)
                if 'code' in response_str.lower() or 'serial' in response_str.lower():
                    transaction.product_codes = json.dumps(response)
                    current_app.logger.info(f"Stored full response as product codes for transaction {ref_number}")
            
            db.session.commit()
            
            return True, "تم الشراء بنجاح", transaction
            
        except Exception as e:
            current_app.logger.error(f"Purchase error: {e}")
            if 'transaction' in locals():
                transaction.transaction_status = 'failed'
                transaction.purchase_response = json.dumps({"error": str(e)})
                db.session.commit()
            return False, f"خطأ في الشراء: {str(e)}", None