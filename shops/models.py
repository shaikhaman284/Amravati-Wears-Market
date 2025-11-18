from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Shop(models.Model):
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shop')
    shop_name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100, default='Amravati')
    pincode = models.CharField(max_length=6)
    contact_number = models.CharField(max_length=15)
    shop_image = models.URLField(max_length=500, blank=True, null=True)

    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)

    is_approved = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shops'
        ordering = ['-created_at']

    def __str__(self):
        return self.shop_name

    def get_product_count(self):
        return self.products.filter(is_active=True).count()