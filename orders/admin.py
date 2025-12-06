# orders/admin.py

from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'base_price', 'display_price', 'mrp', 'commission_rate',
                       'quantity', 'size', 'color', 'item_subtotal', 'commission_amount', 'seller_amount']
    can_delete = False

    fields = ['product_name', 'quantity', 'size', 'color', 'mrp', 'display_price', 'base_price',
              'commission_rate', 'item_subtotal', 'seller_amount', 'commission_amount']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'shop', 'total_amount', 'seller_earnings',
                    'commission_amount', 'order_status', 'coupon_code', 'created_at']
    list_filter = ['order_status', 'payment_status', 'created_at', 'shop']
    search_fields = ['order_number', 'customer__name', 'customer__phone', 'coupon_code']
    readonly_fields = ['order_number', 'subtotal', 'cod_fee', 'coupon_discount', 'total_amount',
                       'commission_amount', 'seller_payout_amount', 'seller_earnings', 'created_at',
                       'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at']

    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'customer', 'shop', 'order_status', 'payment_status')
        }),
        ('Delivery Details', {
            'fields': ('customer_name', 'customer_phone', 'delivery_address', 'city', 'pincode', 'landmark')
        }),
        ('Coupon Details', {
            'fields': ('coupon', 'coupon_code', 'coupon_discount'),
            'classes': ('collapse',),
            'description': 'Coupon discount is absorbed by the seller, reducing their earnings.'
        }),
        ('Pricing Breakdown', {
            'fields': ('subtotal', 'cod_fee', 'total_amount', 'commission_amount',
                       'seller_payout_amount', 'seller_earnings'),
            'description': (
                '• Customer pays: Total Amount (COD)\n'
                '• Seller Payout Amount: Base earnings (sum of base prices)\n'
                '• Seller Earnings: Actual amount seller receives (after coupon impact)\n'
                '• Platform Commission: Platform earns this\n'
                '• Formula: Seller Earnings = Total Amount - Commission - COD Fee'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at')
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing order
            return self.readonly_fields + ['customer', 'shop', 'coupon']
        return self.readonly_fields

    # ✅ Custom display for seller earnings with indicator
    def seller_earnings_display(self, obj):
        if obj.coupon_code:
            return f"₹{obj.seller_earnings:.2f} (Coupon: -{obj.coupon_discount:.2f})"
        return f"₹{obj.seller_earnings:.2f}"

    seller_earnings_display.short_description = 'Seller Earnings'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'size', 'color',
                    'mrp', 'display_price', 'base_price', 'item_subtotal',
                    'seller_amount', 'commission_amount']
    list_filter = ['order__order_status', 'created_at']
    search_fields = ['product_name', 'order__order_number']
    readonly_fields = ['item_subtotal', 'commission_amount', 'seller_amount', 'discount_percentage']

    fieldsets = (
        ('Order Info', {
            'fields': ('order', 'product', 'variant')
        }),
        ('Product Details', {
            'fields': ('product_name', 'size', 'color', 'quantity')
        }),
        ('Pricing', {
            'fields': ('mrp', 'display_price', 'base_price', 'commission_rate', 'discount_percentage'),
            'description': 'MRP > Display Price = Customer discount. Display - Base = Platform commission.'
        }),
        ('Calculated Amounts', {
            'fields': ('item_subtotal', 'seller_amount', 'commission_amount'),
            'description': (
                '• Item Subtotal: Display Price × Quantity (customer pays)\n'
                '• Seller Amount: Base Price × Quantity (seller receives for this item)\n'
                '• Commission Amount: Platform earns from this item'
            )
        }),
    )

    def discount_percentage(self, obj):
        """Display MRP discount percentage"""
        percentage = obj.get_discount_percentage()
        if percentage > 0:
            return f"{percentage}% OFF"
        return "No discount"

    discount_percentage.short_description = 'MRP Discount'
