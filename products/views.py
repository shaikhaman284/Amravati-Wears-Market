from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from decimal import Decimal
from .models import Product, ProductVariant
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateSerializer, ProductUpdateSerializer, SellerProductSerializer,
    ProductVariantSerializer
)


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([AllowAny])
def list_products(request):
    """
    List all products (public - for customers)
    Shows display_price (what customer pays)

    Query params:
    - category: filter by category ID
    - shop: filter by shop ID
    - search: search in name/description
    - min_price, max_price: price range filter (based on display_price)
    - sort: 'price_low', 'price_high', 'newest', 'popular'
    """
    products = Product.objects.filter(is_active=True, shop__is_approved=True)

    # Filter by category (include subcategories if parent category is selected)
    category_id = request.query_params.get('category')
    if category_id:
        from shops.models import Category
        try:
            category = Category.objects.get(id=category_id)
            # Get all subcategory IDs
            subcategory_ids = category.subcategories.values_list('id', flat=True)
            # Filter by selected category OR its subcategories
            if subcategory_ids:
                products = products.filter(Q(category_id=category_id) | Q(category_id__in=subcategory_ids))
            else:
                products = products.filter(category_id=category_id)
        except Category.DoesNotExist:
            products = products.filter(category_id=category_id)

    # Filter by shop
    shop_id = request.query_params.get('shop')
    if shop_id:
        products = products.filter(shop_id=shop_id)

    # Search
    search = request.query_params.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # Price range filter (based on display_price - what customer pays)
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')
    if min_price:
        products = products.filter(display_price__gte=Decimal(min_price))
    if max_price:
        products = products.filter(display_price__lte=Decimal(max_price))

    # Sorting
    sort = request.query_params.get('sort', 'newest')
    if sort == 'price_low':
        products = products.order_by('display_price')
    elif sort == 'price_high':
        products = products.order_by('-display_price')
    elif sort == 'popular':
        products = products.order_by('-review_count', '-average_rating')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = ProductPagination()
    paginated_products = paginator.paginate_queryset(products, request)

    serializer = ProductListSerializer(paginated_products, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_detail(request, product_id):
    """
    Get product details (public)
    Shows display_price (what customer pays)
    """
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product(request):
    """
    Create new product (seller only)
    Seller enters base_price, system calculates display_price
    """
    # Check if user is seller and has approved shop
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can create products'},
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

    serializer = ProductCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        product = serializer.save()

        # Return with pricing breakdown for seller
        return Response({
            'message': 'Product created successfully',
            'product': SellerProductSerializer(product).data,
            'pricing_info': {
                'base_price': float(product.base_price),
                'commission_rate': float(product.commission_rate),
                'commission_amount': float(product.get_commission_amount()),
                'display_price': float(product.display_price),
                'note': 'You will receive base_price. Customer pays display_price.'
            }
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_products(request):
    """
    List seller's own products
    Shows both base_price (what they receive) and display_price (what customer pays)
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can access this'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        products = Product.objects.filter(shop=shop).order_by('-created_at')

        # Filter by active status
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            products = products.filter(is_active=is_active.lower() == 'true')

        serializer = SellerProductSerializer(products, many=True)
        return Response(serializer.data)
    except:
        return Response(
            {'error': 'Shop not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_product_detail(request, product_id):
    """
    Get seller's product detail
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can access this'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        product = Product.objects.get(id=product_id, shop=shop)
        serializer = SellerProductSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_product(request, product_id):
    """
    Update product (seller only)
    If base_price changes, display_price is recalculated
    Supports creating new variants via new_variants field
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can update products'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        product = Product.objects.get(id=product_id, shop=shop)

        # Use transaction to ensure atomicity when creating variants
        with transaction.atomic():
            serializer = ProductUpdateSerializer(
                product,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                product = serializer.save()
                return Response({
                    'message': 'Product updated successfully',
                    'product': SellerProductSerializer(product).data
                })

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product(request, product_id):
    """
    Delete product (soft delete - set is_active=False)
    """
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can delete products'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        shop = request.user.shop
        product = Product.objects.get(id=product_id, shop=shop)
        product.is_active = False
        product.save()
        return Response({'message': 'Product deleted successfully'})
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# NEW VARIANT ENDPOINTS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_product_variants(request, product_id):
    """Get all variants for a product"""
    try:
        if request.user.user_type == 'seller':
            product = Product.objects.get(id=product_id, shop__owner=request.user)
        else:
            product = Product.objects.get(id=product_id, is_active=True)

        variants = product.variants.filter(is_active=True)
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_variant_stock(request, variant_id):
    """Update variant stock (seller only)"""
    if request.user.user_type != 'seller':
        return Response({'error': 'Only sellers can update stock'}, status=status.HTTP_403_FORBIDDEN)

    try:
        variant = ProductVariant.objects.get(id=variant_id, product__shop__owner=request.user)
        stock_quantity = request.data.get('stock_quantity')

        if stock_quantity is None or int(stock_quantity) < 0:
            return Response({'error': 'Invalid stock quantity'}, status=status.HTTP_400_BAD_REQUEST)

        variant.stock_quantity = int(stock_quantity)
        variant.save()  # This will trigger product.update_total_stock()

        return Response({
            'message': 'Stock updated successfully',
            'variant': ProductVariantSerializer(variant).data
        })
    except ProductVariant.DoesNotExist:
        return Response({'error': 'Variant not found'}, status=status.HTTP_404_NOT_FOUND)
