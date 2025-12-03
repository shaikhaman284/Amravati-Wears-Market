from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from shops.models import Shop, Category
from products.models import Product


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    APPLICABILITY_CHOICES = [
        ('all', 'All Products'),
        ('category', 'Specific Category'),
        ('product', 'Specific Product'),
    ]

    # Basic Info
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=20, unique=True, db_index=True, help_text="Unique coupon code (e.g., SAVE20)")

    # Discount Details
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Percentage (0-100) or Fixed amount"
    )

    # Applicability
    applicability = models.CharField(max_length=10, choices=APPLICABILITY_CHOICES, default='all')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='coupons')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='coupons')

    # Constraints
    min_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum cart value to apply coupon"
    )
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total maximum uses (null = unlimited)"
    )
    max_uses_per_customer = models.PositiveIntegerField(
        default=1,
        help_text="Maximum uses per customer"
    )

    # Validity
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    # Status & Tracking
    is_active = models.BooleanField(default=True)
    times_used = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop', 'is_active']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.code} - {self.shop.shop_name}"

    def save(self, *args, **kwargs):
        # Ensure code is uppercase
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if coupon is valid right now"""
        now = timezone.now()

        # Check if active
        if not self.is_active:
            return False, "Coupon is inactive"

        # Check validity period
        if now < self.valid_from:
            return False, "Coupon not yet valid"

        if now > self.valid_to:
            return False, "Coupon has expired"

        # Check max uses
        if self.max_uses and self.times_used >= self.max_uses:
            return False, "Coupon usage limit reached"

        return True, "Valid"

    def can_user_use(self, user):
        """Check if user can use this coupon"""
        usage_count = CouponUsage.objects.filter(
            coupon=self,
            customer=user
        ).count()

        if usage_count >= self.max_uses_per_customer:
            return False, f"You have already used this coupon {self.max_uses_per_customer} time(s)"

        return True, "Can use"

    def get_discount_display(self):
        """Get human-readable discount value"""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}%"
        else:
            return f"₹{self.discount_value}"


class CouponUsage(models.Model):
    """Track coupon usage by customers"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='coupon_usage')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_usages'
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['coupon', 'customer']),
        ]

    def __str__(self):
        return f"{self.customer.name} used {self.coupon.code}"