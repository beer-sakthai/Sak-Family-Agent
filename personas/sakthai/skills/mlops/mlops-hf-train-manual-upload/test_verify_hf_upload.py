import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

# The user wants me to assume the script is in the python path.
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


@patch("sakthai.scripts.verify_hf_upload.verify_url")
@patch("sys.exit")
def test_main_success_with_multiple_urls(mock_sys_exit: MagicMock, mock_verify_url: MagicMock):
    """
    Given multiple valid URLs via command-line arguments,
    When the main function is run and all URLs verify successfully,
    Then it should call verify_url for each URL and exit gracefully.
    """
    # Arrange
    mock_verify_url.return_value = True
    test_urls = ["http://url1.com", "http://url2.com"]
    with patch.object(sys, "argv", ["verify_hf_upload.py"] + test_urls):
        # Act
        verify_hf_upload.main()

    # Assert
    assert mock_verify_url.call_count == 2
    mock_verify_url.assert_any_call(test_urls[0], "Resource #1")
    mock_verify_url.assert_any_call(test_urls[1], "Resource #2")
    mock_sys_exit.assert_not_called()


@patch("sakthai.scripts.verify_hf_upload.verify_url")
@patch("sys.exit")
def test_main_failure_with_one_bad_url(mock_sys_exit: MagicMock, mock_verify_url: MagicMock):
    """
    Given multiple URLs where one fails verification,
    When the main function is run,
    Then it should call sys.exit(1).
    """
    # Arrange
    # Simulate the second URL failing
    mock_verify_url.side_effect = [True, False]
    test_urls = ["http://success.com", "http://fail.com"]
    with patch.object(sys, "argv", ["verify_hf_upload.py"] + test_urls):
        # Act
        verify_hf_upload.main()

    # Assert
    assert mock_verify_url.call_count == 2
    mock_sys_exit.assert_called_once_with(1)


@patch("sakthai.scripts.verify_hf_upload.verify_url")
@patch("sys.exit")
def test_main_exits_with_no_urls(mock_sys_exit: MagicMock, mock_verify_url: MagicMock, capsys):
    """
    Given no command-line arguments,
    When the main function is run,
    Then it should print a usage message and call sys.exit(1).
    """
    # Arrange
    with patch.object(sys, "argv", ["verify_hf_upload.py"]):
        # Act
        verify_hf_upload.main()

    # Assert
    mock_verify_url.assert_not_called()
    mock_sys_exit.assert_called_once_with(1)

    # Check that the usage message was printed to stdout
    captured = capsys.readouterr()
    assert "Usage: python3 verify_hf_upload.py <url1>" in captured.out


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