from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'base_price', 'display_price', 'commission_rate',
                       'quantity', 'item_subtotal', 'commission_amount', 'seller_amount']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'shop', 'total_amount', 'seller_payout_amount',
                    'commission_amount', 'order_status', 'created_at']
    list_filter = ['order_status', 'payment_status', 'created_at', 'shop']
    search_fields = ['order_number', 'customer__name', 'customer__phone']
    readonly_fields = ['order_number', 'subtotal', 'cod_fee', 'total_amount',
                       'commission_amount', 'seller_payout_amount', 'created_at',
                       'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at']

    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'customer', 'shop', 'order_status', 'payment_status')}),
        ('Delivery Details', {'fields': ('customer_name', 'customer_phone', 'delivery_address',
                                         'city', 'pincode', 'landmark')}),
        ('Pricing Breakdown', {
            'fields': ('subtotal', 'cod_fee', 'total_amount', 'commission_amount', 'seller_payout_amount'),
            'description': 'Customer pays Total. Seller receives Payout. Platform earns Commission + COD Fee.'
        }),
        ('Timestamps', {'fields': ('created_at', 'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at')}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing order
            return self.readonly_fields + ['customer', 'shop']
        return self.readonly_fields


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'display_price', 'base_price',
                    'item_subtotal', 'seller_amount', 'commission_amount']
    list_filter = ['order__order_status', 'created_at']
    search_fields = ['product_name', 'order__order_number']
    readonly_fields = ['item_subtotal', 'commission_amount', 'seller_amount']