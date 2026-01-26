import razorpay
import hmac
import hashlib
from app.config import settings

class PaymentService:
    def __init__(self):
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
    def create_order(self, amount: int, currency: str = "INR") -> dict:
        """
        Create a Razorpay order.
        amount is in smallest currency unit (paise for INR).
        """
        data = {
            "amount": amount,
            "currency": currency,
            "payment_capture": 1 # Auto capture
        }
        return self.client.order.create(data=data)
        
    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verify the payment signature.
        """
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        return self.client.utility.verify_payment_signature(params_dict)

payment_service = PaymentService() 
