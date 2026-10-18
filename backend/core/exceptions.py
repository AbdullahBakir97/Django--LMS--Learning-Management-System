"""Every API error is an RFC 9457 problem document: {type, title, status, detail?, errors?}."""

from http import HTTPStatus

from rest_framework.views import exception_handler


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
    response["Content-Type"] = "application/problem+json"
    return response
