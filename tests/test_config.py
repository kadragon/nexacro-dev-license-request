"""
Unit tests for Config class.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-004
"""

import pytest

from src.config import Config


class TestConfigFromEnv:
    """Tests for Config.from_env() class method."""

    def test_from_env_with_all_variables(self, monkeypatch):
        """Test successful config creation when all env vars are set."""
        monkeypatch.setenv("NEXACRO_USER_ID", "test_user")
        monkeypatch.setenv("NEXACRO_USER_PASS", "test_pass")
        monkeypatch.setenv("NEXACRO_CUSTOMER_ID", "test_customer")
        monkeypatch.setenv("NEXACRO_EMAIL", "test@example.com")

        config = Config.from_env()

        assert config.user_id == "test_user"
        assert config.user_pass == "test_pass"
        assert config.customer_id == "test_customer"
        assert config.email == "test@example.com"

    def test_from_env_missing_user_id(self, monkeypatch):
        """Test ValueError when NEXACRO_USER_ID is missing."""
        monkeypatch.setenv("NEXACRO_USER_PASS", "test_pass")
        monkeypatch.setenv("NEXACRO_CUSTOMER_ID", "test_customer")
        monkeypatch.setenv("NEXACRO_EMAIL", "test@example.com")

        with pytest.raises(ValueError, match="NEXACRO_USER_ID"):
            Config.from_env()

    def test_from_env_missing_user_pass(self, monkeypatch):
        """Test ValueError when NEXACRO_USER_PASS is missing."""
        monkeypatch.setenv("NEXACRO_USER_ID", "test_user")
        monkeypatch.setenv("NEXACRO_CUSTOMER_ID", "test_customer")
        monkeypatch.setenv("NEXACRO_EMAIL", "test@example.com")

        with pytest.raises(ValueError, match="NEXACRO_USER_PASS"):
            Config.from_env()

    def test_from_env_missing_customer_id(self, monkeypatch):
        """Test ValueError when NEXACRO_CUSTOMER_ID is missing."""
        monkeypatch.setenv("NEXACRO_USER_ID", "test_user")
        monkeypatch.setenv("NEXACRO_USER_PASS", "test_pass")
        monkeypatch.setenv("NEXACRO_EMAIL", "test@example.com")

        with pytest.raises(ValueError, match="NEXACRO_CUSTOMER_ID"):
            Config.from_env()

    def test_from_env_missing_email(self, monkeypatch):
        """Test ValueError when NEXACRO_EMAIL is missing."""
        monkeypatch.setenv("NEXACRO_USER_ID", "test_user")
        monkeypatch.setenv("NEXACRO_USER_PASS", "test_pass")
        monkeypatch.setenv("NEXACRO_CUSTOMER_ID", "test_customer")

        with pytest.raises(ValueError, match="NEXACRO_EMAIL"):
            Config.from_env()

    def test_from_env_missing_multiple_variables(self, monkeypatch):
        """Test ValueError lists all missing variables."""
        monkeypatch.setenv("NEXACRO_USER_ID", "test_user")

        with pytest.raises(ValueError) as exc_info:
            Config.from_env()

        error_message = str(exc_info.value)
        assert "NEXACRO_USER_PASS" in error_message
        assert "NEXACRO_CUSTOMER_ID" in error_message
        assert "NEXACRO_EMAIL" in error_message


class TestConfigValidation:
    """Tests for Config.validate() method."""

    def test_validate_valid_email(self):
        """Test validation passes with valid email."""
        config = Config(
            user_id="test_user",
            user_pass="test_pass",
            customer_id="test_customer",
            email="test@example.com",
        )

        # Should not raise
        config.validate()

    def test_validate_invalid_email_no_at(self):
        """Test validation fails when email missing @ symbol."""
        config = Config(
            user_id="test_user",
            user_pass="test_pass",
            customer_id="test_customer",
            email="invalid-email.com",
        )

        with pytest.raises(ValueError, match="Invalid email"):
            config.validate()

    def test_validate_empty_email(self):
        """Test validation fails with empty email."""
        config = Config(
            user_id="test_user", user_pass="test_pass", customer_id="test_customer", email=""
        )

        with pytest.raises(ValueError, match="Invalid email"):
            config.validate()


class TestConfigDefaults:
    """Tests for Config default values."""

    def test_default_urls(self):
        """Test that default URLs are set correctly."""
        config = Config(
            user_id="test_user",
            user_pass="test_pass",
            customer_id="test_customer",
            email="test@example.com",
        )

        assert config.homepage_url == "https://support.tobesoft.co.kr/Support/?menu=home"
        assert (
            config.login_url
            == "https://support.tobesoft.co.kr/Next_JSP/CS-Homepage/Next_JSP/Login/Login_new.jsp"
        )
        assert config.license_url == "https://next.tobesoft.com/FrontControllerServlet.do"

    def test_default_timeouts(self):
        """Test that default timeout values are set correctly."""
        config = Config(
            user_id="test_user",
            user_pass="test_pass",
            customer_id="test_customer",
            email="test@example.com",
        )

        assert config.request_timeout == 30
        assert config.max_retries == 3
