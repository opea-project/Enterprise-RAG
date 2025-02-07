# Testing guidelines
There are two kinds of tests:
1. [unit tests](#unit-tests)
2. [microservices tests](#microservices-tests)

Each group of tests has its own [tox](https://tox.wiki/en/3.27.0/example/pytest.html) environment. Tox is the preffered tool for tests invocation although they might be launched manually using pytest as well.

### Tests Prerequisites
In order to be able to run all tests you need to have `tox` and `docker` installed:
```bash
sudo apt install tox
```
For Docker installation, refer to [link](https://docs.docker.com/engine/install/ubuntu/). However, not all tests required all of these libraries (e.g. for unit tests docker is not required) so if you'd like to run just a subset of tests, please refer to the source code.

### Unit tests

Check `tox.ini` for possible environments of unit tests - each microservice has its own environment.
Example Tests execution:
```
cd src/
tox -e embeddings_unit_tests
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
# This will execute all embedding unit tests with names starting from "test_langchain"
tox -e embeddings_unit_tests -- -k test_langchain
```
* Tox will install test requirements accordingly to `deps` parameter in `tox.ini`. When `tox` is launched, new `.tox` directory is created with the virtualenv containing the dependency packages. If there were no changes in the packages, tox will re-use the same virtualenv that was created before. In order to recreate the virtualenv, pass '-r' option, for example:
```
tox -r -e embeddings_unit_tests
```
* If you use a new python package in your tests, remember to add it to `requirements.txt` file in `tests/unit/` or `tests/microservices` directory

