"""
CampusEats Orders Service — RFC 7807 & RFC 9457 Problem Details
CS 543 Web Services · Assignment 6
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

import xml.etree.ElementTree as ET
from flask import request, jsonify, make_response, Response
from typing import Optional, Dict, Any, List


# Stable Type URI Base
ERROR_URI_BASE = "https://campuseats.internal/errors"


def problem(
    status: int,
    title: str,
    detail: str,
    type_slug: Optional[str] = None,
    instance: Optional[str] = None,
    errors: Optional[List[Dict[str, Any]]] = None,
    extra_headers: Optional[Dict[str, str]] = None
) -> Response:
    """
    Returns an RFC 7807 / RFC 9457 Problem Details response.
    Supports content negotiation:
      - application/problem+json (default)
      - application/problem+xml (if Accept: application/xml or text/xml)
    Always enforces explicit charset: charset=utf-8.
    """
    slug = type_slug or title.lower().replace(" ", "-")
    type_uri = f"{ERROR_URI_BASE}/{slug}"
    req_path = instance or (request.path if request else None)

    # Detect XML content negotiation
    wants_xml = False
    if request:
        accept = request.headers.get("Accept", "")
        if "application/xml" in accept or "text/xml" in accept or "application/problem+xml" in accept:
            wants_xml = True

    if wants_xml:
        root = ET.Element("problem", xmlns="urn:ietf:rfc:7807")
        type_elem = ET.SubElement(root, "type")
        type_elem.text = type_uri
        title_elem = ET.SubElement(root, "title")
        title_elem.text = title
        status_elem = ET.SubElement(root, "status")
        status_elem.text = str(status)
        detail_elem = ET.SubElement(root, "detail")
        detail_elem.text = detail
        if req_path:
            inst_elem = ET.SubElement(root, "instance")
            inst_elem.text = req_path

        if errors:
            errors_elem = ET.SubElement(root, "errors")
            for err in errors:
                err_elem = ET.SubElement(errors_elem, "error")
                field_elem = ET.SubElement(err_elem, "field")
                field_elem.text = str(err.get("field", ""))
                msg_elem = ET.SubElement(err_elem, "message")
                msg_elem.text = str(err.get("message", ""))

        xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        res = make_response(xml_bytes, status)
        res.headers["Content-Type"] = "application/problem+xml; charset=utf-8"
    else:
        body: Dict[str, Any] = {
            "type": type_uri,
            "title": title,
            "status": status,
            "detail": detail
        }
        if req_path:
            body["instance"] = req_path
        if errors:
            body["errors"] = errors

        res = make_response(jsonify(body), status)
        res.headers["Content-Type"] = "application/problem+json; charset=utf-8"

    if extra_headers:
        for k, v in extra_headers.items():
            res.headers[k] = v

    return res
