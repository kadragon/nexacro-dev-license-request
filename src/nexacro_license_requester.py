"""
Main entry point for Nexacro license request automation.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-006
"""

import logging
import sys

from src.config import Config
from src.exceptions import AuthenticationError, LicenseRequestError, NetworkError
from src.session_manager import SessionManager


class NexacroLicenseRequester:
    """Orchestrates the Nexacro license request workflow."""

    def __init__(self, config: Config):
        """
        Initialize license requester with configuration.

        Args:
            config: Configuration instance with credentials and settings
        """
        self.config = config
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Configure structured logging with both file and console handlers.

        Returns:
            logging.Logger: Configured logger instance
        """
        from pathlib import Path

        logger = logging.getLogger("NexacroLicenseRequester")
        logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # File handler
        log_file = log_dir / "nexacro_license_request.log"
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_format)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_format)

        # Only add handlers if they don't exist (prevent duplicate handlers)
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def request_license(self) -> bool:
        """
        Execute the complete license request workflow.

        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Starting Nexacro license request workflow")

        try:
            with SessionManager(self.config) as session:
                # Step 1: Establish session
                self.logger.info("Step 1/3: Establishing session")
                cookies = session.establish_session()
                self.logger.info(f"Session established with {len(cookies)} cookies")

                # Step 2: Login
                self.logger.info("Step 2/3: Authenticating")
                session.login()
                self.logger.info(f"Authentication successful for user: {self.config.user_id}")

                # Step 3: Request license
                self.logger.info("Step 3/3: Requesting license")
                session.request_license_email()
                self.logger.info(f"License request submitted successfully for {self.config.email}")

            self._log_request_summary(
                success=True,
                details={
                    "user_id": self.config.user_id,
                    "customer_id": self.config.customer_id,
                    "email": self.config.email,
                },
            )
            return True

        except NetworkError as e:
            self.logger.error(f"Network error during workflow: {e}")
            self._log_request_summary(
                success=False, details={"error": "Network error", "message": str(e)}
            )
            return False

        except AuthenticationError as e:
            self.logger.error(f"Authentication failed: {e}")
            self._log_request_summary(
                success=False, details={"error": "Authentication failed", "message": str(e)}
            )
            return False

        except LicenseRequestError as e:
            self.logger.error(f"License request failed: {e}")
            self._log_request_summary(
                success=False, details={"error": "License request failed", "message": str(e)}
            )
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error during workflow: {e}")
            self._log_request_summary(
                success=False, details={"error": "Unexpected error", "message": str(e)}
            )
            return False

    def _log_request_summary(self, success: bool, details: dict) -> None:
        """
        Log structured summary of request outcome.

        Args:
            success: Whether the request was successful
            details: Dictionary containing request details
        """
        if success:
            self.logger.info(
                "=== LICENSE REQUEST SUCCESS ===\n"
                f"User: {details.get('user_id', 'N/A')}\n"
                f"Customer: {details.get('customer_id', 'N/A')}\n"
                f"Email: {details.get('email', 'N/A')}"
            )
        else:
            self.logger.error(
                "=== LICENSE REQUEST FAILED ===\n"
                f"Error: {details.get('error', 'Unknown')}\n"
                f"Message: {details.get('message', 'No details')}"
            )


def main() -> int:
    """
    Entry point for CLI and GitHub Actions execution.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Load configuration from environment
        config = Config.from_env()
        config.validate()

        # Execute license request
        requester = NexacroLicenseRequester(config)
        success = requester.request_license()

        return 0 if success else 1

    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
