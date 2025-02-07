## Microservices validation tests

### How to run

Before start, ensure you have `HF_TOKEN` in your `env`. The token will be further passed to containers
to pull AI models.
```bash
$ echo ${HF_TOKEN}
abcdefghi1234567890 
```

Additionally, prepare Python virtual environment and install deps. The simplest way is:
```bash
$ pwd
.../src/tests/microservices

$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -U pip
(venv) $ pip install -r requirements.txt
```

Decide on which tests groups to run. They can be filtered out with `-m MARKSEXPR` flag. Tests are marked to categorize.
See all marks in [pytest.ini](../pytest.ini).

Examples:
- `-m "vllm and hpu"` - run vllm tests for Gaudi (lit. marked as vllm and hpu)
- `-m "embeddings or dataprep"` - run tests for embeddings and dataprep (lit. marked as embeddings or dataprep)

More about this marker filters on [Pytest docs](https://docs.pytest.org/en/stable/example/markers.html#marking-test-functions-and-selecting-them-for-a-run)

Some of the tests have combinations of parameters. Ensure you are okay with them by dry-running first.
Add flag `--collect-only` to see tests that are about to run.
If you want to apply additional filtering, use `-k FILTERSEXPR` flag. This will apply filtering by test name (works like `grep`).

Example:
`-m "llms and hpu" -k "golden"` - run llms tests for Gaudi only with golden (default, recommended) settings.

More about this name filters on [Pytest docs](https://docs.pytest.org/en/stable/example/markers.html#using-k-expr-to-select-tests-based-on-their-name)

Then, run pytest:
```bash
(venv) $ pytest -m "llms and hpu" -k "golden"
```
