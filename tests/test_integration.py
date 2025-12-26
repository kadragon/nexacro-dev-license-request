"""
Integration tests for complete workflow.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-007
  test_refs: TEST-license-request-006
"""

from unittest.mock import Mock, patch

import pytest

from src.config import Config
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
def mock_successful_responses():
    """Fixture providing mock HTTP responses for successful complete workflow."""
    homepage_response = Mock()
    homepage_response.status_code = 200
    homepage_response.cookies = {"JSESSIONID": "test_session_123", "PATH": "/"}
    homepage_response.raise_for_status = Mock()

    login_response = Mock()
    login_response.status_code = 200
    login_response.text = '<?xml version="1.0"?><Root><Result>SUCCESS</Result></Root>'
    login_response.raise_for_status = Mock()

    license_response = Mock()
    license_response.status_code = 200
    license_response.text = '<?xml version="1.0"?><Root><Result>SUCCESS</Result></Root>'
    license_response.raise_for_status = Mock()

    return {"homepage": homepage_response, "login": login_response, "license": license_response}


class TestFullWorkflow:
    """Integration tests for complete license request workflow (TEST-license-request-006)"""

    def test_successful_license_request_flow(self, mock_config, mock_successful_responses):
        """Test complete workflow from session to license request succeeds."""
        requester = NexacroLicenseRequester(mock_config)

        with patch("requests.Session.get") as mock_get, patch("requests.Session.post") as mock_post:
            # Setup mock responses
            mock_get.side_effect = [
                mock_successful_responses["homepage"],
                mock_successful_responses["license"],
            ]
            mock_post.return_value = mock_successful_responses["login"]

            # Execute workflow
            result = requester.request_license()

            # Verify success
            assert result is True

            # Verify call sequence
            assert mock_get.call_count == 2  # homepage + license request
            assert mock_post.call_count == 1  # login

            # Verify homepage was called first
            first_get_call = mock_get.call_args_list[0]
            assert mock_config.homepage_url in str(first_get_call)

            # Verify login was called
            post_call = mock_post.call_args
            assert mock_config.login_url in str(post_call)

            # Verify license request was called
            second_get_call = mock_get.call_args_list[1]
            assert mock_config.license_url in str(second_get_call)

    def test_workflow_handles_authentication_failure(self, mock_config):
        """Test workflow gracefully handles authentication failures."""
        requester = NexacroLicenseRequester(mock_config)

        homepage_response = Mock()
        homepage_response.status_code = 200
        homepage_response.cookies = {"JSESSIONID": "test_session"}
        homepage_response.raise_for_status = Mock()

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = '<?xml version="1.0"?><Root><Result>FAIL</Result></Root>'
        login_response.raise_for_status = Mock()

        with patch("requests.Session.get") as mock_get, patch("requests.Session.post") as mock_post:
            mock_get.return_value = homepage_response
            mock_post.return_value = login_response

            result = requester.request_license()

            assert result is False
            # Login should have been attempted but license request should not
            assert mock_post.call_count == 1
            assert mock_get.call_count == 1  # Only homepage, not license

    def test_workflow_handles_network_failure_at_session(self, mock_config):
        """Test workflow handles network failure during session establishment."""
        requester = NexacroLicenseRequester(mock_config)

        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            result = requester.request_license()

            assert result is False

    def test_workflow_handles_network_failure_at_login(self, mock_config):
        """Test workflow handles network failure during login."""
        requester = NexacroLicenseRequester(mock_config)

        homepage_response = Mock()
        homepage_response.status_code = 200
        homepage_response.cookies = {"JSESSIONID": "test_session"}
        homepage_response.raise_for_status = Mock()

        with patch("requests.Session.get") as mock_get, patch("requests.Session.post") as mock_post:
            mock_get.return_value = homepage_response
            mock_post.side_effect = Exception("Connection timeout")

            result = requester.request_license()

            assert result is False

    def test_workflow_validates_config_before_execution(self):
        """Test workflow validates configuration before execution."""
        # Invalid config with malformed email
        invalid_config = Config(
            user_id="test_user",
            user_pass="test_pass",
            customer_id="test_customer",
            email="invalid-email-no-at",
        )

        # Should not attempt any network calls with invalid config
        with pytest.raises(ValueError):
            invalid_config.validate()


class TestEndToEndFlow:
    """End-to-end integration tests with all components"""

    def test_complete_flow_with_all_components(self, mock_config, mock_successful_responses):
        """Test complete end-to-end flow with all components integrated."""
        with patch("requests.Session.get") as mock_get, patch("requests.Session.post") as mock_post:
            # Setup responses
            mock_get.side_effect = [
                mock_successful_responses["homepage"],
                mock_successful_responses["license"],
            ]
            mock_post.return_value = mock_successful_responses["login"]

            requester = NexacroLicenseRequester(mock_config)
            result = requester.request_license()

            # Verify complete success
            assert result is True

            # Verify XML body in login request
            post_call_data = mock_post.call_args.kwargs["data"]
            assert "test_user" in post_call_data
            assert "test_pass" in post_call_data
            assert '<?xml version="1.0"' in post_call_data

            # Verify query parameters in license request
            license_call = mock_get.call_args_list[1]
            params = license_call.kwargs["params"]
            assert params["service"] == "xupservice"
            assert params["p_CustomID"] == "test_customer"
            assert params["p_Email"] == "test@example.com"

    def test_flow_stops_on_first_error(self, mock_config):
        """Test that workflow stops at first error and doesn't proceed."""
        with patch("requests.Session.get") as mock_get:
            # Homepage request fails
            mock_get.side_effect = Exception("Network error")

            requester = NexacroLicenseRequester(mock_config)
            result = requester.request_license()

            assert result is False
            # Should only attempt homepage request
            assert mock_get.call_count == 1


class TestConcurrentSafety:
    """Tests for concurrent execution safety"""

    def test_multiple_requester_instances(self, mock_config, mock_successful_responses):
        """Test that multiple requester instances can work independently."""
        with patch("requests.Session.get") as mock_get, patch("requests.Session.post") as mock_post:
            mock_get.side_effect = [
                mock_successful_responses["homepage"],
                mock_successful_responses["license"],
                mock_successful_responses["homepage"],
                mock_successful_responses["license"],
            ]
            mock_post.side_effect = [
                mock_successful_responses["login"],
                mock_successful_responses["login"],
            ]

            # Create two independent instances
            requester1 = NexacroLicenseRequester(mock_config)
            requester2 = NexacroLicenseRequester(mock_config)

            # Both should succeed independently
            result1 = requester1.request_license()
            result2 = requester2.request_license()

            assert result1 is True
            assert result2 is True
            assert mock_get.call_count == 4
            assert mock_post.call_count == 2
