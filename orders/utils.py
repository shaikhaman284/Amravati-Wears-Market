# orders/utils.py - COMPLETE FILE

from decimal import Decimal
from products.models import Product


def calculate_order_totals(cart_items):
    """
    Calculate order totals with COD fee logic and variant stock validation

    Args:
        cart_items: List of dicts with {product_id, quantity, size, color}

    Returns:
        dict with pricing breakdown

    COD Logic:
    - Orders < ₹500: Add ₹50 COD fee
    - Orders >= ₹500: Free COD (₹0)
    """

    items_breakdown = []
    subtotal = Decimal('0')
    total_commission = Decimal('0')
    total_seller_payout = Decimal('0')

    for item in cart_items:
        try:
            product = Product.objects.get(id=item['product_id'], is_active=True)
        except Product.DoesNotExist:
            raise ValueError(f"Product {item['product_id']} not found or inactive")

        quantity = Decimal(str(item['quantity']))
        size = item.get('size')
        color = item.get('color')
        variant_id = None

        # Validate variant stock if size or color is specified
        if size or color:
            variant = product.get_variant(size=size, color=color)
            if not variant:
                size_display = size if size else 'No size'
                color_display = color if color else 'No color'
                raise ValueError(f"Variant not found for {product.name}: {size_display} / {color_display}")

            if variant.stock_quantity < item['quantity']:
                raise ValueError(
                    f"Insufficient stock for {product.name} ({size_display}/{color_display}). "
                    f"Available: {variant.stock_quantity}"
                )
            variant_id = variant.id
        else:
            # No variant specified - check total stock
            if product.stock_quantity < item['quantity']:
                raise ValueError(f"Insufficient stock for {product.name}. Available: {product.stock_quantity}")

        # Calculate item totals
        item_subtotal = product.display_price * quantity
        item_commission = (product.display_price - product.base_price) * quantity
        item_seller_amount = product.base_price * quantity

        items_breakdown.append({
            'product_id': product.id,
            'variant_id': variant_id,
            'product_name': product.name,
            'base_price': product.base_price,
            'display_price': product.display_price,
            'mrp': product.mrp,  # NEW: Add MRP to items breakdown
            'commission_rate': product.commission_rate,
            'quantity': item['quantity'],
            'size': size,
            'color': color,
            'item_subtotal': item_subtotal,
            'commission_amount': item_commission,
            'seller_amount': item_seller_amount
        })

        subtotal += item_subtotal
        total_commission += item_commission
        total_seller_payout += item_seller_amount

    # COD Fee Logic: ₹50 if subtotal < ₹500, else ₹0
    if subtotal < Decimal('500'):
        cod_fee = Decimal('50.00')
    else:
        cod_fee = Decimal('0.00')

    total_amount = subtotal + cod_fee

    return {
        'items': items_breakdown,
        'subtotal': subtotal,
        'cod_fee': cod_fee,
        'total_amount': total_amount,
        'commission_amount': total_commission,
        'seller_payout_amount': total_seller_payout
    }


def validate_cart_items(cart_items):
    """Validate cart items structure"""
    if not cart_items or not isinstance(cart_items, list):
        raise ValueError("Cart items must be a non-empty list")

    for item in cart_items:
        if 'product_id' not in item or 'quantity' not in item:
            raise ValueError("Each item must have product_id and quantity")

        if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
            raise ValueError("Quantity must be a positive integer")

    return True