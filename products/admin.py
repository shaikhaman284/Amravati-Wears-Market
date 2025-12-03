from django.contrib import admin
from .models import Product, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['size', 'color', 'stock_quantity', 'sku', 'is_active']
    readonly_fields = ['sku']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'category', 'base_price', 'display_price', 'mrp',
                    'get_discount_display', 'commission_rate', 'stock_quantity', 'is_active']
    list_filter = ['is_active', 'category', 'shop', 'created_at']
    search_fields = ['name', 'shop__shop_name']
    readonly_fields = ['display_price', 'slug', 'average_rating', 'review_count',
                       'created_at', 'updated_at', 'get_discount_display']
    inlines = [ProductVariantInline]

    fieldsets = (
        ('Basic Info', {'fields': ('shop', 'category', 'name', 'description', 'slug')}),
        ('Pricing (IMPORTANT)', {
            'fields': ('base_price', 'commission_rate', 'display_price', 'mrp', 'get_discount_display'),
            'description': 'Base Price = What seller receives. Display Price = What customer pays (auto-calculated). MRP = Show discount badge.'
        }),
        ('Inventory', {'fields': ('stock_quantity', 'sizes', 'colors')}),
        ('Images', {'fields': ('image1', 'image2', 'image3', 'image4', 'image5')}),
        ('Ratings', {'fields': ('average_rating', 'review_count')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def get_discount_display(self, obj):
        """Display discount percentage in admin"""
        discount = obj.get_discount_percentage()
        if discount > 0:
            return f"{discount}% OFF"
        return "No discount"
    get_discount_display.short_description = 'Discount'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'color', 'stock_quantity', 'sku', 'is_active']
    list_filter = ['is_active', 'product__shop']
    search_fields = ['product__name', 'sku', 'size', 'color']
    readonly_fields = ['sku', 'created_at', 'updated_at']