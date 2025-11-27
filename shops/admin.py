"""
Django Admin configuration for shops app
Production-ready with proper error handling and logging
"""
from django.contrib import admin
from django.contrib import messages
from django.conf import settings
import logging

from .models import Category, Shop, NewsletterSubscriber
from .email_utils import send_bulk_email

logger = logging.getLogger(__name__)


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
        ('Shop Info', {
            'fields': (
                'owner', 'shop_name', 'address', 'city',
                'pincode', 'contact_number', 'shop_image'
            )
        }),
        ('Commission', {
            'fields': ('commission_rate',)
        }),
        ('Approval', {
            'fields': ('approval_status', 'is_approved', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['approve_shops', 'reject_shops']

    def approve_shops(self, request, queryset):
        """Approve selected shops"""
        updated = queryset.update(approval_status='approved', is_approved=True)
        self.message_user(
            request,
            f"✅ {updated} shop(s) approved successfully.",
            messages.SUCCESS
        )
        logger.info(f"Admin {request.user.name} approved {updated} shops")

    approve_shops.short_description = "✅ Approve selected shops"

    def reject_shops(self, request, queryset):
        """Reject selected shops"""
        updated = queryset.update(approval_status='rejected', is_approved=False)
        self.message_user(
            request,
            f"❌ {updated} shop(s) rejected.",
            messages.WARNING
        )
        logger.info(f"Admin {request.user.name} rejected {updated} shops")

    reject_shops.short_description = "❌ Reject selected shops"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at']

    actions = [
        'send_new_product_email',
        'send_new_shop_email',
        'send_custom_newsletter',
        'send_promotional_email',
        'send_seasonal_greetings',
        'deactivate_subscribers',
        'activate_subscribers'
    ]

    def send_new_product_email(self, request, queryset):
        """Send email notification about new products to active subscribers"""
        active_subscribers = queryset.filter(is_active=True)
        email_list = list(active_subscribers.values_list('email', flat=True))

        if not email_list:
            self.message_user(request, "⚠️ No active subscribers selected.", messages.WARNING)
            return

        subject = "🆕 New Products Added to Amravati Wears Market!"

        plain_message = """
Hello!

Exciting news! We've just added new products to our marketplace.

Check out the latest arrivals from your favorite local shops in Amravati.

👉 Visit now: https://awm27.shop

Happy Shopping!
Amravati Wears Market Team

---
You're receiving this because you subscribed to our newsletter.
To unsubscribe, please contact us at support@awm27.shop
        """.strip()

        html_message = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 30px; }
        .button { display: inline-block; background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🆕 New Products Added!</h1>
        </div>
        <div class="content">
            <p>Hello!</p>
            <p>Exciting news! We've just added new products to our marketplace.</p>
            <p>Check out the latest arrivals from your favorite local shops in Amravati.</p>
            <center>
                <a href="https://awm27.shop" class="button">Visit Now</a>
            </center>
            <p>Happy Shopping!<br><strong>Amravati Wears Market Team</strong></p>
        </div>
        <div class="footer">
            <p>You're receiving this because you subscribed to our newsletter.</p>
            <p>To unsubscribe, contact us at support@awm27.shop</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        try:
            logger.info(f"Sending new product email to {len(email_list)} subscribers")
            success_count, failed_emails = send_bulk_email(
                subject=subject,
                message=plain_message,
                recipient_list=email_list,
                html_content=html_message
            )

            if failed_emails:
                self.message_user(
                    request,
                    f"⚠️ Sent to {success_count} subscriber(s). Failed: {len(failed_emails)}. Check logs for details.",
                    messages.WARNING
                )
                logger.warning(f"Failed emails: {failed_emails}")
            else:
                self.message_user(
                    request,
                    f"✅ Successfully sent email to {success_count} subscriber(s)! 📧",
                    messages.SUCCESS
                )

            logger.info(f"New product email sent by {request.user.name}: {success_count} successful, {len(failed_emails)} failed")

        except Exception as e:
            self.message_user(request, f"❌ Failed to send emails: {str(e)}", messages.ERROR)
            logger.error(f"Error sending new product email: {str(e)}", exc_info=True)

    send_new_product_email.short_description = "📦 Send New Product Email"

    def send_new_shop_email(self, request, queryset):
        """Send email notification about new shops to active subscribers"""
        active_subscribers = queryset.filter(is_active=True)
        email_list = list(active_subscribers.values_list('email', flat=True))

        if not email_list:
            self.message_user(request, "⚠️ No active subscribers selected.", messages.WARNING)
            return

        subject = "🏪 New Shop Joined Amravati Wears Market!"

        plain_message = """
Hello!

Great news! A new shop has joined our marketplace.

Discover more local stores and explore their unique collections.

👉 Browse shops: https://awm27.shop

Happy Shopping!
Amravati Wears Market Team

---
You're receiving this because you subscribed to our newsletter.
To unsubscribe, please contact us at support@awm27.shop
        """.strip()

        html_message = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #059669; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 30px; }
        .button { display: inline-block; background: #059669; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏪 New Shop Joined!</h1>
        </div>
        <div class="content">
            <p>Hello!</p>
            <p>Great news! A new shop has joined our marketplace.</p>
            <p>Discover more local stores and explore their unique collections.</p>
            <center>
                <a href="https://awm27.shop" class="button">Browse Shops</a>
            </center>
            <p>Happy Shopping!<br><strong>Amravati Wears Market Team</strong></p>
        </div>
        <div class="footer">
            <p>You're receiving this because you subscribed to our newsletter.</p>
            <p>To unsubscribe, contact us at support@awm27.shop</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        try:
            logger.info(f"Sending new shop email to {len(email_list)} subscribers")
            success_count, failed_emails = send_bulk_email(
                subject=subject,
                message=plain_message,
                recipient_list=email_list,
                html_content=html_message
            )

            if failed_emails:
                self.message_user(
                    request,
                    f"⚠️ Sent to {success_count} subscriber(s). Failed: {len(failed_emails)}. Check logs for details.",
                    messages.WARNING
                )
                logger.warning(f"Failed emails: {failed_emails}")
            else:
                self.message_user(
                    request,
                    f"✅ Successfully sent email to {success_count} subscriber(s)! 📧",
                    messages.SUCCESS
                )

            logger.info(f"New shop email sent by {request.user.name}: {success_count} successful, {len(failed_emails)} failed")

        except Exception as e:
            self.message_user(request, f"❌ Failed to send emails: {str(e)}", messages.ERROR)
            logger.error(f"Error sending new shop email: {str(e)}", exc_info=True)

    send_new_shop_email.short_description = "🏪 Send New Shop Email"

    def send_custom_newsletter(self, request, queryset):
        """Send custom newsletter to active subscribers"""
        active_subscribers = queryset.filter(is_active=True)
        email_list = list(active_subscribers.values_list('email', flat=True))

        if not email_list:
            self.message_user(request, "⚠️ No active subscribers selected.", messages.WARNING)
            return

        subject = "📢 Important Update from Amravati Wears Market"

        plain_message = """
Hello!

We have an important update for you!

Our platform is currently undergoing scheduled maintenance to improve your shopping experience.

We'll be back online shortly with exciting new features!

Thank you for your patience.

Best regards,
Amravati Wears Market Team

---
You're receiving this because you subscribed to our newsletter.
To unsubscribe, please contact us at support@awm27.shop
        """.strip()

        html_message = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #DC2626; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 30px; }
        .alert { background: #FEF2F2; border-left: 4px solid #DC2626; padding: 15px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📢 Important Update</h1>
        </div>
        <div class="content">
            <p>Hello!</p>
            <div class="alert">
                <strong>⚠️ Scheduled Maintenance</strong>
            </div>
            <p>Our platform is currently undergoing scheduled maintenance to improve your shopping experience.</p>
            <p>We'll be back online shortly with exciting new features!</p>
            <p>Thank you for your patience.</p>
            <p>Best regards,<br><strong>Amravati Wears Market Team</strong></p>
        </div>
        <div class="footer">
            <p>You're receiving this because you subscribed to our newsletter.</p>
            <p>To unsubscribe, contact us at support@awm27.shop</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        try:
            logger.info(f"Sending custom newsletter to {len(email_list)} subscribers")
            success_count, failed_emails = send_bulk_email(
                subject=subject,
                message=plain_message,
                recipient_list=email_list,
                html_content=html_message
            )

            if failed_emails:
                self.message_user(
                    request,
                    f"⚠️ Sent to {success_count} subscriber(s). Failed: {len(failed_emails)}. Check logs for details.",
                    messages.WARNING
                )
                logger.warning(f"Failed emails: {failed_emails}")
            else:
                self.message_user(
                    request,
                    f"✅ Successfully sent newsletter to {success_count} subscriber(s)! 📧",
                    messages.SUCCESS
                )

            logger.info(f"Custom newsletter sent by {request.user.name}: {success_count} successful, {len(failed_emails)} failed")

        except Exception as e:
            self.message_user(request, f"❌ Failed to send emails: {str(e)}", messages.ERROR)
            logger.error(f"Error sending custom newsletter: {str(e)}", exc_info=True)

    send_custom_newsletter.short_description = "📧 Send Custom Newsletter"

    def send_promotional_email(self, request, queryset):
        """Send promotional/discount email to active subscribers"""
        active_subscribers = queryset.filter(is_active=True)
        email_list = list(active_subscribers.values_list('email', flat=True))

        if not email_list:
            self.message_user(request, "⚠️ No active subscribers selected.", messages.WARNING)
            return

        subject = "🎉 Special Offer - Up to 50% Off!"

        plain_message = """
Hello!

🎉 SPECIAL OFFER ALERT! 🎉

We're excited to announce a limited-time promotion on Amravati Wears Market!

✨ Get up to 50% OFF on selected items
⏰ Offer valid for 48 hours only
🛍️ Shop from your favorite local stores

Don't miss out on these amazing deals!

👉 Shop now: https://awm27.shop

Hurry! Offer ends soon.

Happy Shopping!
Amravati Wears Market Team

---
You're receiving this because you subscribed to our newsletter.
To unsubscribe, please contact us at support@awm27.shop
        """.strip()

        html_message = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 28px; }
        .badge { background: #FCD34D; color: #92400E; padding: 8px 16px; border-radius: 20px; display: inline-block; margin-top: 10px; font-weight: bold; }
        .content { background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; }
        .offer-box { background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 20px; margin: 20px 0; border-radius: 4px; }
        .offer-box h2 { margin: 0 0 10px 0; color: #92400E; }
        .features { margin: 20px 0; }
        .feature { padding: 10px 0; border-bottom: 1px solid #e5e7eb; }
        .feature:last-child { border-bottom: none; }
        .feature span { font-size: 20px; margin-right: 10px; }
        .button { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; font-size: 16px; }
        .urgency { text-align: center; background: #FEE2E2; color: #991B1B; padding: 15px; border-radius: 6px; margin: 20px 0; font-weight: bold; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; background: #f9fafb; border-radius: 0 0 8px 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 SPECIAL OFFER!</h1>
            <div class="badge">LIMITED TIME ONLY</div>
        </div>
        <div class="content">
            <div class="offer-box">
                <h2>🔥 Up to 50% OFF</h2>
                <p>On selected items across all categories!</p>
            </div>
            <p>Hello!</p>
            <p>We're thrilled to bring you an exclusive promotion on Amravati Wears Market!</p>
            <div class="features">
                <div class="feature">
                    <span>✨</span> <strong>Huge Discounts:</strong> Save up to 50% on selected products
                </div>
                <div class="feature">
                    <span>🛍️</span> <strong>Wide Selection:</strong> Shop from your favorite local stores
                </div>
                <div class="feature">
                    <span>⚡</span> <strong>Limited Time:</strong> Offer valid for 48 hours only
                </div>
            </div>
            <div class="urgency">
                ⏰ Hurry! Offer ends in 48 hours
            </div>
            <center>
                <a href="https://awm27.shop" class="button">🛒 SHOP NOW</a>
            </center>
            <p>Don't miss out on these incredible deals from Amravati's best shops!</p>
            <p>Happy Shopping!<br><strong>Amravati Wears Market Team</strong></p>
        </div>
        <div class="footer">
            <p>You're receiving this because you subscribed to our newsletter.</p>
            <p>To unsubscribe, contact us at support@awm27.shop</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        try:
            logger.info(f"Sending promotional email to {len(email_list)} subscribers")
            success_count, failed_emails = send_bulk_email(
                subject=subject,
                message=plain_message,
                recipient_list=email_list,
                html_content=html_message
            )

            if failed_emails:
                self.message_user(
                    request,
                    f"⚠️ Sent to {success_count} subscriber(s). Failed: {len(failed_emails)}. Check logs for details.",
                    messages.WARNING
                )
                logger.warning(f"Failed emails: {failed_emails}")
            else:
                self.message_user(
                    request,
                    f"✅ Successfully sent promotional email to {success_count} subscriber(s)! 🎉",
                    messages.SUCCESS
                )

            logger.info(f"Promotional email sent by {request.user.name}: {success_count} successful, {len(failed_emails)} failed")

        except Exception as e:
            self.message_user(request, f"❌ Failed to send emails: {str(e)}", messages.ERROR)
            logger.error(f"Error sending promotional email: {str(e)}", exc_info=True)

    send_promotional_email.short_description = "🎉 Send Promotional Email"

    def send_seasonal_greetings(self, request, queryset):
        """Send seasonal greetings (Diwali, New Year, etc.)"""
        active_subscribers = queryset.filter(is_active=True)
        email_list = list(active_subscribers.values_list('email', flat=True))

        if not email_list:
            self.message_user(request, "⚠️ No active subscribers selected.", messages.WARNING)
            return

        subject = "🪔 Happy Diwali from Amravati Wears Market!"

        plain_message = """
Dear Customer,

🪔 HAPPY DIWALI! 🪔

Wishing you and your family a joyous and prosperous Diwali!

May this festival of lights bring happiness, good health, and success to your life.

As we celebrate this auspicious occasion, we're grateful for your continued support.

Enjoy shopping for festive wear and gifts at:
👉 https://awm27.shop

May your Diwali be filled with light, love, and laughter!

Warm wishes,
Amravati Wears Market Team

---
You're receiving this because you subscribed to our newsletter.
To unsubscribe, please contact us at support@awm27.shop
        """.strip()

        html_message = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%); color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 32px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
        .diya { font-size: 48px; margin: 10px 0; }
        .content { background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; }
        .greeting-card { background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; border: 2px solid #FB923C; }
        .greeting-card p { margin: 10px 0; font-size: 16px; color: #7C2D12; }
        .button { display: inline-block; background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; font-size: 16px; }
        .decorative-line { border-top: 2px dashed #FB923C; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; background: #f9fafb; border-radius: 0 0 8px 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="diya">🪔 🪔 🪔</div>
            <h1>Happy Diwali!</h1>
            <p style="margin: 10px 0; font-size: 18px;">Wishing you light, love & prosperity</p>
        </div>
        <div class="content">
            <p><strong>Dear Customer,</strong></p>
            <div class="greeting-card">
                <p style="font-size: 20px; font-weight: bold; margin: 0;">✨ शुभ दीपावली ✨</p>
                <div class="decorative-line"></div>
                <p>May this festival of lights illuminate your life with joy, prosperity, and good health.</p>
                <p>May Goddess Lakshmi bless you with wealth and success.</p>
                <div class="decorative-line"></div>
                <p style="font-style: italic;">"Where there is light, there is hope and happiness"</p>
            </div>
            <p>As we celebrate this auspicious occasion, we're deeply grateful for your continued support and trust in Amravati Wears Market.</p>
            <p>Shop for festive wear, traditional outfits, and special gifts for your loved ones:</p>
            <center>
                <a href="https://awm27.shop" class="button">🛍️ Shop Festive Collection</a>
            </center>
            <p>May your Diwali be filled with countless moments of joy and celebration!</p>
            <p>Warm wishes,<br><strong>Amravati Wears Market Team</strong></p>
        </div>
        <div class="footer">
            <p>You're receiving this because you subscribed to our newsletter.</p>
            <p>To unsubscribe, contact us at support@awm27.shop</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        try:
            logger.info(f"Sending seasonal greetings to {len(email_list)} subscribers")
            success_count, failed_emails = send_bulk_email(
                subject=subject,
                message=plain_message,
                recipient_list=email_list,
                html_content=html_message
            )

            if failed_emails:
                self.message_user(
                    request,
                    f"⚠️ Sent to {success_count} subscriber(s). Failed: {len(failed_emails)}. Check logs for details.",
                    messages.WARNING
                )
                logger.warning(f"Failed emails: {failed_emails}")
            else:
                self.message_user(
                    request,
                    f"✅ Successfully sent seasonal greetings to {success_count} subscriber(s)! 🎉",
                    messages.SUCCESS
                )

            logger.info(f"Seasonal greetings sent by {request.user.name}: {success_count} successful, {len(failed_emails)} failed")

        except Exception as e:
            self.message_user(request, f"❌ Failed to send emails: {str(e)}", messages.ERROR)
            logger.error(f"Error sending seasonal greetings: {str(e)}", exc_info=True)

    send_seasonal_greetings.short_description = "🪔 Send Seasonal Greetings"

    def deactivate_subscribers(self, request, queryset):
        """Deactivate selected subscribers (unsubscribe them)"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"🚫 {count} subscriber(s) deactivated.",
            messages.SUCCESS
        )
        logger.info(f"Admin {request.user.name} deactivated {count} subscribers")

    deactivate_subscribers.short_description = "🚫 Deactivate Selected Subscribers"

    def activate_subscribers(self, request, queryset):
        """Activate selected subscribers"""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"✅ {count} subscriber(s) activated.",
            messages.SUCCESS
        )
        logger.info(f"Admin {request.user.name} activated {count} subscribers")

    activate_subscribers.short_description = "✅ Activate Selected Subscribers"