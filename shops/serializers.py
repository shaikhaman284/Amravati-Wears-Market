from rest_framework import serializers
from .models import Shop, Category


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'image', 'subcategories', 'is_active']

    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.filter(is_active=True), many=True).data
        return []


class ShopSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone', read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            'id', 'shop_name', 'address', 'city', 'pincode', 'contact_number',
            'shop_image', 'commission_rate', 'is_approved', 'approval_status',
            'owner_name', 'owner_phone', 'product_count', 'created_at'
        ]
        read_only_fields = ['is_approved', 'approval_status', 'commission_rate', 'created_at']

    def get_product_count(self, obj):
        return obj.get_product_count()


class ShopRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['shop_name', 'address', 'city', 'pincode', 'contact_number', 'shop_image']

    def validate_pincode(self, value):
        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("Pincode must be 6 digits")
        return value

    def validate_contact_number(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Invalid contact number")
        return value


class ShopDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    product_count = serializers.SerializerMethodField()
    recent_products = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            'id', 'shop_name', 'address', 'city', 'pincode', 'contact_number',
            'shop_image', 'commission_rate', 'owner_name', 'product_count',
            'recent_products', 'created_at'
        ]

    def get_product_count(self, obj):
        return obj.get_product_count()

    def get_recent_products(self, obj):
        from products.serializers import ProductListSerializer
        products = obj.products.filter(is_active=True).order_by('-created_at')[:6]
        return ProductListSerializer(products, many=True).data