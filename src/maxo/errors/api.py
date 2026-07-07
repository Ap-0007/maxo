from typing import Any, Never

from maxo.errors.base import MaxoError


class MaxBotApiError(MaxoError):
    """Сервер возвращает это, если возникло исключение при вашем запросе."""

    code: str
    error: str
    message: str
    raw_data: Any = None

    def __str__(self) -> str:
        parts: list[str] = []
        if self.code:
            parts.append(f"code={self.code!r}")
        if self.error:
            parts.append(f"error={self.error!r}")
        if self.message:
            parts.append(f"message={self.message!r}")
        if self.raw_data and not parts:
            parts.append(f"raw_data={self.raw_data!r}")

        return f"{self.__class__.__name__}({', '.join(parts)})"


class MaxBotBadRequestError(MaxBotApiError): ...


class MaxBotForbiddenError(MaxBotApiError): ...


class MaxBotUnauthorizedError(MaxBotApiError): ...


class MaxBotNotFoundError(MaxBotApiError): ...


class MaxBotMethodNotAllowedError(MaxBotApiError): ...


class MaxBotUnsupportedMediaTypeError(MaxBotApiError): ...


class MaxBotTooManyRequestsError(MaxBotApiError): ...


class MaxBotUnknownServerError(MaxBotApiError): ...


class MaxBotServiceUnavailableError(MaxBotApiError): ...


class RetvalReturnedServerException(MaxoError): ...


_ERRORS_BY_STATUS: dict[int, type[MaxBotApiError]] = {
    400: MaxBotBadRequestError,
    401: MaxBotUnauthorizedError,
    403: MaxBotForbiddenError,
    404: MaxBotNotFoundError,
    405: MaxBotMethodNotAllowedError,
    415: MaxBotUnsupportedMediaTypeError,
    429: MaxBotTooManyRequestsError,
    500: MaxBotUnknownServerError,
    503: MaxBotServiceUnavailableError,
}


def raise_api_error(status_code: int, data: object) -> Never:
    code, error, message = _extract_api_error(data)
    error_type = _ERRORS_BY_STATUS.get(status_code, MaxBotApiError)
    raise error_type(code, error, message, data)


def _extract_api_error(data: object) -> tuple[str, str, str]:
    if not isinstance(data, dict):
        return "", "", ""

    code = data.get("code") or data.get("error_code", "")
    error = data.get("error") or data.get("error_data", "")
    message = data.get("message", "")
    return (
        _error_to_str(code),
        _error_to_str(error),
        _error_to_str(message),
    )


def _error_to_str(value: object) -> str:
    if value is None:
        return ""
    return str(value)
