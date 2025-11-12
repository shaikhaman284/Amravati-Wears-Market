from django.db import models
from django.conf import settings
from products.models import Product
from orders.models import Order


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')

    rating = models.PositiveSmallIntegerField()  # 1-5
    review_text = models.TextField(blank=True, null=True)

    is_verified_purchase = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        unique_together = ['product', 'order', 'customer']  # One review per product per order

    def __str__(self):
        return f"Review by {self.customer.name} - {self.rating}★"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product average rating
        self.update_product_rating()

    def update_product_rating(self):
        """Update product's average rating and review count"""
        from django.db.models import Avg, Count
        stats = Review.objects.filter(product=self.product).aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        self.product.average_rating = stats['avg_rating'] or 0
        self.product.review_count = stats['count']
        self.product.save()