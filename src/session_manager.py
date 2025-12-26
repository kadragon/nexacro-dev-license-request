"""
Manages HTTP sessions, cookies, and authentication for TOBESOFT portal.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-005
"""

import requests

from src.config import Config
from src.exceptions import AuthenticationError, LicenseRequestError, NetworkError


class SessionManager:
    """Manages session lifecycle for TOBESOFT support portal."""

    def __init__(self, config: Config):
        """
        Initialize session manager with configuration.

        Args:
            config: Configuration instance with credentials and URLs
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )

    def establish_session(self) -> dict[str, str]:
        """
        Retrieve initial session cookies from homepage.

        Returns:
            Dict mapping cookie names to values

        Raises:
            NetworkError: If homepage is unreachable or request fails
        """
        try:
            response = self.session.get(
                self.config.homepage_url, timeout=self.config.request_timeout
            )
            response.raise_for_status()

            # Convert cookies to dictionary
            return dict(response.cookies.items())

        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Request timeout: {self.config.homepage_url}") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection failed: {self.config.homepage_url}") from e
        except requests.exceptions.HTTPError as e:
            raise NetworkError(f"HTTP error: {e}") from e

    def login(self) -> bool:
        """
        Authenticate with TOBESOFT portal using XML POST request.

        Returns:
            bool: True if authentication successful

        Raises:
            AuthenticationError: If login fails
            NetworkError: If network request fails
        """
        xml_body = self._build_login_xml()

        try:
            response = self.session.post(
                self.config.login_url,
                data=xml_body,
                headers={"Content-Type": "text/xml; charset=UTF-8"},
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()

            # Check if login was successful
            if "SUCCESS" in response.text.upper():
                return True
            else:
                raise AuthenticationError("Login failed: Invalid credentials or response")

        except requests.exceptions.Timeout as e:
            raise NetworkError("Request timeout during login") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError("Connection failed during login") from e
        except requests.exceptions.HTTPError as e:
            raise NetworkError(f"HTTP error during login: {e}") from e

    def request_license_email(self) -> bool:
        """
        Submit license request via GET with query parameters.

        Returns:
            bool: True if request successful

        Raises:
            LicenseRequestError: If request submission fails
            NetworkError: If network request fails
        """
        params = self._build_license_params()

        try:
            response = self.session.get(
                self.config.license_url, params=params, timeout=self.config.request_timeout
            )
            response.raise_for_status()

            # Check if request was successful
            if "FAIL" in response.text.upper():
                raise LicenseRequestError("License request failed")
            elif "SUCCESS" in response.text.upper():
                return True
            else:
                raise LicenseRequestError("License request failed: Unknown response")

        except requests.exceptions.Timeout as e:
            raise NetworkError("Request timeout during license request") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError("Connection failed during license request") from e
        except requests.exceptions.HTTPError as e:
            raise NetworkError(f"HTTP error during license request: {e}") from e

    def _build_login_xml(self) -> str:
        """
        Construct XML body for login POST request.

        Returns:
            str: XML formatted login request body
        """
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Root xmlns="http://www.nexacroplatform.com/platform/dataset">
\t<Parameters>
\t\t<Parameter id="RTYPE">XML</Parameter>
\t\t<Parameter id="DB">CS</Parameter>
\t\t<Parameter id="DBUSER">POTAL_USER</Parameter>
\t</Parameters>
\t<Dataset id="input">
\t\t<ColumnInfo>
\t\t\t<Column id="userId" type="STRING" size="256" />
\t\t\t<Column id="userPass" type="STRING" size="256" />
\t\t</ColumnInfo>
\t\t<Rows>
\t\t\t<Row>
\t\t\t\t<Col id="userId">{self.config.user_id}</Col>
\t\t\t\t<Col id="userPass">{self.config.user_pass}</Col>
\t\t\t</Row>
\t\t</Rows>
\t</Dataset>
</Root>"""
        return xml

    def _build_license_params(self) -> dict[str, str]:
        """
        Construct query parameters for license request.

        Returns:
            Dict mapping parameter names to values
        """
        return {
            "service": "xupservice",
            "domain": "NEXTp",
            "model": "CE_LicenseEMailSend_R01",
            "format": "xml",
            "version": "xplatform",
            "p_ConType": "TECH2",
            "p_Product": "NP14",
            "p_Language": "KOR",
            "p_CustomID": self.config.customer_id,
            "p_Email": self.config.email,
            "p_Merge": "N",
            "zip": "false",
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()
