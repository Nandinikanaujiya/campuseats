"""
CampusEats Orders Service — Error Handling (RFC 7807)
CS 543 Web Services · Assignment 4
Team 10: Nandini Kanaujiya, Radhika Verma, Alka Jha, Alok Mishra
"""

from flask import jsonify, make_response


def problem(status: int, title: str, detail: str, instance: str = None, type_uri: str = None):
    """
    Returns an RFC 7807 compliant problem details response.
    Ensures every failure across the service speaks the same error shape.
    """
    if type_uri is None:
        type_uri = f"https://campuseats.internal/errors/{title.lower().replace(' ', '-')}"

    body = {
        "type": type_uri,
        "title": title,
        "status": status,
        "detail": detail
    }
    if instance:
        body["instance"] = instance

    response = make_response(jsonify(body), status)
    response.headers["Content-Type"] = "application/problem+json"
    return response
