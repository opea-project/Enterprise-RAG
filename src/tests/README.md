# Testing guidelines
There are two kinds of tests:
1. [unit tests](#unit-tests)
2. [microservices tests](#microservices-tests)

Each group of tests has its own [tox](https://tox.wiki/en/3.27.0/example/pytest.html) environment. Tox is the preffered tool for tests invocation although they might be launched manually using pytest as well.

### Tests Prerequisites
Install required packages:
```
sudo apt install tox docker-buildx
```

### Unit tests

Tests execution:
```
cd src/
tox -e unit
```


### Microservices tests
Tests execution:
```
cd src/
tox -e microservices
```

Apart from the terminal output, microservices tests results will be stored in `src/tests/microservices/allure-results` directory as well.

### Useful information
* In order to change tests environment configuration edit `tox.ini` file.
* You may pass additional parameters to pytest after `--`. Examples:
```
# This will execute all unit tests with names starting from "test_langchain"
tox -e unit -- -k test_langchain
```
* Tox will install test requirements accordingly to `deps` parameter in `tox.ini`. When `tox` is launched, new `.tox` directory is created with the virtualenv containing the dependency packages. If there were no changes in the packages, tox will re-use the same virtualenv that was created before. In order to recreate the virtualenv, pass '-r' option:
```
tox -r -e unit
```
* If you use a new python package in your tests, remember to add it to `requirements.txt` file in `tests/unit/` or `tests/microservices` directory

