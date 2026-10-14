import uuid
from typing import Dict, Any

class MockPaymentGateway:
    """
    Mock adapter representing payment gateway (Razorpay / UPI / NetBanking).
    Cleanly isolated behind an interface per system rules.
    """
    @staticmethod
    def process_charge(amount: float, payment_method: str, user_id: str) -> Dict[str, Any]:
        tx_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        return {
            "success": True,
            "transaction_ref": tx_id,
            "gateway": "MockRazorpay",
            "amount": amount,
            "currency": "INR",
            "method": payment_method,
            "status": "CAPTURED",
            "message": "Payment authorized and captured instantly via mock gateway"
        }

    @staticmethod
    def process_refund(payment_ref: str, refund_amount: float) -> Dict[str, Any]:
        refund_id = f"RFND-{uuid.uuid4().hex[:10].upper()}"
        return {
            "success": True,
            "refund_id": refund_id,
            "original_payment": payment_ref,
            "refund_amount": refund_amount,
            "status": "PROCESSED",
            "message": "Refund credited to original payment source"
        }

payment_gateway = MockPaymentGateway()
