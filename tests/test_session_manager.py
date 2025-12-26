"""
Unit tests for SessionManager class.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-005
  test_refs: TEST-license-request-001, TEST-license-request-002, TEST-license-request-003
"""

from unittest.mock import Mock, patch

import pytest
import requests

from src.config import Config
from src.exceptions import AuthenticationError, LicenseRequestError, NetworkError
from src.session_manager import SessionManager


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
def session_manager(mock_config):
    """Fixture providing SessionManager instance."""
    return SessionManager(mock_config)


class TestSessionEstablishment:
    """Tests for session establishment (TEST-license-request-001)"""

    def test_establish_session_success(self, session_manager):
        """Test successful session cookie retrieval."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.cookies = {"JSESSIONID": "test_session_id", "OTHER": "value"}
            mock_get.return_value = mock_response

            cookies = session_manager.establish_session()

            assert "JSESSIONID" in cookies
            assert cookies["JSESSIONID"] == "test_session_id"
            mock_get.assert_called_once_with(
                session_manager.config.homepage_url, timeout=session_manager.config.request_timeout
            )

    def test_establish_session_network_error(self, session_manager):
        """Test handling of network errors during session establishment."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            with pytest.raises(NetworkError):
                session_manager.establish_session()

    def test_establish_session_timeout(self, session_manager):
        """Test handling of timeout during session establishment."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            with pytest.raises(NetworkError, match="timeout"):
                session_manager.establish_session()

    def test_establish_session_http_error(self, session_manager):
        """Test handling of HTTP errors during session establishment."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
            mock_get.return_value = mock_response

            with pytest.raises(NetworkError):
                session_manager.establish_session()


class TestAuthentication:
    """Tests for login functionality (TEST-license-request-002)"""

    def test_login_success(self, session_manager):
        """Test successful authentication."""
        with patch.object(session_manager.session, "post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<?xml version="1.0"?><Root><Result>SUCCESS</Result></Root>'
            mock_post.return_value = mock_response

            result = session_manager.login()

            assert result is True
            assert mock_post.call_count == 1

            # Verify XML body was sent
            call_args = mock_post.call_args
            assert "data" in call_args.kwargs
            xml_body = call_args.kwargs["data"]
            assert "test_user" in xml_body
            assert "test_pass" in xml_body

    def test_login_authentication_failure(self, session_manager):
        """Test authentication failure with invalid credentials."""
        with patch.object(session_manager.session, "post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<?xml version="1.0"?><Root><Result>FAIL</Result></Root>'
            mock_post.return_value = mock_response

            with pytest.raises(AuthenticationError):
                session_manager.login()

    def test_login_network_error(self, session_manager):
        """Test handling of network errors during login."""
        with patch.object(session_manager.session, "post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError()

            with pytest.raises(NetworkError):
                session_manager.login()

    def test_build_login_xml(self, session_manager):
        """Test XML body construction for login."""
        xml = session_manager._build_login_xml()

        assert '<?xml version="1.0"' in xml
        assert "http://www.nexacroplatform.com/platform/dataset" in xml
        assert "<Parameters>" in xml
        assert '<Parameter id="RTYPE">XML</Parameter>' in xml
        assert '<Parameter id="DB">CS</Parameter>' in xml
        assert '<Parameter id="DBUSER">POTAL_USER</Parameter>' in xml
        assert '<Dataset id="input">' in xml
        assert '<Col id="userId">test_user</Col>' in xml
        assert '<Col id="userPass">test_pass</Col>' in xml


class TestLicenseRequest:
    """Tests for license request functionality (TEST-license-request-003)"""

    def test_request_license_email_success(self, session_manager):
        """Test successful license request submission."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<?xml version="1.0"?><Root><Result>SUCCESS</Result></Root>'
            mock_get.return_value = mock_response

            result = session_manager.request_license_email()

            assert result is True
            assert mock_get.call_count == 1

    def test_request_license_email_with_params(self, session_manager):
        """Test that license request includes proper query parameters."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<?xml version="1.0"?><Root><Result>SUCCESS</Result></Root>'
            mock_get.return_value = mock_response

            session_manager.request_license_email()

            call_args = mock_get.call_args
            assert "params" in call_args.kwargs
            params = call_args.kwargs["params"]

            # Verify all required parameters
            assert params["service"] == "xupservice"
            assert params["domain"] == "NEXTp"
            assert params["model"] == "CE_LicenseEMailSend_R01"
            assert params["format"] == "xml"
            assert params["version"] == "xplatform"
            assert params["p_ConType"] == "TECH2"
            assert params["p_Product"] == "NP14"
            assert params["p_Language"] == "KOR"
            assert params["p_CustomID"] == "test_customer"
            assert params["p_Email"] == "test@example.com"
            assert params["p_Merge"] == "N"
            assert params["zip"] == "false"

    def test_request_license_email_failure(self, session_manager):
        """Test handling of license request failure."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<?xml version="1.0"?><Root><Result>FAIL</Result></Root>'
            mock_get.return_value = mock_response

            with pytest.raises(LicenseRequestError):
                session_manager.request_license_email()

    def test_request_license_email_http_200_without_success(self, session_manager):
        """Test that HTTP 200 without SUCCESS text should fail (P1 bug fix)."""
        with patch.object(session_manager.session, "get") as mock_get:
            # Simulate HTTP 200 with error page content (no SUCCESS or FAIL)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = (
                "<html><body><h1>Error Page</h1><p>Something went wrong</p></body></html>"
            )
            mock_get.return_value = mock_response

            with pytest.raises(LicenseRequestError, match="Unknown response"):
                session_manager.request_license_email()

    def test_request_license_email_http_200_with_empty_response(self, session_manager):
        """Test that HTTP 200 with empty response should fail (P1 bug fix)."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ""
            mock_get.return_value = mock_response

            with pytest.raises(LicenseRequestError, match="Unknown response"):
                session_manager.request_license_email()

    def test_request_license_email_network_error(self, session_manager):
        """Test handling of network errors during license request."""
        with patch.object(session_manager.session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            with pytest.raises(NetworkError):
                session_manager.request_license_email()

    def test_build_license_params(self, session_manager):
        """Test query parameter construction for license request."""
        params = session_manager._build_license_params()

        assert params["service"] == "xupservice"
        assert params["domain"] == "NEXTp"
        assert params["model"] == "CE_LicenseEMailSend_R01"
        assert params["format"] == "xml"
        assert params["version"] == "xplatform"
        assert params["p_ConType"] == "TECH2"
        assert params["p_Product"] == "NP14"
        assert params["p_Language"] == "KOR"
        assert params["p_CustomID"] == "test_customer"
        assert params["p_Email"] == "test@example.com"
        assert params["p_Merge"] == "N"
        assert params["zip"] == "false"


class TestUserAgent:
    """Tests for User-Agent header configuration"""

    def test_user_agent_header_set(self, session_manager):
        """Test that User-Agent header is set in session."""
        assert "User-Agent" in session_manager.session.headers
        assert "Mozilla" in session_manager.session.headers["User-Agent"]
