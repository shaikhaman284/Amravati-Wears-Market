from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Review
from orders.models import Order
from products.models import Product
from .serializers import ReviewSerializer, ReviewCreateSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request):
    """
    Create product review (only for delivered orders)
    """
    serializer = ReviewCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    product = serializer.validated_data['product']
    order = serializer.validated_data['order']

    # Verify order belongs to customer
    if order.customer != request.user:
        return Response(
            {'error': 'You can only review your own orders'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Verify order is delivered
    if order.order_status != 'delivered':
        return Response(
            {'error': 'You can only review delivered orders'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify product is in order
    if not order.items.filter(product=product).exists():
        return Response(
            {'error': 'Product not found in this order'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if review already exists
    if Review.objects.filter(product=product, order=order, customer=request.user).exists():
        return Response(
            {'error': 'You have already reviewed this product'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create review
    review = serializer.save(customer=request.user)

    return Response(
        ReviewSerializer(review).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_reviews(request, product_id):
    """
    Get all reviews for a product
    """
    try:
        product = Product.objects.get(id=product_id)
        reviews = Review.objects.filter(product=product).order_by('-created_at')

        # Sorting
        sort = request.query_params.get('sort', 'newest')
        if sort == 'highest':
            reviews = reviews.order_by('-rating', '-created_at')
        elif sort == 'lowest':
            reviews = reviews.order_by('rating', '-created_at')

        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'reviews': serializer.data,
            'average_rating': float(product.average_rating),
            'review_count': product.review_count
        })
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )