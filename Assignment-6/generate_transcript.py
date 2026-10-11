"""
Automated transcript generator for CS 543 Assignment 6
Runs curl commands against local server and records genuine output into transcript.txt
"""

import os
import sys
import time
import subprocess
import threading
import uuid
from app import app
from store import store


PORT = 5066
BASE_URL = f"http://127.0.0.1:{PORT}"
AUTH_HEADER = "Authorization: Bearer test-jwt-token"


def run_server():
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


def run_curl(cmd_args, description):
    full_cmd = ["curl.exe", "-i", "-s"] + cmd_args
    cmd_str = " ".join(cmd_args)
    proc = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = proc.stdout
    if not output and proc.stderr:
        output = proc.stderr

    section = []
    section.append("=" * 80)
    section.append(f"# {description}")
    section.append(f"# Command: curl.exe -i {cmd_str}")
    section.append("=" * 80)
    section.append(output.strip())
    section.append("\n")
    return "\n".join(section)


def main():
    store.clear()
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    transcript_parts = [
        "# " + "=" * 78,
        "# CS 543 Web Services · Assignment 6 — Honest responses: status codes, errors & validation",
        "# Live Verified curl -i Execution Transcript",
        "# Team 11: Nandini Kanaujiya (20251651061), Radhika Verma (20251651075), Alka Jha (20251651013), Alok Mishra (20251651014)",
        "# Service: CampusEats Orders Microservice",
        "# Target: http://127.0.0.1:5066",
        "# " + "=" * 78,
        "\n"
    ]

    # -------------------------------------------------------------------------
    # PART D1: Success Transcript (Happy Path)
    # -------------------------------------------------------------------------
    order1_payload = (
        '{"customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3", '
        '"canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb", '
        '"address": "Hostel 4, Room 201, South Campus", '
        '"items": [{"menu_item_id": "1e84ceb4-e952-47f6-b0f1-136805a9f5a6", "item_name": "Paneer Butter Masala Roll", "quantity": 2, "unit_price": 95.0}], '
        '"delivery_fee": 25.0, '
        '"custom_notes": "Extra mint chutney please"}'
    )
    t1 = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", order1_payload
    ], "D1. SUCCESS PATH: POST /orders -> 201 Created with Location header, ETag, and JSON body (Requirement A1, A3, C4)")
    transcript_parts.append(t1)

    # Extract created order ID and ETag from output
    import re
    loc_match = re.search(r"Location:\s*(/orders/[a-f0-9\-]+)", t1)
    etag_match = re.search(r"ETag:\s*(\"[^\"]+\")", t1)
    order1_id = loc_match.group(1).split("/")[-1] if loc_match else "unknown-id"
    order1_etag = etag_match.group(1) if etag_match else '""'

    # -------------------------------------------------------------------------
    # PART D2: Failure Transcript
    # -------------------------------------------------------------------------
    # 1. Missing Authentication (401 Unauthorized)
    t_fail_401 = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", "Content-Type: application/json",
        "-d", order1_payload
    ], "D2. FAILURE 1: Missing Bearer Token -> 401 Unauthorized with WWW-Authenticate and Problem Details (Requirement B1, B2)")
    transcript_parts.append(t_fail_401)

    # 2. Malformed JSON Body (400 Bad Request)
    t_fail_400 = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", '{"customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3", invalid_json'
    ], "D2. FAILURE 2: Malformed JSON syntax -> 400 Bad Request with Problem Details (invalid-json)")
    transcript_parts.append(t_fail_400)

    # 3. Empty Cart (422 Unprocessable Entity - empty-cart)
    empty_cart_payload = (
        '{"customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3", '
        '"canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb", '
        '"address": "Hostel 4, Room 201, South Campus", '
        '"items": []}'
    )
    t_fail_empty = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", empty_cart_payload
    ], "D2. FAILURE 3: Empty Cart -> 422 Unprocessable Entity with stable type 'empty-cart' (Requirement B2, C1)")
    transcript_parts.append(t_fail_empty)

    # 4. Multi-Field Validation Failure (422 Unprocessable Entity with errors[] reporting two bad fields)
    two_bad_fields_payload = (
        '{"customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3", '
        '"canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb", '
        '"address": "", '
        '"items": [{"menu_item_id": "1e84ceb4-e952-47f6-b0f1-136805a9f5a6", "item_name": "Chole Bhature", "quantity": 0, "unit_price": 90.0}]}'
    )
    t_fail_multi = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", two_bad_fields_payload
    ], "D2. FAILURE 4: Field-level multi-error validation -> 422 with errors[] list naming quantity <= 0 and empty address (Requirement B3, C2)")
    transcript_parts.append(t_fail_multi)

    # 5. Item Unavailable (422 Unprocessable Entity - item-unavailable)
    item_unavail_payload = (
        '{"customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3", '
        '"canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb", '
        '"address": "Hostel 4, Room 201, South Campus", '
        '"items": [{"menu_item_id": "1e84ceb4-e952-47f6-b0f1-136805a9f5a6", "item_name": "Cold Coffee Special (Out of Stock)", "quantity": 1, "unit_price": 60.0}]}'
    )
    t_fail_item = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", item_unavail_payload
    ], "D2. FAILURE 5: Item Unavailable -> 422 Unprocessable Entity with stable type 'item-unavailable' (Requirement B2)")
    transcript_parts.append(t_fail_item)

    # 6. Payment Declined (422 Unprocessable Entity - payment-declined)
    pay_decline_payload = (
        '{"customer_id": "c0d3c259-0aac-4c19-acef-bbb7cbd9d9d3", '
        '"canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb", '
        '"address": "Hostel 4, Room 201, South Campus", '
        '"payment_token": "tok_fail_card_declined", '
        '"items": [{"menu_item_id": "1e84ceb4-e952-47f6-b0f1-136805a9f5a6", "item_name": "Veg Thali", "quantity": 1, "unit_price": 110.0}]}'
    )
    t_fail_pay = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", pay_decline_payload
    ], "D2. FAILURE 6: Payment Declined -> 422 Unprocessable Entity with stable type 'payment-declined' (Requirement B2)")
    transcript_parts.append(t_fail_pay)

    # 7. Unknown Order ID (404 Not Found - order-not-found)
    unknown_uuid = str(uuid.uuid4())
    t_fail_404 = run_curl([
        "-X", "GET", f"{BASE_URL}/orders/{unknown_uuid}"
    ], "D2. FAILURE 7: Unknown Resource ID -> 404 Not Found with stable type 'order-not-found' (Requirement B2)")
    transcript_parts.append(t_fail_404)

    # 8. Illegal State Transition (409 Conflict - illegal-transition)
    # Cancel order1
    t_cancel_ok = run_curl([
        "-X", "POST", f"{BASE_URL}/orders/{order1_id}/cancel",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", '{"reason": "Changed my mind about the delivery location"}'
    ], "D2. SETUP: Cancel order1 -> 200 OK (Transitioning to cancelled state)")
    transcript_parts.append(t_cancel_ok)

    # Re-cancel already cancelled order -> 409 Conflict
    t_fail_409 = run_curl([
        "-X", "POST", f"{BASE_URL}/orders/{order1_id}/cancel",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", '{"reason": "Second cancellation attempt"}'
    ], "D2. FAILURE 8: Illegal Transition -> 409 Conflict with stable type 'illegal-transition' (Requirement B2)")
    transcript_parts.append(t_fail_409)

    # 9. Rate Limit Exceeded (429 Too Many Requests with Retry-After)
    rate_client_headers = "Authorization: Bearer rate-limit-test-client"
    for _ in range(60):
        subprocess.run(["curl.exe", "-s", f"{BASE_URL}/orders", "-H", rate_client_headers], capture_output=True)

    t_fail_429 = run_curl([
        "-X", "GET", f"{BASE_URL}/orders",
        "-H", rate_client_headers
    ], "D2. FAILURE 9: Rate Limit Exceeded -> 429 Too Many Requests with Retry-After header (Requirement A4, B2)")
    transcript_parts.append(t_fail_429)

    # 10. Service Unavailable / Simulated Outage (503 Service Unavailable with Retry-After)
    t_fail_503 = run_curl([
        "-X", "GET", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", "X-Simulate-Outage: 1"
    ], "D2. FAILURE 10: Service Outage / Maintenance -> 503 Service Unavailable with Retry-After: 60 header (Requirement A4, B2)")
    transcript_parts.append(t_fail_503)

    # -------------------------------------------------------------------------
    # PART D3: Content Negotiation Check (XML vs JSON vs 406)
    # -------------------------------------------------------------------------
    # Create fresh order for negotiation check
    order2_payload = (
        '{"customer_id": "d1e2f3a4-b5c6-47d8-9e0f-1a2b3c4d5e6f", '
        '"canteen_id": "b38ad05b-816e-4e22-b7c9-2b83c64fb9cb", '
        '"address": "Faculty Residence Block B, Flat 104", '
        '"items": [{"menu_item_id": "2f95dfc5-f063-4807-c102-247916b0a6b7", "item_name": "Masala Dosa with Sambar", "quantity": 1, "unit_price": 80.0}]}'
    )
    t_order2 = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", order2_payload
    ], "D3. SETUP: Create second order for Content Negotiation tests")
    transcript_parts.append(t_order2)

    order2_id = re.search(r"Location:\s*(/orders/[a-f0-9\-]+)", t_order2).group(1).split("/")[-1]

    # D3.1: Request XML
    t_xml = run_curl([
        "-X", "GET", f"{BASE_URL}/orders/{order2_id}",
        "-H", "Accept: application/xml"
    ], "D3. CONTENT NEGOTIATION 1: Accept: application/xml -> 200 OK with Content-Type: application/xml; charset=utf-8 (Requirement C3, C4)")
    transcript_parts.append(t_xml)

    # D3.2: Request JSON (default)
    t_json = run_curl([
        "-X", "GET", f"{BASE_URL}/orders/{order2_id}",
        "-H", "Accept: application/json"
    ], "D3. CONTENT NEGOTIATION 2: Accept: application/json -> 200 OK with Content-Type: application/json; charset=utf-8 (Requirement C3, C4)")
    transcript_parts.append(t_json)

    # D3.3: Request unsupported media type -> 406 Not Acceptable
    t_406 = run_curl([
        "-X", "GET", f"{BASE_URL}/orders/{order2_id}",
        "-H", "Accept: text/csv"
    ], "D3. CONTENT NEGOTIATION 3: Accept: text/csv -> 406 Not Acceptable with Problem Details (Requirement C3)")
    transcript_parts.append(t_406)

    # -------------------------------------------------------------------------
    # PART D4: No Regressions (A5 Checks)
    # -------------------------------------------------------------------------
    # 1. Idempotency-Key Safe Replay
    idem_key = "idem-key-" + uuid.uuid4().hex[:12]
    t_idem1 = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", f"Idempotency-Key: {idem_key}",
        "-H", "Content-Type: application/json",
        "-d", order1_payload
    ], "D4. REGRESSION 1 (First Call): POST /orders with Idempotency-Key -> 201 Created (Requirement D4)")
    transcript_parts.append(t_idem1)

    t_idem2 = run_curl([
        "-X", "POST", f"{BASE_URL}/orders",
        "-H", AUTH_HEADER,
        "-H", f"Idempotency-Key: {idem_key}",
        "-H", "Content-Type: application/json",
        "-d", order1_payload
    ], "D4. REGRESSION 1 (Replay Call): POST /orders with identical Idempotency-Key -> 201 Created with X-Cache-Lookup: HIT-IDEMPOTENT (Requirement D4)")
    transcript_parts.append(t_idem2)

    # Extract ID and ETag of order2
    order2_etag = re.search(r"ETag:\s*(\"[^\"]+\")", t_order2).group(1)

    # 2. Conditional GET with If-None-Match -> 304 Not Modified
    t_cond_get = run_curl([
        "-X", "GET", f"{BASE_URL}/orders/{order2_id}",
        "-H", f"If-None-Match: {order2_etag}"
    ], "D4. REGRESSION 2: Conditional GET with If-None-Match -> 304 Not Modified with empty body (Requirement D4)")
    transcript_parts.append(t_cond_get)

    # 3. Conditional PUT with mismatched If-Match -> 412 Precondition Failed
    t_put_412 = run_curl([
        "-X", "PUT", f"{BASE_URL}/orders/{order2_id}",
        "-H", AUTH_HEADER,
        "-H", 'If-Match: "mismatched-etag-12345"',
        "-H", "Content-Type: application/json",
        "-d", '{"address": "Faculty Residence Block B, Flat 204"}'
    ], "D4. REGRESSION 3: Conditional PUT with invalid If-Match -> 412 Precondition Failed (Requirement D4)")
    transcript_parts.append(t_put_412)

    # 4. PATCH /orders/{id} -> 200 OK
    t_patch = run_curl([
        "-X", "PATCH", f"{BASE_URL}/orders/{order2_id}",
        "-H", AUTH_HEADER,
        "-H", "Content-Type: application/json",
        "-d", '{"custom_notes": "Ring doorbell twice upon arrival"}'
    ], "D4. REGRESSION 4: Partial update via PATCH /orders/{id} -> 200 OK with updated entity (Requirement A1)")
    transcript_parts.append(t_patch)

    # 5. DELETE /orders/{id} -> 204 No Content
    t_delete = run_curl([
        "-X", "DELETE", f"{BASE_URL}/orders/{order2_id}",
        "-H", AUTH_HEADER
    ], "D4. REGRESSION 5: DELETE /orders/{id} -> 204 No Content (Requirement A1, D4)")
    transcript_parts.append(t_delete)

    # Confirm 404 after delete
    t_after_delete = run_curl([
        "-X", "GET", f"{BASE_URL}/orders/{order2_id}"
    ], "D4. REGRESSION 5 VERIFY: GET /orders/{id} after deletion -> 404 Not Found (Requirement D4)")
    transcript_parts.append(t_after_delete)

    # 6. OPTIONS on collection and item
    t_opts_coll = run_curl([
        "-X", "OPTIONS", f"{BASE_URL}/orders"
    ], "D4. REGRESSION 6: OPTIONS /orders -> 204 No Content with Allow: GET, POST, OPTIONS, HEAD")
    transcript_parts.append(t_opts_coll)

    t_opts_item = run_curl([
        "-X", "OPTIONS", f"{BASE_URL}/orders/{order1_id}"
    ], "D4. REGRESSION 7: OPTIONS /orders/{id} -> 204 No Content with Allow: GET, PUT, PATCH, DELETE, OPTIONS, HEAD")
    transcript_parts.append(t_opts_item)

    # 7. 301 Redirect on singular noun
    t_redirect = run_curl([
        "-X", "GET", f"{BASE_URL}/order/{order1_id}"
    ], "D4. REGRESSION 8: GET /order/{id} singular URI -> 301 Moved Permanently with Location: /orders/{id}")
    transcript_parts.append(t_redirect)

    # Save to transcript.txt and curl-transcript.txt
    full_transcript = "\n".join(transcript_parts)
    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(full_transcript)
    with open("curl-transcript.txt", "w", encoding="utf-8") as f:
        f.write(full_transcript)

    print("Successfully generated transcript.txt and curl-transcript.txt!")


if __name__ == "__main__":
    main()
