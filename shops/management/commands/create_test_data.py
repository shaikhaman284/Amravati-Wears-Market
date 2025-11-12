"""
Quick script to create test data
Run: python manage.py shell < create_test_data.py
"""
from accounts.models import User
from shops.models import Shop, Category
from products.models import Product
from rest_framework.authtoken.models import Token

print("Creating test seller...")
seller, created = User.objects.get_or_create(
    phone='+919988776655',
    defaults={
        'name': 'Test Seller',
        'user_type': 'seller'
    }
)
print(f"Seller: {seller.name} ({seller.phone})")

# Get or create token
token, _ = Token.objects.get_or_create(user=seller)
print(f"Seller Token: {token.key}")

print("\nCreating test shop...")
shop, created = Shop.objects.get_or_create(
    owner=seller,
    defaults={
        'shop_name': 'Test Cloth Store',
        'address': '123 Main Street, Rajkamal Chowk',
        'city': 'Amravati',
        'pincode': '444601',
        'contact_number': '9988776655',
        'commission_rate': 15.00,
        'is_approved': True,
        'approval_status': 'approved'
    }
)
print(f"Shop: {shop.shop_name} (Approved: {shop.is_approved})")

print("\nCreating test products...")
category = Category.objects.filter(name='Shirts').first()
if not category:
    print("ERROR: Run 'python manage.py seed_categories' first!")
else:
    products_data = [
        {
            'name': 'Cotton Shirt White',
            'description': 'Pure cotton, comfortable fit',
            'base_price': 500,
            'stock_quantity': 50,
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['White']
        },
        {
            'name': 'Denim Shirt Blue',
            'description': 'Premium denim material',
            'base_price': 800,
            'stock_quantity': 30,
            'sizes': ['M', 'L', 'XL'],
            'colors': ['Blue']
        },
        {
            'name': 'Formal Shirt Black',
            'description': 'Perfect for office wear',
            'base_price': 600,
            'stock_quantity': 40,
            'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
            'colors': ['Black']
        }
    ]

    for prod_data in products_data:
        product, created = Product.objects.get_or_create(
            shop=shop,
            name=prod_data['name'],
            defaults={
                'category': category,
                'description': prod_data['description'],
                'base_price': prod_data['base_price'],
                'commission_rate': shop.commission_rate,
                'stock_quantity': prod_data['stock_quantity'],
                'sizes': prod_data['sizes'],
                'colors': prod_data['colors']
            }
        )
        if created:
            print(f"  ✓ {product.name}: Base ₹{product.base_price} → Display ₹{product.display_price}")

print("\n✅ Test data created!")
print(f"\nSeller Login Token: {token.key}")
print("Use this token in Authorization header for seller APIs")