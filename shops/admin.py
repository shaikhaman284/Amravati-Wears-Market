from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from .models import Category, Shop, NewsletterSubscriber


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'owner', 'city', 'commission_rate', 'approval_status', 'created_at']
    list_filter = ['approval_status', 'city', 'is_approved']
    search_fields = ['shop_name', 'owner__name', 'owner__phone']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Shop Info', {'fields': ('owner', 'shop_name', 'address', 'city', 'pincode', 'contact_number', 'shop_image')}),
        ('Commission', {'fields': ('commission_rate',)}),
        ('Approval', {'fields': ('approval_status', 'is_approved', 'rejection_reason')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    actions = ['approve_shops', 'reject_shops']

    def approve_shops(self, request, queryset):
        queryset.update(approval_status='approved', is_approved=True)
        self.message_user(request, f"{queryset.count()} shops approved successfully.")

    approve_shops.short_description = "Approve selected shops"

    def reject_shops(self, request, queryset):
        queryset.update(approval_status='rejected', is_approved=False)
        self.message_user(request, f"{queryset.count()} shops rejected.")

    reject_shops.short_description = "Reject selected shops"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at']
    
    actions = ['send_new_product_email', 'send_new_shop_email', 'send_custom_newsletter', 'deactivate_subscribers']
    
    def send_new_product_email(self, request, queryset):
        """
        Send email notification about new products
        """
        active_subscribers = queryset.filter(is_active=True)
        email_list = list(active_subscribers.values_list('email', flat=True))
        
        if not email_list:
            self.message_user(request, "No active subscribers selected.", level='warning')
            return
        
        subject = "🆕 New Products Added to Amravati Wears Market!"
        message = """
Hello!

Exciting news! We've just added new products to our marketplace.

Check out the latest arrivals from your favorite local shops in Amravati.

👉 Visit now: https://awm27.shop

Happy Shopping!
Amravati Wears Market Team

---
You're receiving this because you subscribed to our newsletter.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                email_list,
                fail_silently=False,
            )
            self.message_user(request, f"Successfully sent new product email to {len(email_list)} subscribers! 📧")
        except Exception as e:
            self.message_user(request, f"Failed to send emails: {str(e)}", level='error')
    
    send_new_product_email.short_description = "📦 Send New Product Email"
    
    def send_new_shop_email(self, request, queryset):
        """
        Send email notification about new shops
        """
        active_subscribers = queryset.filter(is_active=True)
        email_list = list(active_subscribers.values_list('email', flat=True))
        
        if not email_list:
            self.message_user(request, "No active subscribers selected.", level='warning')
            return
        
        subject = "🏪 New Shop Joined Amravati Wears Market!"
        message = """
Hello!

Great news! A new shop has joined our marketplace.

Discover more local stores and explore their unique collections.

👉 Browse shops: https://awm27.shop

Happy Shopping!
Amravati Wears Market Team

---
You're receiving this because you subscribed to our newsletter.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                email_list,
                fail_silently=False,
            )
            self.message_user(request, f"Successfully sent new shop email to {len(email_list)} subscribers! 📧")
        except Exception as e:
            self.message_user(request, f"Failed to send emails: {str(e)}", level='error')
    
    send_new_shop_email.short_description = "🏪 Send New Shop Email"
    
    def send_custom_newsletter(self, request, queryset):
        """
        Send custom newsletter (you can modify the message before sending)
        """
        active_subscribers = queryset.filter(is_active=True)
        email_list = list(active_subscribers.values_list('email', flat=True))
        
        if not email_list:
            self.message_user(request, "No active subscribers selected.", level='warning')
            return
        
        subject = "📢 Update from Amravati Wears Market"
        message = """
Hello!

We have an important update for you!

[Server is down because of maintenance]

Visit our marketplace: https://awm27.shop

Best regards,
Amravati Wears Market Team

---
You're receiving this because you subscribed to our newsletter.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                email_list,
                fail_silently=False,
            )
            self.message_user(request, f"Successfully sent custom newsletter to {len(email_list)} subscribers! 📧")
        except Exception as e:
            self.message_user(request, f"Failed to send emails: {str(e)}", level='error')
    
    send_custom_newsletter.short_description = "📧 Send Custom Newsletter"
    
    def deactivate_subscribers(self, request, queryset):
        """
        Deactivate selected subscribers (unsubscribe)
        """
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} subscribers deactivated.")
    
    deactivate_subscribers.short_description = "🚫 Deactivate Selected Subscribers"