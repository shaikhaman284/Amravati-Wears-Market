"""
Test FCM notification setup
Run with: python manage.py shell < test_fcm.py
"""

from accounts.models import User
from orders.notification_service import initialize_firebase, send_notification

# Initialize Firebase
try:
    initialize_firebase()
    print("✅ Firebase Admin SDK initialized successfully")
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    exit(1)

# Get a seller
seller = User.objects.filter(user_type='seller').first()
if not seller:
    print("❌ No seller found in database")
    exit(1)

print(f"\n📱 Seller: {seller.name} ({seller.phone})")
print(f"FCM Token: {seller.fcm_token if seller.fcm_token else 'NOT REGISTERED'}")

if seller.fcm_token:
    print("\n🔔 Testing notification send...")
    success = send_notification(
        fcm_token=seller.fcm_token,
        title="Test Notification",
        body="This is a test notification from backend",
        data={'type': 'test'}
    )
    
    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Failed to send test notification")
else:
    print("\n⚠️ Cannot send notification - FCM token not registered")
    print("\nTo fix this:")
    print("1. Open the seller app")
    print("2. Log out if already logged in")
    print("3. Log in again")
    print("4. Check the app logs for 'FCM token registered'")
