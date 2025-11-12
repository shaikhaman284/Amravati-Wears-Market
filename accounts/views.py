from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from config.firebase_config import verify_firebase_token
from .serializers import UserRegistrationSerializer, UserSerializer, TokenVerificationSerializer

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register_or_login(request):
    """
    Register new user or login existing user with Firebase token

    Request Body:
    {
        "firebase_token": "Firebase ID token",
        "name": "User Name",
        "phone": "9876543210",
        "user_type": "customer" or "seller"
    }
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    firebase_token = serializer.validated_data['firebase_token']
    name = serializer.validated_data['name']
    phone = serializer.validated_data['phone']
    user_type = serializer.validated_data.get('user_type', 'customer')

    # Verify Firebase token
    decoded_token = verify_firebase_token(firebase_token)
    if not decoded_token:
        return Response(
            {'error': 'Invalid Firebase token'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    firebase_uid = decoded_token.get('uid')
    firebase_phone = decoded_token.get('phone_number', phone)

    # Get or create user
    user, created = User.objects.get_or_create(
        phone=firebase_phone,
        defaults={
            'name': name,
            'user_type': user_type,
            'firebase_uid': firebase_uid
        }
    )

    # Update name if user exists but name changed
    if not created and user.name != name:
        user.name = name
        user.save()

    # Get or create auth token
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'message': 'Login successful' if not created else 'Registration successful',
        'token': token.key,
        'user': UserSerializer(user).data,
        'is_new_user': created
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token(request):
    """
    Verify Firebase token and return user details

    Request Body:
    {
        "firebase_token": "Firebase ID token"
    }
    """
    serializer = TokenVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    firebase_token = serializer.validated_data['firebase_token']

    # Verify Firebase token
    decoded_token = verify_firebase_token(firebase_token)
    if not decoded_token:
        return Response(
            {'error': 'Invalid Firebase token'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    firebase_phone = decoded_token.get('phone_number')

    try:
        user = User.objects.get(phone=firebase_phone)
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found. Please register first.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def get_current_user(request):
    """
    Get current authenticated user details
    Requires: Authorization: Token <token>
    """
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
def logout(request):
    """
    Logout user by deleting auth token
    """
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# TEMPORARY TEST ENDPOINT - Remove in production
@api_view(['POST'])
@permission_classes([AllowAny])
def test_register(request):
    """
    Test registration without Firebase (for development only)
    """
    phone = request.data.get('phone')
    name = request.data.get('name')
    user_type = request.data.get('user_type', 'customer')

    if not phone or not name:
        return Response({'error': 'Phone and name required'}, status=status.HTTP_400_BAD_REQUEST)

    # Add +91 if not present
    if not phone.startswith('+'):
        phone = f'+91{phone}'

    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={
            'name': name,
            'user_type': user_type
        }
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'message': 'Test user created' if created else 'User already exists',
        'token': token.key,
        'user': UserSerializer(user).data
    })