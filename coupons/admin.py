from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'shop', 'discount_display', 'applicability',
                    'valid_from', 'valid_to', 'times_used', 'is_active']
    list_filter = ['is_active', 'discount_type', 'applicability', 'shop', 'created_at']
    search_fields = ['code', 'shop__shop_name']
    readonly_fields = ['times_used', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('shop', 'code', 'is_active')
        }),
        ('Discount Details', {
            'fields': ('discount_type', 'discount_value')
        }),
        ('Applicability', {
            'fields': ('applicability', 'category', 'product'),
            'description': 'Choose what products this coupon applies to'
        }),
        ('Constraints', {
            'fields': ('min_order_value', 'max_uses', 'max_uses_per_customer')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Statistics', {
            'fields': ('times_used',),
            'description': 'Usage statistics'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def discount_display(self, obj):
        return obj.get_discount_display()
    discount_display.short_description = 'Discount'


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'customer', 'order', 'discount_amount', 'used_at']
    list_filter = ['coupon__shop', 'used_at']
    search_fields = ['coupon__code', 'customer__name', 'order__order_number']
    readonly_fields = ['coupon', 'customer', 'order', 'discount_amount', 'used_at']

    def has_add_permission(self, request):
        # Prevent manual creation of usage records
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent editing usage records
        return False