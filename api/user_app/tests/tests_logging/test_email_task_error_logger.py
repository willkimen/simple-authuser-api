import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from user_app.constants.logging import (
    EMAIL_TASK_ERROR_LEVEL,
    EMAIL_TASK_ERROR_LEVEL_NAME,
    EMAIL_TASK_ERROR_LOGGER_NAME,
)


@pytest.fixture
def mock_logging_configuration(monkeypatch, tmp_path) -> Path:
    """
    Fixture that temporarily adjusts the logging configuration for testing.

    It modifies the log file path to a temporary directory and
    reloads the logging setup to apply the changes.

    Returns:
        Path: Path to the temporary log file.
    """
    # Set the log file path to a temporary directory
    log_file = tmp_path / "email_task_errors.log"

    # Copy the original logging configuration to avoid modifying it globally
    logging_config = settings.LOGGING.copy()

    # Update the log file path in the copied configuration
    logging_config["handlers"]["email_task_error_file"]["filename"] = str(log_file)

    # Temporarily override the settings.LOGGING with the updated configuration
    monkeypatch.setattr(settings, "LOGGING", logging_config)

    # Apply the updated logging configuration
    logging.config.dictConfig(settings.LOGGING)

    return log_file


def test_log_level_is_registered_correctly():
    """
    Test that checks if the custom log level is registered correctly.

    It verifies that the numeric and string representations match.
    """
    assert logging.getLevelName(EMAIL_TASK_ERROR_LEVEL) == EMAIL_TASK_ERROR_LEVEL_NAME
    assert logging.getLevelName(EMAIL_TASK_ERROR_LEVEL_NAME) == EMAIL_TASK_ERROR_LEVEL


def test_logger_calls_internal_log_when_email_task_error_is_used():
    """
    Test that ensures the custom method email_task_error internally calls _log.

    It mocks _log and verifies it is called with the correct parameters.
    """
    logger = logging.getLogger("test_logger")

    # Ensures the custom method has been added
    assert hasattr(logger, "email_task_error")

    with patch.object(logger, "_log") as mock_log:
        logger.email_task_error("Test message")

        mock_log.assert_called_once_with(
            EMAIL_TASK_ERROR_LEVEL, "Test message", (), **{}
        )


def test_email_task_error_logger_has_correct_level():
    """
    Test that checks if the logger has the correct log level.

    It verifies that the logger's level matches the expected custom level.
    """
    logger = logging.getLogger(EMAIL_TASK_ERROR_LOGGER_NAME)

    assert logger.level == EMAIL_TASK_ERROR_LEVEL


def test_email_task_error_handler_has_correct_level():
    """
    Test that checks if the FileHandler associated with the
    logger has the correct level.

    It ensures that the handler level matches the expected custom level.
    """
    logger = logging.getLogger(EMAIL_TASK_ERROR_LOGGER_NAME)

    file_handler = next(
        (
            handler
            for handler in logger.handlers
            if isinstance(handler, logging.FileHandler)
        ),
        None,
    )

    assert file_handler is not None
    assert file_handler.level == EMAIL_TASK_ERROR_LEVEL


def test_email_task_error_log_written(mock_logging_configuration: Path):
    """
    Test that verifies if a log message is correctly written to the file.

    It checks if the custom logging method creates the file
    and if the file contains the expected message.
    """
    log_file = mock_logging_configuration

    logger = logging.getLogger(EMAIL_TASK_ERROR_LOGGER_NAME)

    # Call the custom logging method.
    logger.email_task_error("This is a test error.")

    # Verify that the file was created and contains the log message.
    assert log_file.exists()
    content = log_file.read_text()
    assert "This is a test error." in content
