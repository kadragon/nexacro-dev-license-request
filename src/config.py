"""
Configuration management for Nexacro license requester.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-004
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration container for license requester."""

    user_id: str
    user_pass: str
    customer_id: str
    email: str

    # URLs
    homepage_url: str = "https://support.tobesoft.co.kr/Support/?menu=home"
    login_url: str = (
        "https://support.tobesoft.co.kr/Next_JSP/CS-Homepage/Next_JSP/Login/Login_new.jsp"
    )
    license_url: str = "https://next.tobesoft.com/FrontControllerServlet.do"

    # Timeouts
    request_timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "Config":
        """
        Load configuration from environment variables.

        Returns:
            Config: Configuration instance with values from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = [
            "NEXACRO_USER_ID",
            "NEXACRO_USER_PASS",
            "NEXACRO_EMAIL",
        ]

        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        user_id = os.environ["NEXACRO_USER_ID"]
        return cls(
            user_id=user_id,
            user_pass=os.environ["NEXACRO_USER_PASS"],
            customer_id=user_id,
            email=os.environ["NEXACRO_EMAIL"],
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration values are invalid
        """
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid email format: {self.email}")
