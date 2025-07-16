from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Order(models.Model):
    PRODUCT_CHOICES = [
        ('motha kendai', 'Motha Kendai'),
        ('netthili', 'Netthili'),
        ('vaalai', 'Vaalai'),
        ('goa netthili', 'Goa Netthili'),
        ('yeera', 'Yeera'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('google_pay', 'Google Pay'),
        ('phonepe', 'PhonePe'),
        ('paytm', 'Paytm'),
        ('upi', 'UPI'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # Product prices (per kg)
    PRODUCT_PRICES = {
        'motha kendai': 450,
        'netthili': 400,
        'vaalai': 300,
        'goa netthili': 600,
        'yeera': 500,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    address = models.TextField()
    product = models.CharField(max_length=50, choices=PRODUCT_CHOICES)
    quantity = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash_on_delivery')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate total amount based on product and quantity
        if self.product in self.PRODUCT_PRICES:
            self.total_amount = self.PRODUCT_PRICES[self.product] * self.quantity
        super().save(*args, **kwargs)

    def get_product_price(self):
        return self.PRODUCT_PRICES.get(self.product, 0)

    def __str__(self):
        return f"{self.name} - {self.product} (₹{self.total_amount})"
