# EDP benchmarks

### Prerequisites

Place benchmark files into `src/tests/e2e/benchmarks/edp/files` directory
Categorize into subfolders with `src/tests/e2e/benchmarks/edp/files/categorize.sh`
Test is matching datesets names like `simple_small` with subdirs and picks
all files from this subdir.

### Running benchmarks

See available tests with `tox -e benchmark_edp -- --collect-only`

Run tests with `tox -e benchmark_edp`

Run filtered tests with `tox -e benchmark_edp -- -k <test_name>`

### Results

Results are available in `src/tests/e2e/benchmarks/edp/results` directory.
There are CSVs and JSONs.
