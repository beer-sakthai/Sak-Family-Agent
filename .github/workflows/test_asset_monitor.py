import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

# The script is in a non-standard path, so we import it carefully
from personas.sakthai.skills.monitoring.asset_monitor.scripts import run_asset_monitor


@patch("personas.sakthai.skills.monitoring.asset_monitor.scripts.run_asset_monitor.verify_url")
@patch("personas.sakthai.skills.monitoring.asset_monitor.scripts.run_asset_monitor.send_telegram_message")
@patch("builtins.open", new_callable=mock_open, read_data="http://success.com\nhttp://alsosuccess.com")
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


@patch("personas.sakthai.skills.monitoring.asset_monitor.scripts.run_asset_monitor.verify_url")
@patch("personas.sakthai.skills.monitoring.asset_monitor.scripts.run_asset_monitor.send_telegram_message")
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
    # Check that the message contains the failed URL
    sent_message = mock_send_telegram.call_args[0][1]
    assert "http://fail.com" in sent_message
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

```

### How These Tests Work

1.  **Comprehensive Mocking**: The tests use `@patch` to replace external dependencies (`open`, `os.environ`, `sys.exit`, and the imported `verify_url` and `send_telegram_message` functions) with mock objects. This ensures the test focuses only on the logic inside the `main` function.
2.  **Success Path (`test_main_all_urls_succeed`)**: This test simulates the ideal scenario where the config file is read and all URLs are verified successfully. It asserts that no alert is sent and the script does not exit with an error.
3.  **Failure Path (`test_main_one_url_fails`)**: This test simulates a failure. It configures the mock `verify_url` to return `False` for one of the URLs and asserts that `send_telegram_message` is called with the correct information and that the script exits with an error code.
4.  **Configuration Errors**: The tests for `test_main_no_telegram_chat_id` and `test_main_config_file_not_found` validate the script's startup checks, ensuring it fails gracefully and provides clear error messages when its environment is not set up correctly.

This test suite provides strong coverage for your asset monitor, making it a more reliable component of your agent's operational toolkit.

<!--
[PROMPT_SUGGESTION]How could I add logging to the `run_asset_monitor.py` script and test it?[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Refactor the `send_telegram_message` function to be a class that can be more easily mocked.[/PROMPT_SUGGESTION]
-->