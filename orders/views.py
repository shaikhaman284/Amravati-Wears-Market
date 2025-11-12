from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from .models import Order, OrderItem
from products.models import Product
from .serializers import (
    OrderCreateSerializer, OrderListSerializer,
    OrderDetailSerializer, OrderStatusUpdateSerializer
)
from .utils import calculate_order_totals, validate_cart_items


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Create new order with COD fee logic

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
        "landmark": "Near Temple"
    }
    """
    serializer = OrderCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    cart_items = serializer.validated_data['cart_items']

    try:
        # Validate cart items
        validate_cart_items(cart_items)

        # Calculate totals with COD fee logic
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
                total_amount=order_totals['total_amount'],
                commission_amount=order_totals['commission_amount'],
                seller_payout_amount=order_totals['seller_payout_amount']
            )

            # Create order items
            for item_data in order_totals['items']:
                OrderItem.objects.create(
                    order=order,
                    product_id=item_data['product_id'],
                    product_name=item_data['product_name'],
                    base_price=item_data['base_price'],
                    display_price=item_data['display_price'],
                    commission_rate=item_data['commission_rate'],
                    quantity=item_data['quantity'],
                    size=item_data['size'],
                    color=item_data['color']
                )

                # Reduce stock
                product = Product.objects.get(id=item_data['product_id'])
                product.stock_quantity -= item_data['quantity']
                product.save()

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
    Update order status (seller only)
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

            # Restore stock
            for item in order.items.all():
                if item.product:
                    item.product.stock_quantity += item.quantity
                    item.product.save()

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