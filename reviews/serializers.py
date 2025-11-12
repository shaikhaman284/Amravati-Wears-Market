from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'customer_name', 'rating', 'review_text',
            'is_verified_purchase', 'created_at'
        ]
        read_only_fields = ['customer_name', 'is_verified_purchase', 'created_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['product', 'order', 'rating', 'review_text']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value