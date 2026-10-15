from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Error body shared by every endpoint, same shape as the Go version."""

    trace_id: str
    message: str


class APIError(Exception):
    """Raised by handlers; converted to an ErrorResponse by the app's exception handler."""

    def __init__(self, status_code: int, trace_id: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.trace_id = trace_id
        self.message = message


def error_response(status_code: int, trace_id: str, message: str) -> JSONResponse:
    body = ErrorResponse(trace_id=trace_id, message=message)
    return JSONResponse(status_code=status_code, content=body.model_dump())
