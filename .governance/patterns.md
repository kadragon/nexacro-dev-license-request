# Design Patterns: Nexacro License Requester

## Pattern 1: Session Lifecycle Management

### Context
Web automation requiring session cookies and authentication across multiple HTTP requests.

### Pattern
```python
class SessionManager:
    def __init__(self, config: Config):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': '...'})

    def __enter__(self):
        self.establish_session()
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

# Usage
with SessionManager(config) as session:
    session.request_license_email()
```

### Benefits
- Automatic session cleanup
- Clear lifecycle boundaries
- Exception-safe resource management

---

## Pattern 2: Configuration from Environment

### Context
Secure credential management for CI/CD environments.

### Pattern
```python
@dataclass
class Config:
    user_id: str
    user_pass: str

    @classmethod
    def from_env(cls) -> 'Config':
        required = ['NEXACRO_USER_ID', 'NEXACRO_USER_PASS']
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise ValueError(f"Missing: {', '.join(missing)}")
        return cls(user_id=os.getenv('NEXACRO_USER_ID'), ...)
```

### Benefits
- Explicit validation of required variables
- Type-safe configuration object
- Single source of truth

---

## Pattern 3: Retry with Exponential Backoff

### Context
Network requests that may fail transiently.

### Pattern
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except NetworkError as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def establish_session(self):
    # Network call here
    pass
```

### Benefits
- Resilience to transient failures
- Configurable retry strategy
- Clear logging of retry attempts

---

## Pattern 4: Exception Hierarchy for Domain Errors

### Context
Distinguishing different failure modes for appropriate handling.

### Pattern
```python
class NexacroError(Exception):
    """Base exception for all Nexacro-related errors."""
    pass

class NetworkError(NexacroError):
    """Network connectivity or timeout errors."""
    pass

class AuthenticationError(NexacroError):
    """Login or credential errors."""
    pass

class LicenseRequestError(NexacroError):
    """License request submission errors."""
    pass

# Usage
try:
    session.login()
except AuthenticationError:
    # Handle auth failure specifically
    logger.error("Check credentials")
except NetworkError:
    # Handle network issues
    logger.error("Check connectivity")
```

### Benefits
- Precise error handling
- Clear error categorization
- Improved debugging
