from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from decimal import Decimal
from .models import Coupon, CouponUsage
from .serializers import (
    CouponSerializer, CouponCreateSerializer, CouponUpdateSerializer,
    CouponValidateSerializer, CouponUsageSerializer
)
from products.models import Product


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_coupon(request):
    """
    Create new coupon (seller only)
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can create coupons'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        if not shop.is_approved:
            return Response(
                {'error': 'Your shop is not approved yet'},
                status=status.HTTP_403_FORBIDDEN
            )
    except:
        return Response(
            {'error': 'You need to register a shop first'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = CouponCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        coupon = serializer.save()
        return Response({
            'message': 'Coupon created successfully',
            'coupon': CouponSerializer(coupon).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_coupons(request):
    """
    List seller's coupons
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can access this'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        coupons = Coupon.objects.filter(shop=shop).order_by('-created_at')

        # Filter by active status
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            coupons = coupons.filter(is_active=is_active.lower() == 'true')

        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)
    except:
        return Response(
            {'error': 'Shop not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_coupon_detail(request, coupon_id):
    """
    Get coupon details (seller only)
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can access this'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        coupon = Coupon.objects.get(id=coupon_id, shop=shop)
        serializer = CouponSerializer(coupon)
        return Response(serializer.data)
    except Coupon.DoesNotExist:
        return Response(
            {'error': 'Coupon not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_coupon(request, coupon_id):
    """
    Update coupon (seller only)
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can update coupons'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        coupon = Coupon.objects.get(id=coupon_id, shop=shop)

        serializer = CouponUpdateSerializer(coupon, data=request.data, partial=True)
        if serializer.is_valid():
            coupon = serializer.save()
            return Response({
                'message': 'Coupon updated successfully',
                'coupon': CouponSerializer(coupon).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Coupon.DoesNotExist:
        return Response(
            {'error': 'Coupon not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_coupon(request, coupon_id):
    """
    Delete coupon (seller only)
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can delete coupons'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        coupon = Coupon.objects.get(id=coupon_id, shop=shop)
        coupon.delete()
        return Response({'message': 'Coupon deleted successfully'})
    except Coupon.DoesNotExist:
        return Response(
            {'error': 'Coupon not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_coupon(request):
    """
    Validate and calculate coupon discount for cart

    Request Body:
    {
        "code": "SAVE20",
        "cart_items": [
            {"product_id": 1, "quantity": 2, "price": 1000}
        ]
    }
    """
    serializer = CouponValidateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    code = serializer.validated_data['code'].upper()
    cart_items = serializer.validated_data['cart_items']

    try:
        # Get coupon
        coupon = Coupon.objects.get(code=code)

        # Check if coupon is valid
        is_valid, message = coupon.is_valid()
        if not is_valid:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user can use this coupon
        can_use, message = coupon.can_user_use(request.user)
        if not can_use:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        # Get product IDs from cart
        product_ids = [item['product_id'] for item in cart_items]
        products = Product.objects.filter(id__in=product_ids)

        # Check if all products are from coupon's shop
        for product in products:
            if product.shop_id != coupon.shop_id:
                return Response(
                    {'error': f'Coupon is only valid for products from {coupon.shop.shop_name}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Calculate applicable cart value
        applicable_total = Decimal('0')

        for item in cart_items:
            product = products.get(id=item['product_id'])
            quantity = Decimal(str(item['quantity']))
            price = Decimal(str(item['price']))
            item_total = price * quantity

            # Check if product is applicable for coupon
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
                applicable_total += item_total

        # Check minimum order value
        if applicable_total < coupon.min_order_value:
            return Response(
                {'error': f'Minimum order value of ₹{coupon.min_order_value} required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate discount
        if coupon.discount_type == 'percentage':
            discount_amount = (applicable_total * coupon.discount_value) / Decimal('100')
        else:  # fixed
            discount_amount = coupon.discount_value
            # Cap discount at applicable total
            if discount_amount > applicable_total:
                discount_amount = applicable_total

        return Response({
            'valid': True,
            'coupon': {
                'id': coupon.id,
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value),
                'discount_display': coupon.get_discount_display()
            },
            'applicable_total': float(applicable_total),
            'discount_amount': float(discount_amount),
            'message': f'Coupon applied! You saved ₹{discount_amount}'
        })

    except Coupon.DoesNotExist:
        return Response(
            {'error': 'Invalid coupon code'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to validate coupon'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_coupon_usages(request, coupon_id):
    """
    Get usage history for a coupon (seller only)
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can access this'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        coupon = Coupon.objects.get(id=coupon_id, shop=shop)
        usages = CouponUsage.objects.filter(coupon=coupon).order_by('-used_at')

        serializer = CouponUsageSerializer(usages, many=True)
        return Response({
            'coupon': CouponSerializer(coupon).data,
            'usages': serializer.data
        })
    except Coupon.DoesNotExist:
        return Response(
            {'error': 'Coupon not found'},
            status=status.HTTP_404_NOT_FOUND
        )