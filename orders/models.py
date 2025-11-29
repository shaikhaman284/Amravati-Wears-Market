from django.db import models
from django.conf import settings
from shops.models import Shop
from products.models import Product
from decimal import Decimal
import uuid


class Order(models.Model):
    ORDER_STATUS = [
        ('placed', 'Placed'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('cod', 'Cash on Delivery'),
        ('paid', 'Paid'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='orders')

    # Delivery Details
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=15)
    delivery_address = models.TextField()
    city = models.CharField(max_length=100, default='Amravati')
    pincode = models.CharField(max_length=6)
    landmark = models.CharField(max_length=255, blank=True, null=True)

    # Pricing - CRITICAL LOGIC
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # Sum of display_prices
    cod_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ₹50 if subtotal < ₹500
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # subtotal + cod_fee

    # Commission & Payout
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Platform earns
    seller_payout_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Seller receives

    # Status
    order_status = models.CharField(max_length=15, choices=ORDER_STATUS, default='placed')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='cod')
    cancellation_reason = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'order_status']),
            models.Index(fields=['shop', 'order_status']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: ORD + timestamp + random
            self.order_number = f"ORD{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate all order totals based on order items"""
        items = self.items.all()

        # Subtotal = sum of (display_price × quantity)
        self.subtotal = sum(item.item_subtotal for item in items)

        # COD Fee Logic: ₹50 if subtotal < ₹500, else ₹0
        if self.subtotal < Decimal('500'):
            self.cod_fee = Decimal('50.00')
        else:
            self.cod_fee = Decimal('0.00')

        # Total = subtotal + COD fee
        self.total_amount = self.subtotal + self.cod_fee

        # Commission = sum of (display_price - base_price) × quantity
        self.commission_amount = sum(item.commission_amount for item in items)

        # Seller payout = sum of (base_price × quantity)
        self.seller_payout_amount = sum(item.seller_amount for item in items)

        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)  # NEW

    # Snapshots (prices at time of order)
    product_name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)  # What seller gets per unit
    display_price = models.DecimalField(max_digits=10, decimal_places=2)  # What customer pays per unit
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)

    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)

    # Calculated fields
    item_subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # display_price × quantity
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)  # (display - base) × quantity
    seller_amount = models.DecimalField(max_digits=10, decimal_places=2)  # base_price × quantity

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Calculate item totals
        self.item_subtotal = self.display_price * Decimal(str(self.quantity))
        self.commission_amount = (self.display_price - self.base_price) * Decimal(str(self.quantity))
        self.seller_amount = self.base_price * Decimal(str(self.quantity))
        super().save(*args, **kwargs)