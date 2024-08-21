### Microservices tests prerequisites
Install tox
```
sudo apt install tox
```

### How to run the tests
Go to microservices tests directory and execute tox
```
cd src/tests/microservices
tox
```
You can add additional parameters to `tox` command - they will be passed to `pytest` command respectively. Example:
```
# This will run only a single test file
tox -- test_reranks_tei.py
```

