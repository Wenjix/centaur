import time
from unittest.mock import patch

import httpx
import pytest
from client import BASE_URL, StandardMetricsClient


def _client() -> StandardMetricsClient:
    client = StandardMetricsClient(client_id="id", client_secret="secret")
    client._token_cache = {
        "access_token": "test-token",
        "expires_at": time.time() + 3600,
    }
    return client


def test_http_client_does_not_follow_redirects() -> None:
    """Credentialed requests must not be forwarded to redirect targets."""
    with _client()._get_http_client() as http_client:
        assert http_client.follow_redirects is False


def test_request_rejects_redirect_responses() -> None:
    """A redirect is an error, not a request to re-issue with credentials."""
    client = _client()
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(302, headers={"Location": "https://evil.example/x"})

    transport = httpx.MockTransport(handler)
    with (
        patch.object(
            client,
            "_get_http_client",
            return_value=httpx.Client(
                base_url=BASE_URL, transport=transport, follow_redirects=False
            ),
        ),
        pytest.raises(RuntimeError, match="redirect"),
    ):
        client._request("GET", "/companies")

    assert len(calls) == 1
