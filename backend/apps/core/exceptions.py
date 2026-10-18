"""Every API error is an RFC 9457 problem document: {type, title, status, detail?, errors?}."""

from http import HTTPStatus

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class PaymentRequired(APIException):
    status_code = 402
    default_detail = "Buy this course to enrol."
    default_code = "payment_required"


def problem_details_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    status = response.status_code
    problem = {"type": "about:blank", "title": HTTPStatus(status).phrase, "status": status}
    data = response.data
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        problem["detail"] = str(data["detail"])
    else:
        problem["errors"] = data
    response.data = problem
    # The attribute survives rendering (which rewrites the header); the header serves callers
    # that read the response before it is rendered.
    response.content_type = response["Content-Type"] = "application/problem+json"
    return response
