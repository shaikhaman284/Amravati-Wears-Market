from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


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


class SiteVisitor(models.Model):
    """
    Track unique site visitors for analytics
    A visitor is considered unique if they haven't visited in the last 24 hours
    """
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    visited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'site_visitors'
        ordering = ['-visited_at']
        indexes = [
            models.Index(fields=['ip_address', 'visited_at']),
        ]
    
    def __str__(self):
        return f"{self.ip_address} - {self.visited_at}"
    
    @classmethod
    def get_unique_visitors_count(cls):
        """
        Count unique visitors in the last 30 days
        """
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return cls.objects.filter(visited_at__gte=thirty_days_ago).values('ip_address').distinct().count()
    
    @classmethod
    def record_visit(cls, ip_address, user_agent=None):
        """
        Record a visit if the IP hasn't visited in the last 24 hours
        """
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        recent_visit = cls.objects.filter(
            ip_address=ip_address,
            visited_at__gte=twenty_four_hours_ago
        ).exists()
        
        if not recent_visit:
            cls.objects.create(ip_address=ip_address, user_agent=user_agent)
            return True
        return False


class NewsletterSubscriber(models.Model):
    """
    Track newsletter subscribers for email marketing
    """
    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'newsletter_subscribers'
        ordering = ['-subscribed_at']
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
    
    def __str__(self):
        return self.email
    
    @classmethod
    def get_active_subscribers(cls):
        """
        Get all active newsletter subscribers
        """
        return cls.objects.filter(is_active=True)