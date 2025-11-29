from rest_framework import serializers
from .models import Product, ProductVariant
from shops.models import Category


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariant"""

    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'stock_quantity', 'sku', 'is_active']
        read_only_fields = ['id', 'sku']


class ProductVariantCreateSerializer(serializers.Serializer):
    """Serializer for creating variants"""
    size = serializers.CharField(max_length=50, allow_blank=True, required=False, allow_null=True)
    color = serializers.CharField(max_length=50, allow_blank=True, required=False, allow_null=True)
    stock_quantity = serializers.IntegerField(min_value=0)


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
    variants = ProductVariantSerializer(many=True, read_only=True)  # NEW

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'display_price',
            'stock_quantity', 'sizes', 'colors', 'images',
            'shop_name', 'shop_id', 'category_name', 'average_rating',
            'review_count', 'is_active', 'created_at', 'variants'  # Added variants
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
    variants = ProductVariantCreateSerializer(many=True, required=False)  # NEW

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'base_price', 'stock_quantity',
            'sizes', 'colors', 'image1', 'image2', 'image3', 'image4', 'image5',
            'variants'  # Added
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
        variants_data = validated_data.pop('variants', [])  # NEW

        # Get shop from context (current user's shop)
        request = self.context.get('request')
        shop = request.user.shop

        # Set shop and commission rate
        validated_data['shop'] = shop
        validated_data['commission_rate'] = shop.commission_rate

        # Product model will auto-calculate display_price in save()
        product = Product.objects.create(**validated_data)

        # Create variants if provided
        if variants_data:
            for variant_data in variants_data:
                ProductVariant.objects.create(product=product, **variant_data)
            # Update total stock after creating variants
            product.update_total_stock()

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
    """For sellers viewing their own products - shows both prices"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    commission_amount = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True, read_only=True)  # NEW

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'display_price', 'commission_rate',
            'commission_amount', 'stock_quantity', 'category_name', 'average_rating',
            'review_count', 'is_active', 'created_at',
            'description', 'sizes', 'colors', 'images', 'category', 'variants'  # Added variants
        ]

    def get_commission_amount(self, obj):
        return float(obj.get_commission_amount())

    def get_images(self, obj):
        """Collect all product images"""
        images = []
        for i in range(1, 6):
            img = getattr(obj, f'image{i}')
            if img:
                images.append(img)
        return images