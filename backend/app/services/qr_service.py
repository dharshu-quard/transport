import hmac
import hashlib
import json
import time
from typing import Tuple, Dict, Any, Optional
from backend.app.core.config import settings

def _compute_hmac(data_str: str) -> str:
    key = settings.QR_SIGNING_SECRET.encode("utf-8")
    signature = hmac.new(key, data_str.encode("utf-8"), hashlib.sha256).hexdigest()
    return signature

def generate_qr_ticket_payload(
    ticket_id: str,
    booking_ref: str,
    trip_id: str,
    passenger_name: str,
    seat_number: int,
    fare: float
) -> Tuple[str, str]:
    payload_dict = {
        "v": 1,
        "type": "TICKET",
        "tid": ticket_id,
        "ref": booking_ref,
        "trip": trip_id,
        "pax": passenger_name,
        "seat": seat_number,
        "fare": fare,
        "iat": int(time.time())
    }
    canonical_json = json.dumps(payload_dict, sort_keys=True, separators=(",", ":"))
    signature = _compute_hmac(canonical_json)
    full_qr_content = json.dumps({
        "data": payload_dict,
        "sig": signature
    }, separators=(",", ":"))
    return full_qr_content, signature

def generate_qr_pass_payload(
    pass_id: str,
    pass_number: str,
    employee_code: str,
    holder_name: str,
    holder_type: str,
    valid_until: str
) -> Tuple[str, str]:
    payload_dict = {
        "v": 1,
        "type": "PASS",
        "pid": pass_id,
        "pnum": pass_number,
        "emp": employee_code,
        "name": holder_name,
        "role": holder_type,
        "exp": valid_until,
        "iat": int(time.time())
    }
    canonical_json = json.dumps(payload_dict, sort_keys=True, separators=(",", ":"))
    signature = _compute_hmac(canonical_json)
    full_qr_content = json.dumps({
        "data": payload_dict,
        "sig": signature
    }, separators=(",", ":"))
    return full_qr_content, signature

def verify_qr_payload(qr_string: str) -> Dict[str, Any]:
    """
    Verifies offline cryptographic integrity of any scanned QR ticket or pass.
    Detects forged signatures, tampering, and invalid formatting.
    """
    try:
        parsed = json.loads(qr_string)
        if not isinstance(parsed, dict) or "data" not in parsed or "sig" not in parsed:
            return {"valid": False, "forged": True, "error": "Invalid QR schema", "data": None}

        data_dict = parsed["data"]
        claimed_sig = parsed["sig"]

        canonical_json = json.dumps(data_dict, sort_keys=True, separators=(",", ":"))
        expected_sig = _compute_hmac(canonical_json)

        if not hmac.compare_digest(claimed_sig, expected_sig):
            return {
                "valid": False,
                "forged": True,
                "error": "Cryptographic signature mismatch! Ticket is forged or tampered.",
                "data": data_dict
            }

        return {
            "valid": True,
            "forged": False,
            "error": None,
            "data": data_dict,
            "type": data_dict.get("type")
        }
    except Exception as e:
        return {"valid": False, "forged": True, "error": f"Corrupt QR data: {str(e)}", "data": None}
