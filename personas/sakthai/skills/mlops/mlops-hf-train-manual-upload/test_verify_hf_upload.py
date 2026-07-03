import subprocess
from unittest.mock import MagicMock, patch

import pytest

from sakthai.scripts import verify_hf_upload


@patch("subprocess.run")
def test_verify_url_success_on_200_status(mock_subprocess_run: MagicMock):
    """
    Given a URL,
    When the curl command returns a '200' status code,
    Then verify_url should return True.
    """
    # Arrange: Configure the mock to simulate a successful curl command
    mock_result = MagicMock()
    mock_result.stdout = "200"
    mock_subprocess_run.return_value = mock_result

    # Act
    result = verify_hf_upload.verify_url("https://example.com/success", "Test Resource")

    # Assert
    assert result is True
    mock_subprocess_run.assert_called_once_with(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', "https://example.com/success"],
        capture_output=True, text=True, check=True, timeout=30
    )


@patch("subprocess.run")
def test_verify_url_failure_on_404_status(mock_subprocess_run: MagicMock):
    """
    Given a URL,
    When the curl command returns a non-200 status code (e.g., '404'),
    Then verify_url should return False.
    """
    # Arrange: Configure the mock to simulate a failed curl command (404 Not Found)
    mock_result = MagicMock()
    mock_result.stdout = "404"
    mock_subprocess_run.return_value = mock_result

    # Act
    result = verify_hf_upload.verify_url("https://example.com/notfound", "Test Resource")

    # Assert
    assert result is False
    mock_subprocess_run.assert_called_once()


@patch("subprocess.run")
def test_verify_url_error_on_subprocess_exception(mock_subprocess_run: MagicMock):
    """
    Given a URL,
    When the subprocess.run command raises an exception (e.g., TimeoutExpired),
    Then verify_url should catch it and return False.
    """
    # Arrange: Configure the mock to raise an exception
    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="curl", timeout=30)

    # Act
    result = verify_hf_upload.verify_url("https://example.com/timeout", "Test Resource")

    # Assert
    assert result is False
    mock_subprocess_run.assert_called_once()