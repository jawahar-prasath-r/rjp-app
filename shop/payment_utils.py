"""
Payment utility functions for the dry fish shop
"""
import uuid
import json
import razorpay
from django.conf import settings
from django.urls import reverse


class PaymentProcessor:
    """Handle different payment methods"""

    @staticmethod
    def generate_transaction_id():
        """Generate a unique transaction ID"""
        return f"DFS_{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def get_razorpay_client():
        """Get Razorpay client instance"""
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    @staticmethod
    def create_razorpay_order(order):
        """Create Razorpay order for payment"""
        # Check if we have valid Razorpay credentials
        if (settings.RAZORPAY_KEY_ID == 'rzp_test_YOUR_KEY_ID' or
            settings.RAZORPAY_KEY_SECRET == 'YOUR_SECRET_KEY'):
            # Demo mode - return mock order
            return {
                'id': f'order_demo_{PaymentProcessor.generate_transaction_id()}',
                'amount': int(float(order.total_amount) * 100),
                'currency': 'INR',
                'status': 'created',
                'receipt': f'order_{order.id}'
            }

        client = PaymentProcessor.get_razorpay_client()

        razorpay_order = client.order.create({
            'amount': int(float(order.total_amount) * 100),  # Amount in paise
            'currency': 'INR',
            'receipt': f'order_{order.id}',
            'notes': {
                'order_id': order.id,
                'product': order.product,
                'quantity': order.quantity,
                'customer_name': order.name,
                'customer_mobile': order.mobile
            }
        })

        return razorpay_order

    @staticmethod
    def verify_razorpay_payment(payment_id, order_id, signature):
        """Verify Razorpay payment signature"""
        # Check if we're in demo mode
        if order_id.startswith('order_demo_'):
            # Demo mode - always return True for testing
            return True

        client = PaymentProcessor.get_razorpay_client()

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            return True
        except:
            return False

    @staticmethod
    def get_google_pay_config():
        """Get Google Pay configuration for Razorpay"""
        return {
            'environment': 'TEST',  # Change to 'PRODUCTION' for live
            'apiVersion': 2,
            'apiVersionMinor': 0,
            'allowedPaymentMethods': [{
                'type': 'CARD',
                'parameters': {
                    'allowedAuthMethods': ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
                    'allowedCardNetworks': ['MASTERCARD', 'VISA', 'RUPAY']
                },
                'tokenizationSpecification': {
                    'type': 'PAYMENT_GATEWAY',
                    'parameters': {
                        'gateway': 'razorpay',
                        'gatewayMerchantId': settings.RAZORPAY_KEY_ID
                    }
                }
            }],
            'merchantInfo': {
                'merchantId': settings.RAZORPAY_KEY_ID,
                'merchantName': settings.MERCHANT_NAME
            }
        }
    
    @staticmethod
    def create_payment_request(order):
        """Create payment request data"""
        return {
            'order_id': order.id,
            'amount': float(order.total_amount),
            'currency': 'INR',
            'description': f'{order.product} - {order.quantity}kg',
            'customer': {
                'name': order.name,
                'mobile': order.mobile,
                'email': order.user.email if order.user else ''
            }
        }
    
    @staticmethod
    def get_upi_payment_url(order):
        """Generate UPI payment URL"""
        upi_id = settings.UPI_ID
        amount = order.total_amount
        transaction_id = PaymentProcessor.generate_transaction_id()

        # Update order with transaction ID
        order.transaction_id = transaction_id
        order.save()

        upi_url = f"upi://pay?pa={upi_id}&pn={settings.MERCHANT_NAME}&am={amount}&cu=INR&tn=Order {order.id}&tr={transaction_id}"
        return upi_url

    @staticmethod
    def get_google_pay_url(order):
        """Generate Google Pay specific UPI URL"""
        transaction_id = PaymentProcessor.generate_transaction_id()
        order.transaction_id = transaction_id
        order.save()

        amount = str(order.total_amount)
        # Google Pay specific UPI URL format
        google_pay_url = f"tez://upi/pay?pa={settings.UPI_ID}&pn={settings.MERCHANT_NAME}&am={amount}&cu=INR&tn=Order {order.id} - {order.get_product_display()}&tr={transaction_id}"

        return google_pay_url

    @staticmethod
    def get_phonepe_url(order):
        """Generate PhonePe specific UPI URL"""
        transaction_id = PaymentProcessor.generate_transaction_id()
        order.transaction_id = transaction_id
        order.save()

        amount = str(order.total_amount)
        # PhonePe specific UPI URL format
        phonepe_url = f"phonepe://pay?pa={settings.UPI_ID}&pn={settings.MERCHANT_NAME}&am={amount}&cu=INR&tn=Order {order.id} - {order.get_product_display()}&tr={transaction_id}"

        return phonepe_url

    @staticmethod
    def get_paytm_url(order):
        """Generate Paytm specific UPI URL"""
        transaction_id = PaymentProcessor.generate_transaction_id()
        order.transaction_id = transaction_id
        order.save()

        amount = str(order.total_amount)
        # Paytm specific UPI URL format
        paytm_url = f"paytmmp://pay?pa={settings.UPI_ID}&pn={settings.MERCHANT_NAME}&am={amount}&cu=INR&tn=Order {order.id} - {order.get_product_display()}&tr={transaction_id}"

        return paytm_url
    
    @staticmethod
    def verify_payment(transaction_id, payment_method):
        """Verify payment status (mock implementation)"""
        # In a real implementation, you would call the payment gateway API
        # For now, we'll return a mock response
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'payment_method': payment_method,
            'verified': True
        }


class OfflinePaymentHandler:
    """Handle offline payment methods"""
    
    @staticmethod
    def get_bank_details():
        """Get bank account details for bank transfer"""
        return {
            'bank_name': 'State Bank of India',
            'account_holder': 'JAWAHAR PRASATH R',
            'account_number': '6522940425198622',
            'ifsc_code': 'SBIN0000842',
            'branch': 'Gudiyattam'
        }
    
    @staticmethod
    def get_cod_instructions():
        """Get Cash on Delivery instructions"""
        return {
            'title': 'Cash on Delivery',
            'instructions': [
                'Pay cash when your order is delivered',
                'Please keep exact change ready',
                'Our delivery person will provide a receipt',
                'COD available ALL OVER TAMILNADU'
            ],
            'cod_charges': 50  # COD handling charges
        }
    
    @staticmethod
    def process_offline_payment(order, payment_method):
        """Process offline payment methods"""
        if payment_method == 'cash_on_delivery':
            order.payment_status = 'pending'
            order.transaction_id = PaymentProcessor.generate_transaction_id()
        elif payment_method == 'bank_transfer':
            order.payment_status = 'pending'
            order.transaction_id = PaymentProcessor.generate_transaction_id()
        
        order.save()
        return True
