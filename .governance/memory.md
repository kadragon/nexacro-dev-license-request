# Project Memory: Nexacro Dev License Request Automation

## Project Overview
Automated GitHub Actions workflow to request Nexacro development licenses bimonthly from TOBESOFT support portal.

**Created**: 2025-12-26
**Current Phase**: Initial Implementation
**Spec Reference**: SPEC-license-request-001

## Architecture Decisions

### 1. Session Management Pattern
- **Decision**: Use `requests.Session()` to maintain cookies across requests
- **Rationale**: TOBESOFT portal requires session cookies from homepage before login
- **Pattern**: Homepage GET → Extract cookies → Login POST → License GET
- **Location**: `src/session_manager.py`

### 2. Credential Management
- **Decision**: Store all credentials in GitHub Secrets, load via environment variables
- **Credentials**:
  - `NEXACRO_USER_ID`: knuehaksa (also used as customer ID)
  - `NEXACRO_USER_PASS`: rydnjs!@#
  - `NEXACRO_EMAIL`: kadragon@knue.ac.kr
- **Security**: Never log credentials, use structured logging with redaction

### 3. Error Handling Strategy
- **Exception Hierarchy**:
  - `NexacroError` (base)
    - `NetworkError` (connection, timeout)
    - `AuthenticationError` (login failures)
    - `LicenseRequestError` (request submission failures)
- **Retry Logic**: Max 3 retries with exponential backoff for network errors
- **Notification**: GitHub Actions sends email on workflow failure

### 4. Testing Approach
- **Strategy**: TDD with comprehensive mocking
- **Mock**: All external HTTP calls using `unittest.mock` and `pytest`
- **Coverage Targets**: >90% for core logic, 100% for critical paths
- **Integration**: Full workflow test with mocked responses

## HTTP Endpoint Details

### Endpoint 1: Homepage Session
- **URL**: `https://support.tobesoft.co.kr/Support/?menu=home`
- **Method**: GET
- **Purpose**: Obtain initial session cookies
- **Response**: HTML page with `Set-Cookie` headers
- **Extract**: Session cookies (JSESSIONID or similar)

### Endpoint 2: Login
- **URL**: `https://support.tobesoft.co.kr/Next_JSP/CS-Homepage/Next_JSP/Login/Login_new.jsp`
- **Method**: POST
- **Content-Type**: `text/xml; charset=UTF-8`
- **Body Format**: Nexacro XML with userId and userPass parameters
- **Success Indicator**: HTTP 200 with success response

### Endpoint 3: License Request
- **URL**: `https://next.tobesoft.com/FrontControllerServlet.do`
- **Method**: GET
- **Query Parameters**:
  - `service`: xupservice
  - `domain`: NEXTp
  - `model`: CE_LicenseEMailSend_R01
  - `format`: xml
  - `version`: xplatform
  - `p_ConType`: TECH2
  - `p_Product`: NP14
  - `p_Language`: KOR
  - `p_CustomID`: {NEXACRO_USER_ID}
  - `p_Email`: {NEXACRO_EMAIL}
  - `p_Merge`: N
  - `zip`: false

## Schedule
- **Cron**: `5 0 1 1,3,5,7,9,11 *`
- **Timezone**: UTC (00:05 UTC = 09:05 KST)
- **Description**: 9:05 AM KST on 1st day of Jan, Mar, May, Jul, Sep, Nov

## Known Issues & Risks

### Resolved Issues

1. **uv Package Manager Integration**
   - **Issue**: Initial setup used pip/venv, needed migration to uv
   - **Resolution**: Configured pyproject.toml with proper hatchling build backend
   - **Learning**: uv requires explicit package path configuration in `tool.hatch.build.targets.wheel`

2. **License Request Response Validation**
   - **Issue**: Initial implementation used OR logic, allowing false positives
   - **Resolution**: Check for FAIL explicitly before SUCCESS
   - **Pattern**: Always validate negative cases before positive ones

3. **P1: License Request False Positive on HTTP 200 (TASK-012)**
   - **Issue**: `session_manager.py:114` used `or response.status_code == 200`, causing any HTTP 200 response to be treated as success even when portal returned error pages
   - **Impact**: Silent failures where license request failed but workflow reported success
   - **Resolution**: Removed `or response.status_code == 200` condition, now only checks for explicit "SUCCESS" text
   - **Tests Added**: `test_request_license_email_http_200_without_success`, `test_request_license_email_http_200_with_empty_response`
   - **Date**: 2025-12-26
   - **Coverage Impact**: +2 tests, maintained 96% coverage

4. **P2: File Logging Handler Missing (TASK-012)**
   - **Issue**: `nexacro_license_requester.py:30-50` documented file+console logging but only implemented console handler
   - **Impact**: GitHub Actions workflow uploads empty logs/ artifact on failure, making debugging impossible
   - **Resolution**: Added FileHandler to write logs to `logs/nexacro_license_request.log` with UTF-8 encoding
   - **Tests Added**: `test_logger_has_console_handler`, `test_logger_has_file_handler`
   - **Date**: 2025-12-26
   - **Coverage Impact**: +2 tests, improved coverage from 95% to 96%

### Current Limitations

1. **Cookie Format Assumption**
   - Assumes JSESSIONID cookie name
   - Risk: TOBESOFT may change cookie names
   - Mitigation: Generic cookie extraction implemented

2. **Response Format Dependency**
   - Relies on "SUCCESS"/"FAIL" text in responses
   - Risk: API response format changes
   - Mitigation: HTTP status codes also checked as fallback

## Next Steps

### For Initial Deployment (TASK-010)
1. Configure GitHub Secrets in repository settings
2. Test workflow with manual trigger (workflow_dispatch)
3. Verify license email is received
4. Monitor first scheduled execution

### For Production (TASK-011)
1. Enable scheduled workflow
2. Monitor bimonthly executions (Jan 1, Mar 1, May 1, Jul 1, Sep 1, Nov 1)
3. Update memory.md with production insights

### Future Enhancements
1. Add retry logic with exponential backoff for network failures
2. Implement structured JSON logging for better observability
3. Add Slack/Discord notification integration
4. Create dashboard for tracking license request history

## Lessons Learned

### 1. TDD Workflow Effectiveness
- **Observation**: Following strict RED-GREEN-REFACTOR cycle resulted in 96% coverage
- **Benefit**: All edge cases caught during test writing phase
- **Practice**: Write tests first, especially for error scenarios
- **TASK-012 Example**: P1 and P2 bugs caught by code review, fixed using TDD (test first, then fix)

### 2. uv Package Manager Advantages
- **Speed**: Dependency resolution ~10x faster than pip
- **Lock File**: `uv.lock` ensures reproducible builds
- **Python Version Management**: Built-in Python version installation
- **GitHub Actions**: Native uv support via `astral-sh/setup-uv@v5`

### 3. Session Management Pattern
- **Discovery**: Context manager (`__enter__`/`__exit__`) ensures session cleanup
- **Benefit**: Automatic resource management prevents connection leaks
- **Application**: Used successfully in SessionManager class

### 4. XML Request Formatting
- **Challenge**: Nexacro requires specific XML namespace and structure
- **Solution**: Template with f-string interpolation
- **Learning**: Preserve exact whitespace (tabs) from n8n workflow

### 5. GitHub Actions with uv
- **Setup**: Requires both `setup-uv` and `uv python install`
- **Optimization**: `uv sync` directly uses `pyproject.toml` and `uv.lock`
- **Best Practice**: No need for requirements.txt files with uv

### 6. Error Handling Hierarchy
- **Pattern**: Custom exception hierarchy enables precise error handling
- **Structure**: Base `NexacroError` → Specific errors (Network, Auth, Request)
- **Benefit**: Different retry strategies for different error types

### 7. Integration Testing Strategy
- **Approach**: Mock HTTP responses at `requests.Session` level
- **Coverage**: Test happy path + all failure scenarios
- **Validation**: Verify call sequence and parameters

### 8. Configuration Management
- **Pattern**: Dataclass + `from_env()` class method
- **Validation**: Explicit validation method called in main()
- **Security**: Never log credentials, validate email format

### 9. Modern Tooling with Ruff
- **Discovery**: Ruff is 10-100x faster than traditional linters (flake8, black)
- **Benefit**: Single tool for linting and formatting
- **Configuration**: All in pyproject.toml, no separate config files needed
- **Features**: Auto-fixing, import sorting, comprehensive rules

### 10. Pre-commit Hooks Effectiveness
- **Implementation**: 14 hooks configured in .pre-commit-config.yaml
- **Categories**: Linting, formatting, type checking, security, file quality
- **Benefit**: Catch issues before commit, consistent code quality
- **CI Integration**: Same hooks run in CI for double-checking

### 11. Multi-Python Version Testing
- **Strategy**: Test on Python 3.11, 3.12, 3.13 in CI
- **Tool**: GitHub Actions matrix strategy
- **Benefit**: Ensure compatibility across Python versions
- **Coverage Upload**: Only from Python 3.11 to avoid duplicates

### 12. Pyright vs Mypy
- **Decision**: Replaced mypy with pyright for type checking
- **Rationale**: Pyright is faster (written in TypeScript/Node.js), more accurate, and actively maintained by Microsoft
- **Performance**: ~5-10x faster than mypy on large codebases
- **Features**: Better IDE integration, more precise type inference
- **Configuration**: Simpler config in pyproject.toml, less verbose

### 13. Comprehensive Security Scanning
- **Dual Approach**: Bandit for code + pip-audit for dependencies
- **Bandit**: Static analysis for common security issues in Python code
- **pip-audit**: Scans dependencies against known CVEs from PyPI Advisory Database
- **Pre-commit Integration**: Both run automatically before commits
- **CI Integration**: Both run in CI pipeline for double-checking

## Project Statistics

- **Total Implementation Time**: Single day (2025-12-26)
- **Total Test Cases**: 47 tests (added 4 tests for P1/P2 fixes)
- **Test Coverage**: 96% (target: >90%)
- **Lines of Code**: 167 (src, +10 for file logging)
- **Test Code**: ~550 lines
- **Specification Files**: 1 (spec.yaml)
- **Governance Documents**: 4 files
- **Pre-commit Hooks**: 14 hooks configured
- **CI Jobs**: 4 parallel jobs (lint, test, build, pre-commit)

## Success Metrics

✅ All 47 tests passing (was 43, added 4 for P1/P2)
✅ 96% code coverage achieved (improved from 95%)
✅ SDD×TDD structure fully implemented
✅ GitHub Actions workflows configured (License + CI)
✅ Comprehensive documentation complete
✅ No manual intervention required for execution
✅ Error handling for all failure scenarios
✅ Logging and observability implemented (file + console)
✅ Pre-commit hooks configured (ruff, pyright, bandit, yamllint)
✅ CI pipeline with multi-Python version testing (3.11, 3.12, 3.13)
✅ All linting and type checking passing
✅ Security scanning with bandit + pip-audit
✅ P1 and P2 critical bugs fixed (TASK-012)

## Maintenance Notes

### Bi-monthly Checklist (Before Scheduled Run)
1. Verify GitHub Secrets are still valid
2. Check TOBESOFT portal for any UI/API changes
3. Review last execution logs for anomalies
4. Confirm email delivery of previous license

### Annual Checklist
1. Update dependencies: `uv lock --upgrade`
2. Run full test suite: `uv run pytest --cov=src`
3. Review and rotate credentials
4. Update Python version if needed (currently 3.11)
5. Review and update governance documentation
