from __future__ import annotations
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import enums
    from .exceptions import *

_allowed_status = [200, 201, 202, 204]
_error_map = {
    enums.ErrorType.GROUP: {
        403: WillClientForbidden("Forbidden to fetch group"),
        404: UnknownGroup("Unknown group"),
    },
    enums.ErrorType.MESSAGE: {
        403: WillClientForbidden("Forbidden to fetch message"),
        404: UnknownMessage("Unknown message")
    },
    enums.ErrorType.MEMBER: {
        403: WillClientForbidden("Forbidden to fetch member"),
        404: UnknownMember("Unknown member")
    },
    enums.ErrorType.AUTH: {
        403: WillClientForbidden("Forbidden to login"),
        404: UnknownLogin("Unknown login")
    },
    enums.ErrorType.OTHER: {
        401: WillClientUnauthorized("Unauthorized request"),
        403: WillClientForbidden("Forbidden to fetch data"),
        404: WillClientUnknown("Unknown error type for data"),
        405: WillClientException("Method not allowed while fetching data"),
        429: TooManyRequests("Request times out of credits"),
        500: WillClientException("WillClient internal error")
    }
}

def is_not_allowed_code(code: int) -> bool:
    return bool(code not in _allowed_status)

def raise_code_error(code: int, ertype: enums.ErrorType):
    error_map = _error_map.get(ertype, {})
    error_type = error_map.get(code)

    if error_type is None:
        error_type = _error_map[enums.ErrorType.OTHER].get(code, WillClientException("WillClient internal error"))

    raise error_type

class _Missing:
    __slots__ = ()

    def __eq__(self, other) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self):
        return '...'

MISSING: Any = _Missing()