from django.db import models
from shops.models import Shop, Category
from decimal import Decimal
import uuid


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

    # NEW: MRP Field for real discounts
    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum Retail Price (optional)"
    )

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

    # NEW: MRP Discount Calculation
    def get_discount_percentage(self):
        """Calculate discount percentage from MRP"""
        if self.mrp and self.mrp > self.display_price:
            return round(((self.mrp - self.display_price) / self.mrp) * 100, 2)
        return 0

    # EXISTING METHODS FOR VARIANT SUPPORT
    def update_total_stock(self):
        """Calculate and update total stock from all active variants"""
        from django.db.models import Sum
        total = self.variants.filter(is_active=True).aggregate(
            total=Sum('stock_quantity')
        )['total'] or 0
        # Use update to avoid triggering save() recursion
        Product.objects.filter(id=self.id).update(stock_quantity=total)

    def get_variant(self, size=None, color=None):
        """Get specific variant by size and color"""
        filters = {'is_active': True}
        if size:
            filters['size'] = size
        if color:
            filters['color'] = color
        return self.variants.filter(**filters).first()

    def has_variants(self):
        """Check if product has size/color variants"""
        return self.variants.filter(is_active=True).exists()


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_variants'
        unique_together = ['product', 'size', 'color']
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        variant_name = f"{self.product.name}"
        if self.size:
            variant_name += f" - {self.size}"
        if self.color:
            variant_name += f" - {self.color}"
        return variant_name

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            size_part = self.size or 'NOSIZE'
            color_part = self.color or 'NOCOLOR'
            unique_id = uuid.uuid4().hex[:6].upper()
            self.sku = f"VAR-{self.product.id}-{size_part}-{color_part}-{unique_id}"

        super().save(*args, **kwargs)

        # Update product total stock after saving variant
        self.product.update_total_stock()