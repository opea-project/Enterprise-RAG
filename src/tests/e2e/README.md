# End-to-End (E2E) Testing with Pytest, Tox, and Allure

This project uses **Pytest** to define and run **end-to-end (E2E)** tests, automated via **Tox** and integrated with **Allure** for reporting. E2E tests validate entire user flows or system interactions and are essential for ensuring the system behaves as expected.

## Prerequisites

To run E2E tests, you need the following installed on your system:

- Python
- Tox

Install Tox via pip if not already available:

```bash
pip install tox
```

## Running the Tests

Navigate to the src/tests/ directory and execute:

```
cd src/tests/
tox -e e2e
```

To run specific tests that match a name pattern (using a simple regex), use:

```
tox -e e2e -- -k <regex>
```
Replace <regex> with your search keyword or pattern.


## Allure Integration
We use Allure for test reporting. When tests are run via tox, results are automatically collected and stored in `allure-results` directory (as specified in tox.ini). These results can then be uploaded to Zephyr using the following script:

https://github.com/intel-sandbox/rag-solution-infra/blob/main/tools/upload_test_results_to_zephyr.py


## Project Structure & Best Practices
### Test Location
All E2E tests are stored in the src/tests/ directory. Each module should be named according to the component being tested. Example:

```
test_chatqa.py
test_edp.py
```

This naming convention helps with clarity and maintainability.

### Helpers and Fixtures
Reusable test helpers and setup logic are implemented as Pytest fixtures. Shared fixtures are defined in `src/tests/conftest.py`, while additional utilities can be organized under `src/tests/helpers/`.

Example fixture:

```python
# src/tests/conftest.py

import pytest
from .helpers.guard_helper import GuardHelper

@pytest.fixture(scope="session")
def guard_helper(chatqa_api_helper, fingerprint_api_helper):
    return GuardHelper(chatqa_api_helper, fingerprint_api_helper)
```

## Linking Tests to Zephyr
Each test should be linked to its corresponding Zephyr test case using the @allure.testcase decorator:

```python
import allure

@allure.testcase("IEASG-T82")
def test_in_guard_language(guard_helper):
    # test logic here
```

This ensures traceability between test implementation and test management in Zephyr.

