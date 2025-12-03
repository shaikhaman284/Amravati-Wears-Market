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
    discount_percentage = serializers.SerializerMethodField()  # NEW

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'display_price', 'mrp', 'discount_percentage',  # Added mrp & discount
            'stock_quantity', 'main_image', 'shop_name', 'category_name',
            'average_rating', 'review_count', 'is_active'
        ]

    def get_main_image(self, obj):
        return obj.image1 if obj.image1 else None

    def get_discount_percentage(self, obj):
        """Calculate real discount from MRP"""
        return obj.get_discount_percentage()


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full product details (customer view)"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    shop_id = serializers.IntegerField(source='shop.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True, read_only=True)
    discount_percentage = serializers.SerializerMethodField()  # NEW

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'display_price', 'mrp',  # Added mrp
            'discount_percentage', 'stock_quantity', 'sizes', 'colors',  # Added discount
            'images', 'shop_name', 'shop_id', 'category_name', 'average_rating',
            'review_count', 'is_active', 'created_at', 'variants'
        ]

    def get_images(self, obj):
        images = []
        for i in range(1, 6):
            img = getattr(obj, f'image{i}')
            if img:
                images.append(img)
        return images

    def get_discount_percentage(self, obj):
        """Calculate real discount from MRP"""
        return obj.get_discount_percentage()


class ProductCreateSerializer(serializers.ModelSerializer):
    """For sellers creating products - CRITICAL PRICING LOGIC"""
    variants = ProductVariantCreateSerializer(many=True, required=False)
    mrp = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)  # NEW

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'base_price', 'mrp',  # Added mrp
            'stock_quantity', 'sizes', 'colors', 'image1', 'image2',
            'image3', 'image4', 'image5', 'variants'
        ]

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Base price must be greater than 0")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative")
        return value

    def validate(self, data):
        """Validate MRP is higher than display price for discount"""
        mrp = data.get('mrp')
        base_price = data.get('base_price')

        if mrp and base_price:
            # We need to calculate display_price to validate
            # Get commission rate from context (will be set during creation)
            request = self.context.get('request')
            if request and hasattr(request.user, 'shop'):
                from decimal import Decimal
                commission_rate = request.user.shop.commission_rate
                display_price = base_price * (1 + commission_rate / Decimal('100'))

                if mrp <= display_price:
                    raise serializers.ValidationError({
                        'mrp': f'MRP (₹{mrp}) should be higher than customer price (₹{display_price:.2f}) to show discount'
                    })

        return data

    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])

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
    mrp = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)  # NEW

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'base_price', 'mrp',  # Added mrp
            'stock_quantity', 'sizes', 'colors', 'image1', 'image2',
            'image3', 'image4', 'image5', 'is_active'
        ]

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Base price must be greater than 0")
        return value

    def validate(self, data):
        """Validate MRP is higher than display price"""
        mrp = data.get('mrp')
        base_price = data.get('base_price', self.instance.base_price)
        commission_rate = self.instance.commission_rate

        if mrp:
            from decimal import Decimal
            display_price = base_price * (1 + commission_rate / Decimal('100'))

            if mrp <= display_price:
                raise serializers.ValidationError({
                    'mrp': f'MRP (₹{mrp}) should be higher than customer price (₹{display_price:.2f}) to show discount'
                })

        return data

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
    variants = ProductVariantSerializer(many=True, read_only=True)
    discount_percentage = serializers.SerializerMethodField()  # NEW

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'display_price', 'mrp',  # Added mrp
            'discount_percentage', 'commission_rate', 'commission_amount',  # Added discount
            'stock_quantity', 'category_name', 'average_rating', 'review_count',
            'is_active', 'created_at', 'description', 'sizes', 'colors',
            'images', 'category', 'variants'
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

    def get_discount_percentage(self, obj):
        """Calculate real discount from MRP"""
        return obj.get_discount_percentage()