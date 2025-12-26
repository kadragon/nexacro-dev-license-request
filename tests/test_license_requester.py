"""
Unit tests for NexacroLicenseRequester main orchestrator.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-006
  test_refs: TEST-license-request-006
"""

import logging
from unittest.mock import Mock, patch

import pytest

from src.config import Config
from src.exceptions import AuthenticationError, LicenseRequestError, NetworkError
from src.nexacro_license_requester import NexacroLicenseRequester


@pytest.fixture
def mock_config():
    """Fixture providing test configuration."""
    return Config(
        user_id="test_user",
        user_pass="test_pass",
        customer_id="test_customer",
        email="test@example.com",
    )


@pytest.fixture
def license_requester(mock_config):
    """Fixture providing NexacroLicenseRequester instance."""
    return NexacroLicenseRequester(mock_config)


class TestLicenseRequester:
    """Tests for main orchestrator functionality"""

    def test_request_license_success(self, license_requester):
        """Test successful full workflow execution."""
        with patch("src.nexacro_license_requester.SessionManager") as MockSessionManager:
            mock_session = Mock()
            mock_session.establish_session.return_value = {"JSESSIONID": "test"}
            mock_session.login.return_value = True
            mock_session.request_license_email.return_value = True
            MockSessionManager.return_value.__enter__.return_value = mock_session

            result = license_requester.request_license()

            assert result is True
            mock_session.establish_session.assert_called_once()
            mock_session.login.assert_called_once()
            mock_session.request_license_email.assert_called_once()

    def test_request_license_session_failure(self, license_requester):
        """Test workflow handles session establishment failure."""
        with patch("src.nexacro_license_requester.SessionManager") as MockSessionManager:
            mock_session = Mock()
            mock_session.establish_session.side_effect = NetworkError("Session failed")
            MockSessionManager.return_value.__enter__.return_value = mock_session

            result = license_requester.request_license()

            assert result is False

    def test_request_license_login_failure(self, license_requester):
        """Test workflow handles login failure."""
        with patch("src.nexacro_license_requester.SessionManager") as MockSessionManager:
            mock_session = Mock()
            mock_session.establish_session.return_value = {"JSESSIONID": "test"}
            mock_session.login.side_effect = AuthenticationError("Login failed")
            MockSessionManager.return_value.__enter__.return_value = mock_session

            result = license_requester.request_license()

            assert result is False

    def test_request_license_request_failure(self, license_requester):
        """Test workflow handles license request failure."""
        with patch("src.nexacro_license_requester.SessionManager") as MockSessionManager:
            mock_session = Mock()
            mock_session.establish_session.return_value = {"JSESSIONID": "test"}
            mock_session.login.return_value = True
            mock_session.request_license_email.side_effect = LicenseRequestError("Request failed")
            MockSessionManager.return_value.__enter__.return_value = mock_session

            result = license_requester.request_license()

            assert result is False


class TestLogging:
    """Tests for logging functionality"""

    def test_logger_setup(self, license_requester):
        """Test that logger is properly configured."""
        assert license_requester.logger is not None
        assert license_requester.logger.name == "NexacroLicenseRequester"

    def test_logger_has_console_handler(self, license_requester):
        """Test that logger has console handler configured."""
        assert any(
            isinstance(h, logging.StreamHandler) for h in license_requester.logger.handlers
        ), "Logger should have at least one console handler"

    def test_logger_has_file_handler(self, license_requester):
        """Test that logger has file handler configured (P2 bug fix)."""
        assert any(isinstance(h, logging.FileHandler) for h in license_requester.logger.handlers), (
            "Logger should have file handler as documented"
        )

    def test_log_request_summary_success(self, license_requester):
        """Test logging of successful request summary."""
        with patch.object(license_requester.logger, "info") as mock_info:
            license_requester._log_request_summary(success=True, details={"step": "completed"})

            mock_info.assert_called_once()
            call_args = str(mock_info.call_args)
            assert "SUCCESS" in call_args or "success" in call_args

    def test_log_request_summary_failure(self, license_requester):
        """Test logging of failed request summary."""
        with patch.object(license_requester.logger, "error") as mock_error:
            license_requester._log_request_summary(
                success=False, details={"error": "Network timeout"}
            )

            mock_error.assert_called_once()


class TestMainEntryPoint:
    """Tests for main() entry point"""

    def test_main_with_valid_env(self, monkeypatch):
        """Test main() executes successfully with valid environment."""
        monkeypatch.setenv("NEXACRO_USER_ID", "test_user")
        monkeypatch.setenv("NEXACRO_USER_PASS", "test_pass")
        monkeypatch.setenv("NEXACRO_CUSTOMER_ID", "test_customer")
        monkeypatch.setenv("NEXACRO_EMAIL", "test@example.com")

        with patch("src.nexacro_license_requester.NexacroLicenseRequester") as MockRequester:
            mock_instance = Mock()
            mock_instance.request_license.return_value = True
            MockRequester.return_value = mock_instance

            from src.nexacro_license_requester import main

            # Should not raise and should return 0
            result = main()
            assert result == 0

    def test_main_with_missing_env(self, monkeypatch):
        """Test main() handles missing environment variables."""
        # Clear all env vars
        for var in ["NEXACRO_USER_ID", "NEXACRO_USER_PASS", "NEXACRO_CUSTOMER_ID", "NEXACRO_EMAIL"]:
            monkeypatch.delenv(var, raising=False)

        from src.nexacro_license_requester import main

        # Should return non-zero exit code
        result = main()
        assert result != 0

    def test_main_with_request_failure(self, monkeypatch):
        """Test main() handles request failure."""
        monkeypatch.setenv("NEXACRO_USER_ID", "test_user")
        monkeypatch.setenv("NEXACRO_USER_PASS", "test_pass")
        monkeypatch.setenv("NEXACRO_CUSTOMER_ID", "test_customer")
        monkeypatch.setenv("NEXACRO_EMAIL", "test@example.com")

        with patch("src.nexacro_license_requester.NexacroLicenseRequester") as MockRequester:
            mock_instance = Mock()
            mock_instance.request_license.return_value = False
            MockRequester.return_value = mock_instance

            from src.nexacro_license_requester import main

            result = main()
            assert result == 1
