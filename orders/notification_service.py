"""
Firebase Cloud Messaging Notification Service
Handles sending push notifications to seller devices
"""

import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    if not firebase_admin._apps:
        try:
            cred_path = os.path.join(settings.BASE_DIR, settings.FIREBASE_CREDENTIALS_PATH)
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise


def send_notification(fcm_token, title, body, data=None):
    """
    Send push notification to a specific device
    
    Args:
        fcm_token (str): FCM device token
        title (str): Notification title
        body (str): Notification body
        data (dict): Additional data payload
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not fcm_token:
        logger.warning("No FCM token provided")
        return False
    
    try:
        # Initialize Firebase if not already done
        initialize_firebase()
        
        # Create notification payload
        notification = messaging.Notification(
            title=title,
            body=body
        )
        
        # Create message
        message = messaging.Message(
            notification=notification,
            data=data or {},
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    channel_id='order_notifications',
                    priority='high',
                )
            )
        )
        
        # Send message
        response = messaging.send(message)
        logger.info(f"Successfully sent notification: {response}")
        return True
        
    except messaging.UnregisteredError:
        logger.warning(f"FCM token is invalid or unregistered: {fcm_token}")
        return False
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False


def send_new_order_notification(user, order):
    """
    Send notification for new order placement
    
    Args:
        user: User object (seller)
        order: Order object
    """
    if not user.fcm_token:
        logger.info(f"User {user.phone} has no FCM token registered")
        return False
    
    title = "🛍️ New Order Received!"
    body = f"Order #{order.order_number} - ₹{order.total_amount}"
    
    data = {
        'type': 'new_order',
        'order_number': order.order_number,
        'order_id': str(order.id),
        'total_amount': str(order.total_amount),
        'customer_name': order.customer_name,
    }
    
    return send_notification(user.fcm_token, title, body, data)


def send_order_cancelled_notification(user, order):
    """
    Send notification for order cancellation
    
    Args:
        user: User object (seller)
        order: Order object
    """
    if not user.fcm_token:
        logger.info(f"User {user.phone} has no FCM token registered")
        return False
    
    title = "❌ Order Cancelled"
    body = f"Order #{order.order_number} was cancelled by customer"
    
    data = {
        'type': 'order_cancelled',
        'order_number': order.order_number,
        'order_id': str(order.id),
        'total_amount': str(order.total_amount),
    }
    
    return send_notification(user.fcm_token, title, body, data)
