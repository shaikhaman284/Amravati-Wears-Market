# orders/migrations/XXXX_backfill_seller_earnings.py

from django.db import migrations
from decimal import Decimal


def backfill_seller_earnings(apps, schema_editor):
    """
    Backfill seller_earnings for all existing orders.
    seller_earnings = total_amount - commission_amount - cod_fee
    """
    Order = apps.get_model('orders', 'Order')

    # Process in batches to avoid memory issues
    batch_size = 500
    orders_to_update = []

    for order in Order.objects.all().iterator(chunk_size=batch_size):
        # Calculate seller earnings
        seller_earnings = order.total_amount - order.commission_amount - order.cod_fee
        order.seller_earnings = seller_earnings
        orders_to_update.append(order)

        # Update in batches
        if len(orders_to_update) >= batch_size:
            Order.objects.bulk_update(orders_to_update, ['seller_earnings'], batch_size=batch_size)
            orders_to_update = []
            print(f"Updated {batch_size} orders...")

    # Update remaining orders
    if orders_to_update:
        Order.objects.bulk_update(orders_to_update, ['seller_earnings'])
        print(f"Updated {len(orders_to_update)} orders...")

    print("Seller earnings backfill completed!")


def reverse_backfill(apps, schema_editor):
    """Reverse the backfill by setting seller_earnings back to 0"""
    Order = apps.get_model('orders', 'Order')
    Order.objects.all().update(seller_earnings=Decimal('0.00'))


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0006_order_seller_earnings'),  # Replace with your actual previous migration
    ]

    operations = [
        migrations.RunPython(backfill_seller_earnings, reverse_backfill),
    ]
