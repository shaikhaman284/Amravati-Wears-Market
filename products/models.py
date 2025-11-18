from django.db import models
from shops.models import Shop, Category
from decimal import Decimal


class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')

    name = models.CharField(max_length=255)
    description = models.TextField()

    # CRITICAL: Base price is what seller receives
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Commission rate (copied from shop, can be overridden)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)

    # Display price = what customer pays (auto-calculated)
    display_price = models.DecimalField(max_digits=10, decimal_places=2)

    stock_quantity = models.PositiveIntegerField(default=0)

    # Variants
    sizes = models.JSONField(default=list, blank=True)  # ["S", "M", "L", "XL"]
    colors = models.JSONField(default=list, blank=True)  # ["Red", "Blue", "Green"]

    # Images
    image1 = models.URLField(max_length=500, blank=True, null=True)
    image2 = models.URLField(max_length=500, blank=True, null=True)
    image3 = models.URLField(max_length=500, blank=True, null=True)
    image4 = models.URLField(max_length=500, blank=True, null=True)
    image5 = models.URLField(max_length=500, blank=True, null=True)

    # SEO & Filtering
    slug = models.SlugField(max_length=300, blank=True)

    # Ratings
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['shop', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-calculate display_price based on base_price and commission_rate
        if self.base_price and self.commission_rate:
            self.display_price = self.base_price * (1 + self.commission_rate / Decimal('100'))

        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def get_commission_amount(self):
        """Returns the commission amount for this product"""
        return self.display_price - self.base_price

    def is_in_stock(self):
        return self.stock_quantity > 0