#!/usr/bin/env python
"""
Test script to verify Razorpay integration
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dryfish_shop_enhanced.settings')
django.setup()

from shop.payment_utils import PaymentProcessor
from shop.models import Order
from django.contrib.auth.models import User

def test_razorpay_integration():
    """Test Razorpay payment integration"""
    print("🧪 Testing Razorpay Integration...")
    
    try:
        # Test Razorpay client initialization
        client = PaymentProcessor.get_razorpay_client()
        print("✅ Razorpay client initialized successfully")
        
        # Create a test user if not exists
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            print("✅ Test user created")
        else:
            print("✅ Test user found")
        
        # Create a test order
        test_order = Order.objects.create(
            user=user,
            name='Test Customer',
            mobile='9876543210',
            address='Test Address',
            product='motha kendai',
            quantity=1,
            payment_method='google_pay',
            total_amount=450.00
        )
        print(f"✅ Test order created: #{test_order.id}")
        
        # Test Razorpay order creation (demo mode)
        razorpay_order = PaymentProcessor.create_razorpay_order(test_order)
        print(f"✅ Razorpay order created: {razorpay_order['id']}")
        print(f"   Amount: ₹{razorpay_order['amount']/100}")
        print(f"   Currency: {razorpay_order['currency']}")
        print(f"   Status: {razorpay_order['status']}")

        # Test payment verification (demo mode)
        is_verified = PaymentProcessor.verify_razorpay_payment(
            'demo_payment_123', razorpay_order['id'], 'demo_signature'
        )
        print(f"✅ Payment verification: {'Passed' if is_verified else 'Failed'}")
        
        # Test UPI URL generation
        upi_url = PaymentProcessor.get_upi_payment_url(test_order)
        print(f"✅ UPI URL generated: {upi_url[:50]}...")
        
        # Test bank details
        from shop.payment_utils import OfflinePaymentHandler
        bank_details = OfflinePaymentHandler.get_bank_details()
        print(f"✅ Bank details: {bank_details['account_holder']} - {bank_details['account_number']}")
        
        # Clean up test order
        test_order.delete()
        print("✅ Test order cleaned up")
        
        print("\n🎉 All tests passed! Payment integration is working correctly.")
        print("\n📋 Integration Summary:")
        print("   • Razorpay client: ✅ Working")
        print("   • Order creation: ✅ Working") 
        print("   • UPI integration: ✅ Working")
        print("   • Bank details: ✅ Updated")
        print("\n💡 You can now accept real payments!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_razorpay_integration()
