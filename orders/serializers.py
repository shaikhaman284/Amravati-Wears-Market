from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'base_price', 'display_price',
            'commission_rate', 'quantity', 'size', 'color',
            'item_subtotal', 'commission_amount', 'seller_amount'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """For listing orders (both customer and seller)"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    customer_name = serializers.CharField(read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'shop_name', 'customer_name',
            'items_count', 'total_amount', 'order_status',
            'payment_status', 'created_at'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order details"""
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)
    shop_contact = serializers.CharField(source='shop.contact_number', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'shop_name', 'shop_contact',
            'customer_name', 'customer_phone', 'delivery_address',
            'city', 'pincode', 'landmark',
            'subtotal', 'cod_fee', 'total_amount',
            'commission_amount', 'seller_payout_amount',
            'order_status', 'payment_status',
            'items', 'created_at', 'confirmed_at', 'shipped_at',
            'delivered_at', 'cancelled_at'
        ]


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