from django.contrib import admin
from .models import Category, Shop


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