import os
import sys
from unittest.mock import MagicMock, patch

# Need to mock huggingface_hub before importing poll_endpoint
sys.modules["huggingface_hub"] = MagicMock()

# Let's adjust sys.path to be able to import it
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/inference-endpoint"))
)

# noqa: E402
import poll_endpoint  # noqa: E402


class DummyEndpoint:
    def __init__(self, name: str, status: str, url: str) -> None:
        self.name = name
        self.status = status
        self.url = url


def test_poll_success() -> None:
    api_mock = MagicMock()
    # Mock list_inference_endpoints to return a running endpoint
    api_mock.list_inference_endpoints.return_value = [
        DummyEndpoint(name="sakthai-endpoint", status="running", url="http://example.com")
    ]

    with patch("time.sleep") as mock_sleep:
        result = poll_endpoint.poll(api_mock, max_polls=2, sleep_time=0)
        assert result == 0
        mock_sleep.assert_not_called()


def test_poll_timeout() -> None:
    api_mock = MagicMock()
    # Mock list_inference_endpoints to return a pending endpoint
    api_mock.list_inference_endpoints.return_value = [
        DummyEndpoint(name="sakthai-endpoint", status="pending", url="http://example.com")
    ]

    with patch("time.sleep") as mock_sleep:
        result = poll_endpoint.poll(api_mock, max_polls=2, sleep_time=0)
        assert result == 1
        assert mock_sleep.call_count == 2


def test_poll_exception_handling() -> None:
    api_mock = MagicMock()
    # Mock list_inference_endpoints to raise an exception
    api_mock.list_inference_endpoints.side_effect = Exception("API error")

    with patch("time.sleep") as mock_sleep:
        result = poll_endpoint.poll(api_mock, max_polls=2, sleep_time=0)
        assert result == 1
        assert mock_sleep.call_count == 2


def test_poll_no_endpoint() -> None:
    api_mock = MagicMock()
    # Mock list_inference_endpoints to return empty
    api_mock.list_inference_endpoints.return_value = []

    with patch("time.sleep") as mock_sleep:
        result = poll_endpoint.poll(api_mock, max_polls=2, sleep_time=0)
        assert result == 1
        assert mock_sleep.call_count == 2


def test_poll_other_endpoint() -> None:
    api_mock = MagicMock()
    # Mock list_inference_endpoints to return an endpoint not matching 'sakthai'
    api_mock.list_inference_endpoints.return_value = [
        DummyEndpoint(name="other-endpoint", status="running", url="http://example.com")
    ]

    with patch("time.sleep") as mock_sleep:
        result = poll_endpoint.poll(api_mock, max_polls=2, sleep_time=0)
        assert result == 1
        assert mock_sleep.call_count == 2
