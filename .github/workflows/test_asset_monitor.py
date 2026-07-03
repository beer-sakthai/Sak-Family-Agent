import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from unittest.mock import MagicMock, mock_open, patch

# The script is a sibling file in this directory, not part of a package.
sys.path.insert(0, str(Path(__file__).parent))
import run_asset_monitor  # noqa: E402


@patch("run_asset_monitor.verify_url")
@patch("run_asset_monitor.send_telegram_message")
@patch(
    "builtins.open", new_callable=mock_open, read_data="http://success.com\nhttp://alsosuccess.com"
)
@patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "test_chat_id"})
@patch("sys.exit")
def test_main_all_urls_succeed(
    mock_sys_exit: MagicMock,
    mock_open_file: MagicMock,
    mock_send_telegram: MagicMock,
    mock_verify_url: MagicMock,
):
    """
    Given a list of URLs where all are valid,
    When the main function runs,
    Then it should not send a Telegram message and should not exit with an error.
    """
    # Arrange
    mock_verify_url.return_value = True

    # Act
    run_asset_monitor.main()

    # Assert
    assert mock_verify_url.call_count == 2
    mock_send_telegram.assert_not_called()
    mock_sys_exit.assert_not_called()


@patch("run_asset_monitor.verify_url")
@patch("run_asset_monitor.send_telegram_message")
@patch("builtins.open", new_callable=mock_open, read_data="http://success.com\nhttp://fail.com")
@patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "test_chat_id"})
@patch("sys.exit")
def test_main_one_url_fails(
    mock_sys_exit: MagicMock,
    mock_open_file: MagicMock,
    mock_send_telegram: MagicMock,
    mock_verify_url: MagicMock,
):
    """
    Given a list of URLs where one fails verification,
    When the main function runs,
    Then it should send a Telegram message and exit with status 1.
    """
    # Arrange
    mock_verify_url.side_effect = [True, False]  # First URL succeeds, second fails

    # Act
    run_asset_monitor.main()

    # Assert
    assert mock_verify_url.call_count == 2
    mock_send_telegram.assert_called_once()
    # Check that the message includes the failed URL as a parsed URL token
    sent_message = mock_send_telegram.call_args[0][1]
    parsed_urls = []
    for token in sent_message.split():
        parsed = urlparse(token.strip(".,;:()[]{}<>\"'"))
        if parsed.scheme in {"http", "https"} and parsed.hostname:
            parsed_urls.append(parsed)
    assert any(p.scheme == "http" and p.hostname == "fail.com" for p in parsed_urls)
    mock_sys_exit.assert_called_once_with(1)


@patch("builtins.open")
@patch.dict(os.environ, {}, clear=True)  # Ensure environment is empty
@patch("sys.exit")
def test_main_no_telegram_chat_id(mock_sys_exit: MagicMock, mock_open_file: MagicMock, capsys):
    """
    Given the TELEGRAM_CHAT_ID environment variable is not set,
    When the main function runs,
    Then it should print an error and exit with status 1.
    """
    # Act
    run_asset_monitor.main()

    # Assert
    mock_open_file.assert_not_called()
    mock_sys_exit.assert_called_once_with(1)
    captured = capsys.readouterr()
    assert "TELEGRAM_CHAT_ID environment variable not set" in captured.err


@patch("builtins.open")
@patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "test_chat_id"})
@patch("sys.exit")
def test_main_config_file_not_found(mock_sys_exit: MagicMock, mock_open_file: MagicMock, capsys):
    """
    Given the URL config file does not exist,
    When the main function runs,
    Then it should print an error and exit with status 1.
    """
    # Arrange
    mock_open_file.side_effect = FileNotFoundError

    # Act
    run_asset_monitor.main()

    # Assert
    mock_sys_exit.assert_called_once_with(1)
    captured = capsys.readouterr()
    assert "Configuration file not found" in captured.err
