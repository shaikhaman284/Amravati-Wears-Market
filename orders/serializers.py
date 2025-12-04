# orders/serializers.py - COMPLETE FILE

from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_image = serializers.SerializerMethodField()
    variant_info = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'variant',
            'product_name',
            'product_image',
            'base_price',
            'display_price',
            'mrp',
            'discount_percentage',
            'commission_rate',
            'quantity',
            'size',
            'color',
            'item_subtotal',
            'commission_amount',
            'seller_amount',
            'variant_info'
        ]

    def get_product_image(self, obj):
        """Get the main image of the product"""
        if obj.product and obj.product.image1:
            return obj.product.image1
        return None

    def get_variant_info(self, obj):
        """Get variant display info"""
        if obj.variant:
            return {
                'id': obj.variant.id,
                'sku': obj.variant.sku,
                'size': obj.variant.size,
                'color': obj.variant.color
            }
        return None

    def get_discount_percentage(self, obj):
        """Calculate discount percentage from MRP"""
        return obj.get_discount_percentage()


class OrderListSerializer(serializers.ModelSerializer):
    """For listing orders (both customer and seller)"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    customer_name = serializers.CharField(read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'shop_name', 'customer_name',
            'items_count', 'subtotal', 'coupon_discount', 'total_amount',
            'order_status', 'payment_status', 'created_at',
            'seller_payout_amount', 'commission_amount'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order details"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    shop_contact = serializers.CharField(source='shop.contact_number', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    net_cash_to_keep = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'shop_name', 'shop_contact',
            'customer_name', 'customer_phone', 'delivery_address',
            'city', 'pincode', 'landmark',
            'subtotal', 'cod_fee', 'coupon_code', 'coupon_discount', 'total_amount',
            'commission_amount', 'seller_payout_amount',
            'net_cash_to_keep',
            'order_status', 'payment_status',
            'items', 'created_at', 'confirmed_at', 'shipped_at',
            'delivered_at', 'cancelled_at',
            'cancellation_reason'
        ]

    def get_net_cash_to_keep(self, obj):
        """Calculate net cash seller keeps after collecting COD"""
        return float(obj.total_amount - obj.commission_amount - obj.cod_fee)


class OrderCreateSerializer(serializers.Serializer):
    """For creating new orders"""
    cart_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of {product_id, quantity, size, color}"
    )
    customer_name = serializers.CharField(max_length=255)
    customer_phone = serializers.CharField(max_length=15)
    delivery_address = serializers.CharField()
    city = serializers.CharField(max_length=100, default='Amravati')
    pincode = serializers.CharField(max_length=6)
    landmark = serializers.CharField(max_length=255, required=False, allow_blank=True)
    coupon_code = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    def validate_pincode(self, value):
        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("Pincode must be 6 digits")
        return value

    def validate_customer_phone(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    """For updating order status"""
    order_status = serializers.ChoiceField(
        choices=['placed', 'confirmed', 'shipped', 'delivered', 'cancelled']
    )
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)