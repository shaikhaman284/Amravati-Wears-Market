import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
import os

# Initialize Firebase Admin SDK
cred_path = os.path.join(settings.BASE_DIR, settings.FIREBASE_CREDENTIALS_PATH)

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

def verify_firebase_token(id_token):
    """
    Verify Firebase ID token and return decoded token
    Returns: dict with user info or None if invalid
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Firebase token verification failed: {str(e)}")
        return None

def get_user_by_phone(phone_number):
    """
    Get Firebase user by phone number
    """
    try:
        user = auth.get_user_by_phone_number(phone_number)
        return user
    except Exception as e:
        print(f"Error getting user by phone: {str(e)}")
        return None