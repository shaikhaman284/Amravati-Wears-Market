# orders/views.py - COMPLETE FILE WITH MRP SUPPORT

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Order, OrderItem
from products.models import Product, ProductVariant
from coupons.models import Coupon, CouponUsage
from .serializers import (
    OrderCreateSerializer, OrderListSerializer,
    OrderDetailSerializer, OrderStatusUpdateSerializer
)
from .utils import calculate_order_totals, validate_cart_items


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Create new order with COD fee logic, variant stock management, coupon support, and MRP tracking

    Request Body:
    {
        "cart_items": [
            {"product_id": 1, "quantity": 2, "size": "M", "color": "Blue"},
            {"product_id": 2, "quantity": 1, "size": "L", "color": "White"}
        ],
        "customer_name": "John Doe",
        "customer_phone": "9876543210",
        "delivery_address": "123 Street, Colony",
        "city": "Amravati",
        "pincode": "444601",
        "landmark": "Near Temple",
        "coupon_code": "SAVE20"  // Optional
    }
    """
    serializer = OrderCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    cart_items = serializer.validated_data['cart_items']
    coupon_code = serializer.validated_data.get('coupon_code', '').strip().upper()

    try:
        # Validate cart items
        validate_cart_items(cart_items)

        # Calculate totals with COD fee logic and variant validation (includes MRP)
        order_totals = calculate_order_totals(cart_items)

        # Check if all products are from same shop
        product_ids = [item['product_id'] for item in cart_items]
        products = Product.objects.filter(id__in=product_ids)
        shops = set(p.shop_id for p in products)

        if len(shops) > 1:
            return Response(
                {'error': 'All products must be from the same shop'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shop = products.first().shop

        # Validate and calculate coupon discount
        coupon = None
        coupon_discount = Decimal('0')

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, shop=shop)

                # Check if coupon is valid
                is_valid, message = coupon.is_valid()
                if not is_valid:
                    return Response({'error': f'Coupon error: {message}'}, status=status.HTTP_400_BAD_REQUEST)

                # Check if user can use this coupon
                can_use, message = coupon.can_user_use(request.user)
                if not can_use:
                    return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

                # Calculate applicable cart value for coupon
                applicable_total = Decimal('0')

                for item_data in order_totals['items']:
                    product = Product.objects.get(id=item_data['product_id'])

                    is_applicable = False
                    if coupon.applicability == 'all':
                        is_applicable = True
                    elif coupon.applicability == 'category' and coupon.category:
                        if product.category_id == coupon.category_id:
                            is_applicable = True
                    elif coupon.applicability == 'product' and coupon.product:
                        if product.id == coupon.product_id:
                            is_applicable = True

                    if is_applicable:
                        applicable_total += item_data['item_subtotal']

                # Check minimum order value
                if applicable_total < coupon.min_order_value:
                    return Response(
                        {'error': f'Minimum order value of ₹{coupon.min_order_value} required for this coupon'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Calculate discount
                if coupon.discount_type == 'percentage':
                    coupon_discount = (applicable_total * coupon.discount_value) / Decimal('100')
                else:  # fixed
                    coupon_discount = coupon.discount_value
                    # Cap discount at applicable total
                    if coupon_discount > applicable_total:
                        coupon_discount = applicable_total

            except Coupon.DoesNotExist:
                return Response({'error': 'Invalid coupon code'}, status=status.HTTP_400_BAD_REQUEST)

        # Create order in transaction
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                customer=request.user,
                shop=shop,
                customer_name=serializer.validated_data['customer_name'],
                customer_phone=serializer.validated_data['customer_phone'],
                delivery_address=serializer.validated_data['delivery_address'],
                city=serializer.validated_data['city'],
                pincode=serializer.validated_data['pincode'],
                landmark=serializer.validated_data.get('landmark', ''),
                subtotal=order_totals['subtotal'],
                cod_fee=order_totals['cod_fee'],
                coupon=coupon,
                coupon_code=coupon_code if coupon else None,
                coupon_discount=coupon_discount,
                total_amount=order_totals['total_amount'] - coupon_discount,
                commission_amount=order_totals['commission_amount'],
                seller_payout_amount=order_totals['seller_payout_amount']
            )

            # Create order items and reduce stock (WITH MRP)
            for item_data in order_totals['items']:
                OrderItem.objects.create(
                    order=order,
                    product_id=item_data['product_id'],
                    variant_id=item_data.get('variant_id'),
                    product_name=item_data['product_name'],
                    base_price=item_data['base_price'],
                    display_price=item_data['display_price'],
                    mrp=item_data.get('mrp'),  # ADDED: Capture MRP at time of order
                    commission_rate=item_data['commission_rate'],
                    quantity=item_data['quantity'],
                    size=item_data['size'],
                    color=item_data['color']
                )

                # Reduce stock from variant or product
                if item_data.get('variant_id'):
                    variant = ProductVariant.objects.get(id=item_data['variant_id'])
                    variant.stock_quantity -= item_data['quantity']
                    variant.save()  # This will trigger product.update_total_stock()
                else:
                    product = Product.objects.get(id=item_data['product_id'])
                    product.stock_quantity -= item_data['quantity']
                    product.save()

            # Record coupon usage and increment usage count
            if coupon:
                CouponUsage.objects.create(
                    coupon=coupon,
                    customer=request.user,
                    order=order,
                    discount_amount=coupon_discount
                )
                coupon.times_used += 1
                coupon.save()

        return Response({
            'message': 'Order placed successfully',
            'order': OrderDetailSerializer(order).data
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Failed to create order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_orders(request):
    """
    Get customer's orders
    """
    if request.user.user_type == 'seller':
        return Response(
            {'error': 'Use seller orders endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    orders = Order.objects.filter(customer=request.user).order_by('-created_at')

    # Filter by status
    order_status = request.query_params.get('status')
    if order_status:
        orders = orders.filter(order_status=order_status)

    serializer = OrderListSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_detail(request, order_number):
    """
    Get order details by order number
    """
    try:
        if request.user.user_type == 'customer':
            order = Order.objects.get(order_number=order_number, customer=request.user)
        elif request.user.user_type == 'seller':
            order = Order.objects.get(order_number=order_number, shop__owner=request.user)
        else:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_seller_orders(request):
    """
    Get seller's shop orders
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can access this'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        orders = Order.objects.filter(shop=shop).order_by('-created_at')

        # Filter by status
        order_status = request.query_params.get('status')
        if order_status:
            orders = orders.filter(order_status=order_status)

        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
    except:
        return Response({'error': 'Shop not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_number):
    """
    Update order status (seller only) with variant stock restoration and coupon handling
    Valid transitions:
    - placed → confirmed
    - confirmed → shipped
    - shipped → delivered
    - Any → cancelled (with restrictions)
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can update order status'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = OrderStatusUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    new_status = serializer.validated_data['order_status']

    try:
        shop = request.user.shop
        order = Order.objects.get(order_number=order_number, shop=shop)

        # Status transition validation
        current_status = order.order_status

        valid_transitions = {
            'placed': ['confirmed', 'cancelled'],
            'confirmed': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],  # Cannot change once delivered
            'cancelled': []  # Cannot change once cancelled
        }

        if new_status not in valid_transitions.get(current_status, []):
            return Response(
                {'error': f'Cannot change status from {current_status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status and timestamp
        order.order_status = new_status

        if new_status == 'confirmed':
            order.confirmed_at = timezone.now()
        elif new_status == 'shipped':
            order.shipped_at = timezone.now()
        elif new_status == 'delivered':
            order.delivered_at = timezone.now()
            order.payment_status = 'paid'  # Mark as paid on delivery
        elif new_status == 'cancelled':
            order.cancelled_at = timezone.now()

            # Store cancellation reason if provided
            cancellation_reason = request.data.get('reason')
            if cancellation_reason:
                order.cancellation_reason = cancellation_reason

            # Restore stock to variants or products
            for item in order.items.all():
                if item.variant:
                    item.variant.stock_quantity += item.quantity
                    item.variant.save()  # This will trigger product.update_total_stock()
                elif item.product:
                    item.product.stock_quantity += item.quantity
                    item.product.save()

            # Restore coupon usage count if cancelled
            if order.coupon:
                order.coupon.times_used -= 1
                order.coupon.save()

        order.save()

        return Response({
            'message': f'Order status updated to {new_status}',
            'order': OrderDetailSerializer(order).data
        })

    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_seller_dashboard(request):
    """
    Get seller dashboard stats
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can access this'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop

        # Get stats
        from django.db.models import Sum, Count
        from datetime import date

        total_products = Product.objects.filter(shop=shop, is_active=True).count()
        pending_orders = Order.objects.filter(shop=shop, order_status='placed').count()

        # Today's orders
        today_orders = Order.objects.filter(
            shop=shop,
            created_at__date=date.today()
        ).count()

        # Total earnings (delivered orders)
        total_earnings = Order.objects.filter(
            shop=shop,
            order_status='delivered'
        ).aggregate(total=Sum('seller_payout_amount'))['total'] or 0

        # Pending earnings (confirmed + shipped orders)
        pending_earnings = Order.objects.filter(
            shop=shop,
            order_status__in=['confirmed', 'shipped']
        ).aggregate(total=Sum('seller_payout_amount'))['total'] or 0

        # Recent orders
        recent_orders = Order.objects.filter(shop=shop).order_by('-created_at')[:5]

        return Response({
            'total_products': total_products,
            'pending_orders': pending_orders,
            'today_orders': today_orders,
            'total_earnings': float(total_earnings),
            'pending_earnings': float(pending_earnings),
            'recent_orders': OrderListSerializer(recent_orders, many=True).data
        })
    except:
        return Response({'error': 'Shop not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_customer_order(request, order_number):
    """
    Cancel order by customer (before shipping only) with variant stock restoration and coupon handling
    """
    if request.user.user_type != 'customer':
        return Response(
            {'error': 'Only customers can cancel their orders using this endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        # Get order belonging to this customer
        order = Order.objects.get(order_number=order_number, customer=request.user)

        # Check if order can be cancelled
        if order.order_status not in ['placed', 'confirmed']:
            return Response(
                {
                    'error': f'Cannot cancel order with status: {order.order_status}. Orders can only be cancelled before shipping.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update order status to cancelled
        order.order_status = 'cancelled'
        order.cancelled_at = timezone.now()

        # Restore stock for all items (variant or product)
        for item in order.items.all():
            if item.variant:
                item.variant.stock_quantity += item.quantity
                item.variant.save()  # This will trigger product.update_total_stock()
            elif item.product:
                item.product.stock_quantity += item.quantity
                item.product.save()

        # Restore coupon usage count if cancelled
        if order.coupon:
            order.coupon.times_used -= 1
            order.coupon.save()

        order.save()

        return Response({
            'message': 'Order cancelled successfully',
            'order': OrderDetailSerializer(order).data
        })

    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': 'Failed to cancel order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)