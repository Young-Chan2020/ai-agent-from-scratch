import json
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_agent.core.errors import InvalidRequestError, ProviderUnavailableError


JsonResponse = dict[str, object]
HttpTransport = Callable[[str, dict[str, str], dict[str, object]], JsonResponse]


def send_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, object],
) -> JsonResponse:
    """Send a JSON POST request using only the Python standard library."""
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # English: Normalize HTTP failures so the runtime does not depend on urllib exceptions.
        # 中文：把 HTTP 錯誤統一成 ProviderError，避免上層依賴 urllib 的例外型別。
        if 400 <= exc.code < 500:
            raise InvalidRequestError(
                f"provider rejected the request with HTTP {exc.code}"
            ) from exc
        raise ProviderUnavailableError(
            f"provider returned HTTP {exc.code}"
        ) from exc
    except URLError as exc:
        raise ProviderUnavailableError("provider could not be reached") from exc
