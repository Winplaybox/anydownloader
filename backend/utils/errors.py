from enum import Enum
from starlette.responses import JSONResponse

class ErrorCode(str, Enum):
    URL_MISSING = "URL_MISSING"
    URL_INVALID = "URL_INVALID"
    PLATFORM_UNSUPPORTED = "PLATFORM_UNSUPPORTED"
    NO_MEDIA = "NO_MEDIA"
    NOT_FOUND = "NOT_FOUND"
    PRIVATE_OR_RESTRICTED = "PRIVATE_OR_RESTRICTED"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_FAILED = "UPSTREAM_FAILED"
    TIMEOUT = "TIMEOUT"
    INTERNAL = "INTERNAL"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    SOURCE_BLOCKED = "SOURCE_BLOCKED"

ERROR_COPY = {
    ErrorCode.URL_MISSING: ("Paste a link to get started.", 400, False),
    ErrorCode.URL_INVALID: ("That doesn't look like a valid link.", 400, False),
    ErrorCode.PLATFORM_UNSUPPORTED: ("This site isn't supported yet. Supported: X, YouTube, Facebook, Instagram, TikTok.", 400, False),
    ErrorCode.NO_MEDIA: ("This post has no video or image to download.", 404, False),
    ErrorCode.NOT_FOUND: ("This post was deleted or doesn't exist.", 404, False),
    ErrorCode.PRIVATE_OR_RESTRICTED: ("This content is private, age-restricted, or needs login.", 403, False),
    ErrorCode.RATE_LIMITED: ("Too many requests. Try again in a minute.", 429, True),
    ErrorCode.UPSTREAM_FAILED: ("The platform didn't respond. Try again.", 502, True),
    ErrorCode.TIMEOUT: ("That took too long. Try again.", 504, True),
    ErrorCode.INTERNAL: ("Something went wrong on our side.", 500, True),
    ErrorCode.LOGIN_REQUIRED: ("This content needs a logged-in account to view.", 403, False),
    ErrorCode.SOURCE_BLOCKED: ("The platform is temporarily blocking our server. Please retry in a few minutes.", 503, True),
}

def get_error_message(code: ErrorCode) -> str:
    entry = ERROR_COPY.get(code)
    return entry[0] if entry else "Something went wrong on our side."

class AppError(Exception):
    def __init__(self, code: ErrorCode, custom_message: str = None, retryable: bool = None):
        default_msg, status_code, default_retryable = ERROR_COPY.get(
            code, ("Something went wrong on our side.", 500, True)
        )
        self.code = code
        self.message = custom_message or default_msg
        self.status_code = status_code
        self.retryable = retryable if retryable is not None else default_retryable
        super().__init__(self.message)

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            {
                "ok": False,
                "error": {
                    "code": self.code.value,
                    "message": self.message,
                    "retryable": self.retryable,
                },
            },
            status_code=self.status_code,
        )

def error_response(code: ErrorCode, custom_message: str = None, retryable: bool = None) -> JSONResponse:
    err = AppError(code, custom_message, retryable)
    return err.to_response()
