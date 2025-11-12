from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Shop, Category
from .serializers import (
    ShopSerializer, ShopRegistrationSerializer, ShopDetailSerializer,
    CategorySerializer
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_shop(request):
    """
    Register a new shop (for sellers only)
    """
    # Check if user is seller
    if request.user.user_type != 'seller':
        return Response(
            {'error': 'Only sellers can register shops'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Check if user already has a shop
    if hasattr(request.user, 'shop'):
        return Response(
            {'error': 'You already have a shop registered'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ShopRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        shop = serializer.save(owner=request.user)
        return Response(
            ShopSerializer(shop).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_shop(request):
    """
    Get current user's shop details
    """
    try:
        shop = request.user.shop
        serializer = ShopDetailSerializer(shop)
        return Response(serializer.data)
    except Shop.DoesNotExist:
        return Response(
            {'error': 'You do not have a shop registered'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_shop(request):
    """
    Update shop details
    """
    try:
        shop = request.user.shop
        serializer = ShopRegistrationSerializer(shop, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ShopSerializer(shop).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Shop.DoesNotExist:
        return Response(
            {'error': 'Shop not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def list_approved_shops(request):
    """
    List all approved shops (public - for customers)
    """
    shops = Shop.objects.filter(is_approved=True).order_by('-created_at')

    # Filter by city if provided
    city = request.query_params.get('city')
    if city:
        shops = shops.filter(city__iexact=city)

    serializer = ShopSerializer(shops, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_shop_detail(request, shop_id):
    """
    Get shop details by ID (public)
    """
    try:
        shop = Shop.objects.get(id=shop_id, is_approved=True)
        serializer = ShopDetailSerializer(shop, context={'request': request})
        return Response(serializer.data)
    except Shop.DoesNotExist:
        return Response(
            {'error': 'Shop not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def list_categories(request):
    """
    List all categories with subcategories (public)
    """
    # Get only parent categories
    parent_categories = Category.objects.filter(parent=None, is_active=True)
    serializer = CategorySerializer(parent_categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_category_detail(request, category_id):
    """
    Get category details with subcategories
    """
    try:
        category = Category.objects.get(id=category_id, is_active=True)
        serializer = CategorySerializer(category)
        return Response(serializer.data)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found'},
            status=status.HTTP_404_NOT_FOUND
        )