# Amravati Wears Market - API Documentation

**Base URL:** `https://api.awm27.shop`

---

## Authentication

All authenticated endpoints require header:
```
Authorization: Token <user_token>
```

---

## 1. Authentication APIs

### Register/Login
**POST** `/api/auth/test-register/`

Request:
```json
{
  "phone": "9876543210",
  "name": "John Doe",
  "user_type": "customer"  // or "seller"
}
```

Response:
```json
{
  "message": "Test user created",
  "token": "abc123...",
  "user": {
    "id": 1,
    "phone": "+919876543210",
    "name": "John Doe",
    "user_type": "customer"
  }
}
```

### Get Current User
**GET** `/api/auth/me/`

Requires: Token

---

## 2. Shop APIs

### Register Shop
**POST** `/api/shops/register/`

Requires: Token (seller only)

Request:
```json
{
  "shop_name": "My Cloth Store",
  "address": "123 Main Street",
  "city": "Amravati",
  "pincode": "444601",
  "contact_number": "9988776655"
}
```

### Get Approved Shops
**GET** `/api/shops/approved/`

Query params: `?city=Amravati`

### Get My Shop
**GET** `/api/shops/my-shop/`

Requires: Token (seller)

---

## 3. Category APIs

### List Categories
**GET** `/api/shops/categories/`

Returns categories with subcategories

---

## 4. Product APIs

### List Products (Customer)
**GET** `/api/products/`

Query params:
- `category`: Filter by category ID
- `shop`: Filter by shop ID
- `search`: Search in name/description
- `min_price`, `max_price`: Price range (display_price)
- `sort`: `price_low`, `price_high`, `newest`, `popular`

Response shows `display_price` (what customer pays)

### Get Product Detail
**GET** `/api/products/{id}/`

### Create Product (Seller)
**POST** `/api/products/create/`

Requires: Token (seller with approved shop)

Request:
```json
{
  "category": 1,
  "name": "Cotton Shirt",
  "description": "Pure cotton",
  "base_price": 500,
  "stock_quantity": 50,
  "sizes": ["S", "M", "L", "XL"],
  "colors": ["White", "Blue"]
}
```

Response includes pricing breakdown:
```json
{
  "message": "Product created",
  "product": {
    "base_price": "500.00",
    "display_price": "575.00",
    "commission_rate": "15.00"
  },
  "pricing_info": {
    "base_price": 500.0,
    "commission_amount": 75.0,
    "display_price": 575.0,
    "note": "You receive base_price. Customer pays display_price."
  }
}
```

### List My Products (Seller)
**GET** `/api/products/my-products/`

Shows both base_price and display_price

### Update Product
**PUT/PATCH** `/api/products/update/{id}/`

### Delete Product
**DELETE** `/api/products/delete/{id}/`

Soft delete (sets is_active=False)

---

## 5. Order APIs

### Create Order
**POST** `/api/orders/create/`

Requires: Token (customer)

Request:
```json
{
  "cart_items": [
    {
      "product_id": 1,
      "quantity": 2,
      "size": "M",
      "color": "Blue"
    }
  ],
  "customer_name": "John Doe",
  "customer_phone": "9876543210",
  "delivery_address": "123 Street",
  "city": "Amravati",
  "pincode": "444601",
  "landmark": "Near Temple"
}
```

**COD Fee Logic:**
- Subtotal < ₹500: COD fee = ₹50
- Subtotal ≥ ₹500: COD fee = ₹0

### Get My Orders (Customer)
**GET** `/api/orders/my-orders/`

Query params: `?status=placed`

### Get Order Detail
**GET** `/api/orders/{order_number}/`

### Get Seller Orders
**GET** `/api/orders/seller/orders/`

Requires: Token (seller)

### Update Order Status
**PATCH** `/api/orders/seller/{order_number}/status/`

Requires: Token (seller)

Request:
```json
{
  "order_status": "confirmed"
}
```

Valid transitions:
- placed → confirmed
- confirmed → shipped
- shipped → delivered

### Seller Dashboard
**GET** `/api/orders/seller/dashboard/`

Returns:
```json
{
  "total_products": 10,
  "pending_orders": 3,
  "today_orders": 5,
  "total_earnings": 15000.0,
  "pending_earnings": 3000.0,
  "recent_orders": [...]
}
```

---

## 6. Review APIs

### Create Review
**POST** `/api/reviews/create/`

Requires: Token, delivered order

Request:
```json
{
  "product": 1,
  "order": 1,
  "rating": 5,
  "review_text": "Great product!"
}
```

### Get Product Reviews
**GET** `/api/reviews/product/{product_id}/`

Query params: `?sort=highest` or `newest` or `lowest`

---

## Pricing Model

**Seller enters:** Base Price (what they receive)

**System calculates:** Display Price = Base Price × 1.15

**Customer pays:** Display Price

**Example:**
- Seller sets: ₹500
- Customer pays: ₹575
- Seller receives: ₹500
- Platform earns: ₹75 (15% commission)

---

## Error Responses

```json
{
  "error": "Error message"
}
```

Common status codes:
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error