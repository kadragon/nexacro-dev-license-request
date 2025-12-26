# Coding Style Guide: Nexacro License Requester

## General Principles
- **Language**: Python 3.11+
- **Style Guide**: PEP 8 with 100-character line limit
- **Type Hints**: Mandatory for all function signatures
- **Docstrings**: Google-style for all public methods

## Python Conventions

### Imports
```python
# Standard library imports first
import os
import logging
from typing import Dict, Optional

# Third-party imports second
import requests
import pytest

# Local imports last
from config import Config
from session_manager import SessionManager
```

### Naming Conventions
- **Classes**: PascalCase (`SessionManager`, `Config`)
- **Functions/Methods**: snake_case (`establish_session`, `request_license`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`, `REQUEST_TIMEOUT`)
- **Private Methods**: Prefix with underscore (`_build_login_xml`)

### Error Handling
```python
# Always use specific exception types
try:
    response = self.session.get(url, timeout=self.config.request_timeout)
    response.raise_for_status()
except requests.exceptions.Timeout as e:
    raise NetworkError(f"Request timeout: {url}") from e
except requests.exceptions.ConnectionError as e:
    raise NetworkError(f"Connection failed: {url}") from e
```

### Logging
```python
# Use structured logging with context
logger.info(
    "License request submitted",
    extra={
        "customer_id": config.customer_id,
        "email": config.email,
        "timestamp": datetime.utcnow().isoformat()
    }
)

# Never log credentials
logger.debug(f"Authenticating user: {config.user_id}")  # OK
logger.debug(f"Password: {config.user_pass}")  # NEVER DO THIS
```

### Type Hints
```python
from typing import Dict, Optional

def extract_cookies(self, response: requests.Response) -> Dict[str, str]:
    """Extract cookies from response headers."""
    pass

def request_license(self) -> bool:
    """Execute license request workflow."""
    pass
```

## Testing Conventions

### Test Structure
```python
class TestSessionManager:
    """Group related tests in classes."""

    def test_specific_behavior_success(self):
        """Test names describe specific behavior and expected outcome."""
        pass

    def test_specific_behavior_failure(self):
        """Each failure mode gets its own test."""
        pass
```

### Fixtures
```python
@pytest.fixture
def mock_config() -> Config:
    """Provide test configuration."""
    return Config(
        user_id="test_user",
        user_pass="test_pass",
        customer_id="test_customer",
        email="test@example.com"
    )
```

### Mocking
```python
# Prefer patch as context manager
with patch.object(session_manager.session, 'get') as mock_get:
    mock_get.return_value = Mock(status_code=200)
    result = session_manager.establish_session()
    assert result is not None
```

## File Organization

### Module Header
```python
"""
Module description here.

Trace:
  spec_id: SPEC-license-request-001
  task_id: TASK-XXX
"""
```

### Class Organization
1. Class docstring
2. `__init__` method
3. Public methods (alphabetically)
4. Private methods (alphabetically)
