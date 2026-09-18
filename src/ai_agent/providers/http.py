import json
from collections.abc import Callable, Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_agent.core.errors import InvalidRequestError, ProviderUnavailableError


JsonResponse = dict[str, object]
HttpTransport = Callable[[str, dict[str, str], dict[str, object]], JsonResponse]
StreamTransport = Callable[
    [str, dict[str, str], dict[str, object]], Iterator[dict[str, object]]
]


def _handle_http_error(exc: HTTPError) -> None:
    if 400 <= exc.code < 500:
        raise InvalidRequestError(
            f"provider rejected the request with HTTP {exc.code}"
        ) from exc
    raise ProviderUnavailableError(
        f"provider returned HTTP {exc.code}"
    ) from exc


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
        _handle_http_error(exc)
    except URLError as exc:
        raise ProviderUnavailableError("provider could not be reached") from exc


def send_sse_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, object],
) -> Iterator[dict[str, object]]:
    """Yield JSON payloads from a Server-Sent Events response."""
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            **headers,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue

                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break

                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    # English: The transport only parses SSE framing; provider adapters interpret event schemas.
                    # 中文：Transport 只負責解析 SSE framing，實際 event schema 仍由各 Provider Adapter 處理。
                    yield parsed
    except HTTPError as exc:
        _handle_http_error(exc)
    except URLError as exc:
        raise ProviderUnavailableError("provider could not be reached") from exc
