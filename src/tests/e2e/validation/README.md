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
tox -e e2e -- --build-config-file=<build configuration file> --credentials-file=<credentials file> -k <regex>
```
* `<build configuration file>` - full path to `config.yaml` file
* `<credentials file>` - full path to `default_credentials.txt` file which contains credentials for admin and user
* `<regex>` - desired test name you want to run

## Allure Integration
We use Allure for test reporting. When tests are run via tox, results are automatically collected and stored in `allure-results` directory (as specified in tox.ini).

## Project Structure & Best Practices
### Test Location
All E2E tests are stored in the src/tests/e2e/validation directory. Each module should be named according to the component being tested. Example:

```
test_chatqa_pipeline.py
test_edp.py
```

This naming convention helps with clariyyty and maintainability.

### Test Data
Any data files required for the tests (such as input files for EDP, long code snippets, or other external assets) should be stored in the `src/tests/e2e/files` directory. This ensures that large or static data is kept separate from the test logic.

### Helpers and Fixtures
Reusable test helpers and setup logic are implemented as Pytest fixtures. Shared fixtures are defined in `src/tests/e2e/conftest.py`, while additional utilities can be organized under `src/tests/e2e/helpers/`.

## Linking Tests to Zephyr
Each test should be linked to its corresponding Zephyr test case using the `@allure.testcase` decorator:

```python
import allure

@allure.testcase("IEASG-T82")
def test_in_guard_language(guard_helper):
    # test logic here
```

This ensures traceability between test implementation and test management in Zephyr.

