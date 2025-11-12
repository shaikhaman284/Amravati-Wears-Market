from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer', 'product', 'rating', 'is_verified_purchase', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['customer__name', 'product__name', 'review_text']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Review Info', {'fields': ('product', 'order', 'customer', 'rating', 'review_text')}),
        ('Status', {'fields': ('is_verified_purchase',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )