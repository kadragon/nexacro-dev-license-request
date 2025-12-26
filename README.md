# Nexacro Development License Request Automation

Automated GitHub Actions workflow to request Nexacro development licenses bimonthly from the TOBESOFT support portal.

## Overview

**Schedule**: 9:05 AM KST on the 1st day of January, March, May, July, September, and November
**Method**: Python script using `requests` library and `uv` package manager
**Notification**: GitHub Actions email on failure
**Test Coverage**: 95%
**Code Quality**: Ruff linter + formatter, Pyright type checker, Bandit + pip-audit security
**CI/CD**: GitHub Actions with 15 pre-commit hooks

## Project Structure

```
nexacro-dev-license-request/
├── .spec/              # Feature specifications (SDD)
├── .tasks/             # Task management (backlog, current, done)
├── .governance/        # Project memory and conventions
├── .github/workflows/  # GitHub Actions workflows
├── src/                # Python source code
│   ├── config.py                    # Configuration management
│   ├── session_manager.py           # HTTP session & authentication
│   ├── nexacro_license_requester.py # Main orchestrator
│   └── exceptions.py                # Custom exceptions
├── tests/              # Test suite (TDD)
│   ├── test_config.py
│   ├── test_session_manager.py
│   ├── test_license_requester.py
│   └── test_integration.py
├── pyproject.toml      # Project configuration & dependencies
└── uv.lock             # Locked dependencies
```

## Features

- Automated bimonthly license requests
- Session management with cookie handling
- XML-based authentication
- Comprehensive error handling
- 95% test coverage
- Structured logging
- GitHub Actions integration with uv package manager
- Pre-commit hooks for code quality (ruff, pyright, bandit, pip-audit)
- Automated CI/CD pipeline with multi-Python version testing
- Dual security scanning: bandit (code) + pip-audit (dependencies)

## Setup Instructions

### 1. Configure GitHub Secrets

Navigate to repository Settings → Secrets and variables → Actions, and add:

- `NEXACRO_USER_ID`: Your TOBESOFT portal user ID (also used as customer ID for license request) (knuehaksa)
- `NEXACRO_USER_PASS`: Your TOBESOFT portal password
- `NEXACRO_EMAIL`: Email address for license delivery (kadragon@knue.ac.kr)

### 2. Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd nexacro-dev-license-request

# Install uv if not already installed
# See: https://docs.astral.sh/uv/getting-started/installation/

# Install dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Create .env file for local testing (DO NOT COMMIT)
cat > .env <<EOF
NEXACRO_USER_ID=your_user_id
NEXACRO_USER_PASS=your_password
NEXACRO_EMAIL=your_email@example.com
EOF
```

### 3. Code Quality Tools

```bash
# Run linter
uv run ruff check src tests

# Run formatter
uv run ruff format src tests

# Run type checker (Pyright - faster than mypy)
uv run pyright src

# Run security code scanner
uv run bandit -c pyproject.toml -r src

# Run dependency vulnerability scanner
uv run pip-audit --skip-editable

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

### 4. Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test category
uv run pytest tests/test_session_manager.py -v
```

### 5. Manual Execution

```bash
# Local testing
uv run python -m src.nexacro_license_requester

# GitHub Actions manual trigger
# Go to Actions → Request Nexacro Development License → Run workflow
```

## Development Workflow (SDD × TDD)

This project follows **Spec-Driven Development (SDD)** and **Test-Driven Development (TDD)**:

1. **Specifications** in `.spec/` define WHAT should be built
2. **Tasks** in `.tasks/` define WHEN and WHAT NEXT
3. **Governance** in `.governance/` stores HOW and WHY

### Adding New Features

1. Create specification in `.spec/feature-name/spec.yaml`
2. Add tasks to `.tasks/backlog.yaml` referencing the spec
3. Write tests first (RED)
4. Implement code to pass tests (GREEN)
5. Refactor while keeping tests green
6. Update `.governance/memory.md` with learnings

## Architecture

### HTTP Request Flow

1. **Session Establishment**
   - GET `https://support.tobesoft.co.kr/Support/?menu=home`
   - Extract session cookies (JSESSIONID)

2. **Authentication**
   - POST `https://support.tobesoft.co.kr/Next_JSP/CS-Homepage/Next_JSP/Login/Login_new.jsp`
   - Content-Type: `text/xml; charset=UTF-8`
   - XML body with Nexacro-specific parameters

3. **License Request**
   - GET `https://next.tobesoft.com/FrontControllerServlet.do`
   - Query parameters:
     - `service`: xupservice
     - `model`: CE_LicenseEMailSend_R01
     - `p_Product`: NP14
     - `p_CustomID`: Customer ID
     - `p_Email`: Email for delivery

### Error Handling

- `NetworkError`: Connection or timeout issues
- `AuthenticationError`: Login failures
- `LicenseRequestError`: Request submission failures
- Automatic logging of all errors
- GitHub Actions email notification on failure

## Monitoring

- **Workflow Runs**: Check Actions tab for execution history
- **Logs**: Download workflow logs for debugging
- **Notifications**: Email sent on workflow failure
- **Artifacts**: Logs preserved for 30 days on failure

## Maintenance

- **Credential Rotation**: Update GitHub Secrets as needed
- **Schedule Adjustment**: Modify cron in `.github/workflows/request-license.yml`
- **Dependency Updates**: Run `uv lock --upgrade` regularly
- **Test Coverage**: Maintain >90% coverage

## GitHub Actions Workflow

The workflow runs automatically on schedule and can be triggered manually:

```yaml
on:
  schedule:
    - cron: '5 0 1 1,3,5,7,9,11 *'  # 9:05 AM KST
  workflow_dispatch:  # Manual trigger
```

**Features**:
- Uses `uv` for fast dependency installation
- Python 3.11 runtime
- 10-minute timeout
- Automatic log upload on failure
- Secure credential management via GitHub Secrets

## Traceability

All code references:
- `spec_id`: Links to specification in `.spec/`
- `task_id`: Links to task in `.tasks/`

## Testing

Test suite includes:
- **Unit tests**: Individual component testing
- **Integration tests**: Full workflow testing
- **Error handling tests**: Failure scenario testing
- **Coverage**: 95% (target: >90%)
- **CI**: Automated testing on Python 3.11, 3.12, 3.13

## Technologies

### Core
- **Python**: 3.11+ (tested on 3.11, 3.12, 3.13)
- **Package Manager**: uv (fast, modern Python package manager)
- **HTTP Client**: requests

### Development
- **Testing**: pytest, pytest-cov, pytest-mock
- **Linting**: ruff (replaces flake8, isort, pyupgrade)
- **Formatting**: ruff format
- **Type Checking**: pyright (faster and more accurate than mypy)
- **Security**: bandit (code), pip-audit (dependencies)
- **Pre-commit**: 15 hooks for code quality

### CI/CD
- **GitHub Actions**: Multi-job CI pipeline
  - Lint and type check
  - Test on Python 3.11, 3.12, 3.13
  - Package build verification
  - Pre-commit hooks validation
- **Configuration**: python-dotenv

## License

[Your License Here]

## Contact

- Email: kadragon@knue.ac.kr
- Project Maintainer: kadragon
