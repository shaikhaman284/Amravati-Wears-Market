from rest_framework import serializers
from .models import Coupon, CouponUsage
from django.utils import timezone


class CouponSerializer(serializers.ModelSerializer):
    """For listing coupons (seller view)"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    product_name = serializers.CharField(source='product.name', read_only=True, allow_null=True)
    discount_display = serializers.CharField(source='get_discount_display', read_only=True)
    is_valid_now = serializers.SerializerMethodField()
    usage_stats = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'shop_name', 'discount_type', 'discount_value',
            'discount_display', 'applicability', 'category', 'category_name',
            'product', 'product_name', 'min_order_value', 'max_uses',
            'max_uses_per_customer', 'valid_from', 'valid_to', 'is_active',
            'times_used', 'is_valid_now', 'usage_stats', 'created_at'
        ]

    def get_is_valid_now(self, obj):
        """Check if coupon is currently valid"""
        is_valid, message = obj.is_valid()
        return {'valid': is_valid, 'message': message}

    def get_usage_stats(self, obj):
        """Get usage statistics"""
        return {
            'times_used': obj.times_used,
            'max_uses': obj.max_uses if obj.max_uses else 'Unlimited',
            'remaining': (obj.max_uses - obj.times_used) if obj.max_uses else 'Unlimited'
        }


class CouponCreateSerializer(serializers.ModelSerializer):
    """For creating coupons"""

    class Meta:
        model = Coupon
        fields = [
            'code', 'discount_type', 'discount_value', 'applicability',
            'category', 'product', 'min_order_value', 'max_uses',
            'max_uses_per_customer', 'valid_from', 'valid_to', 'is_active'
        ]

    def validate_code(self, value):
        """Validate coupon code"""
        value = value.upper().strip()

        if len(value) < 3 or len(value) > 20:
            raise serializers.ValidationError("Coupon code must be between 3 and 20 characters")

        if not value.isalnum():
            raise serializers.ValidationError("Coupon code must contain only letters and numbers")

        return value

    def validate_discount_value(self, value):
        """Validate discount value"""
        if value <= 0:
            raise serializers.ValidationError("Discount value must be greater than 0")

        return value

    def validate(self, data):
        """Cross-field validation"""
        # Validate percentage discount
        if data['discount_type'] == 'percentage' and data['discount_value'] > 100:
            raise serializers.ValidationError({
                'discount_value': 'Percentage discount cannot exceed 100%'
            })

        # Validate applicability constraints
        if data['applicability'] == 'category' and not data.get('category'):
            raise serializers.ValidationError({
                'category': 'Category is required when applicability is "category"'
            })

        if data['applicability'] == 'product' and not data.get('product'):
            raise serializers.ValidationError({
                'product': 'Product is required when applicability is "product"'
            })

        # Validate dates
        if data['valid_from'] >= data['valid_to']:
            raise serializers.ValidationError({
                'valid_to': 'End date must be after start date'
            })

        if data['valid_to'] < timezone.now():
            raise serializers.ValidationError({
                'valid_to': 'End date cannot be in the past'
            })

        return data

    def create(self, validated_data):
        """Create coupon with shop from context"""
        request = self.context.get('request')
        validated_data['shop'] = request.user.shop
        return super().create(validated_data)


class CouponUpdateSerializer(serializers.ModelSerializer):
    """For updating coupons"""

    class Meta:
        model = Coupon
        fields = [
            'discount_type', 'discount_value', 'applicability',
            'category', 'product', 'min_order_value', 'max_uses',
            'max_uses_per_customer', 'valid_from', 'valid_to', 'is_active'
        ]
        # Code cannot be changed after creation

    def validate_discount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Discount value must be greater than 0")
        return value

    def validate(self, data):
        """Cross-field validation"""
        discount_type = data.get('discount_type', self.instance.discount_type)
        discount_value = data.get('discount_value', self.instance.discount_value)

        if discount_type == 'percentage' and discount_value > 100:
            raise serializers.ValidationError({
                'discount_value': 'Percentage discount cannot exceed 100%'
            })

        applicability = data.get('applicability', self.instance.applicability)

        if applicability == 'category' and not data.get('category', self.instance.category):
            raise serializers.ValidationError({
                'category': 'Category is required when applicability is "category"'
            })

        if applicability == 'product' and not data.get('product', self.instance.product):
            raise serializers.ValidationError({
                'product': 'Product is required when applicability is "product"'
            })

        valid_from = data.get('valid_from', self.instance.valid_from)
        valid_to = data.get('valid_to', self.instance.valid_to)

        if valid_from >= valid_to:
            raise serializers.ValidationError({
                'valid_to': 'End date must be after start date'
            })

        return data


class CouponValidateSerializer(serializers.Serializer):
    """For validating coupon codes"""
    code = serializers.CharField(max_length=20)
    cart_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of {product_id, quantity, price}"
    )


class CouponUsageSerializer(serializers.ModelSerializer):
    """For tracking coupon usage"""
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True, allow_null=True)

    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon_code', 'customer_name', 'order_number',
            'discount_amount', 'used_at'
        ]