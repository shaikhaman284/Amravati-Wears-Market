from rest_framework import serializers
from .models import Product
from shops.models import Category

class ProductListSerializer(serializers.ModelSerializer):
    """For listing products (customer view)"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'display_price', 'stock_quantity',
            'main_image', 'shop_name', 'category_name', 'average_rating',
            'review_count', 'is_active'
        ]

    def get_main_image(self, obj):
        return obj.image1 if obj.image1 else None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full product details (customer view)"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    shop_id = serializers.IntegerField(source='shop.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'display_price',
            'stock_quantity', 'sizes', 'colors', 'images',
            'shop_name', 'shop_id', 'category_name', 'average_rating',
            'review_count', 'is_active', 'created_at'
        ]

    def get_images(self, obj):
        images = []
        for i in range(1, 6):
            img = getattr(obj, f'image{i}')
            if img:
                images.append(img)
        return images


class ProductCreateSerializer(serializers.ModelSerializer):
    """For sellers creating products - CRITICAL PRICING LOGIC"""

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'base_price', 'stock_quantity',
            'sizes', 'colors', 'image1', 'image2', 'image3', 'image4', 'image5'
        ]

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Base price must be greater than 0")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative")
        return value

    def create(self, validated_data):
        # Get shop from context (current user's shop)
        request = self.context.get('request')
        shop = request.user.shop

        # Set shop and commission rate
        validated_data['shop'] = shop
        validated_data['commission_rate'] = shop.commission_rate

        # Product model will auto-calculate display_price in save()
        product = Product.objects.create(**validated_data)
        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    """For sellers updating products"""

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'base_price', 'stock_quantity',
            'sizes', 'colors', 'image1', 'image2', 'image3', 'image4', 'image5', 'is_active'
        ]

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Base price must be greater than 0")
        return value

    def update(self, instance, validated_data):
        # If base_price changed, display_price will be recalculated in save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SellerProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    commission_amount = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    sizes = serializers.ListField(child=serializers.CharField(), required=False)
    colors = serializers.ListField(child=serializers.CharField(), required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',               # <-- Added description
            'base_price', 'commission_rate', 'display_price', 'commission_amount',
            'stock_quantity', 'sizes', 'colors',                # <-- Added sizes/colors
            'images', 'main_image',
            'category_name', 'category',                        # <-- Add category if needed
            'average_rating', 'review_count', 'is_active', 'created_at',
            'shop_name', 'shop_id',                             # <-- Add shop info if needed
        ]

    def get_images(self, obj):
        images = []
        for i in range(1, 6):
            img = getattr(obj, f'image{i}')
            if img:
                images.append(img)
        return images

    def get_main_image(self, obj):
        return obj.image1 if obj.image1 else ""

    def get_commission_amount(self, obj):
        return float(obj.get_commission_amount())

