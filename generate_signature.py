import hmac
import hashlib
import sys

# Your Test Secret from config/request
# In a real app, never hardcode this. Here for your manual testing convenience.
SECRET = "h7n4MOgogqK13Nm3pjsrGp3K" 

def generate_signature(order_id, payment_id):
    """
    Generates the Razorpay signature for verification.
    Formula: hmac_sha256(order_id + "|" + payment_id, secret)
    """
    msg = f"{order_id}|{payment_id}".encode()
    signature = hmac.new(SECRET.encode(), msg, hashlib.sha256).hexdigest()
    return signature

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_signature.py <order_id> <payment_id>")
        print("Example: python generate_signature.py order_S8W0geguCecyoK pay_123456789")
    else:
        o_id = sys.argv[1]
        p_id = sys.argv[2]
        sig = generate_signature(o_id, p_id)
        print(f"\nSignature for:\nOrder ID: {o_id}\nPayment ID: {p_id}\n")
        print(f"razorpay_signature: {sig}")
