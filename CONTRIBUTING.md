# Contributing Guidelines

Thank you for your interest in contributing to our project! We welcome contributions from the community to help improve our application. Please take a moment to review the guidelines below before submitting your contribution.

# Table of Contents
1. [Local linting](#local-linting)

### Local linting

This project utilizes [Super-Linter](https://github.com/super-linter/super-linter) to run as a Github Action for Pull Requests. If you would like to check before pushing your changes whether they comply with the linter's rules, you can run the linter locally.

#### Prerequisites
In order to run Super-Linter, you need to have Docker installed. Follow the instructions to install it on you machine: [docker installation](https://docs.docker.com/engine/install/).

#### Running the linter
To run Super-Linter, perform following command. It will work only on commited changes diffed against the main branch, so be sure to commit locally all of the changes you'd like to check. If you'd like to run the linter for all of the code, change `VALIDATE_ALL_CODEBASE` to true.

```bash

docker run \
  -e LOG_LEVEL=DEBUG \
  -e VALIDATE_ALL_CODEBASE=false \
  -e VALIDATE_BASH=true \
  -e BASH_SEVERITY=error \
  -e FILTER_REGEX_EXCLUDE=".*helm/templates/.*.yaml" \
  -e VALIDATE_YAML=true \
  -e VALIDATE_PYTHON_RUFF=true \
  -e VALIDATE_DOCKERFILE_HADOLINT=true \
  -e DEFAULT_BRANCH=main \
  -e RUN_LOCAL=true \
  -e SAVE_SUPER_LINTER_SUMMARY=true \
  -e SAVE_SUPER_LINTER_OUTPUT=true \
  -v .:/tmp/lint \
  --rm \
  ghcr.io/super-linter/super-linter:slim-v6.8.0
```

For more information on running Super-Linter locally, follow [link](https://github.com/super-linter/super-linter/blob/main/docs/run-linter-locally.md).