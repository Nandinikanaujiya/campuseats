"""
CampusEats Orders Service — Error Handling (RFC 7807)
CS 543 Web Services · Assignment 5
Team 11: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

from flask import jsonify, make_response


def problem(status: int, title: str, detail: str, instance: str = None, extra_headers: dict = None):
    """
    Returns an RFC 7807 problem details response with application/problem+json.
    """
    body = {
        "type": f"https://campuseats.internal/errors/{title.lower().replace(' ', '-')}",
        "title": title,
        "status": status,
        "detail": detail
    }
    if instance:
        body["instance"] = instance

    response = make_response(jsonify(body), status)
    response.headers["Content-Type"] = "application/problem+json"
    if extra_headers:
        for key, value in extra_headers.items():
            response.headers[key] = value
    return response
