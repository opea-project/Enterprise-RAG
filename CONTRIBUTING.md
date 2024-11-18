# Contributing

## Table of Contents
1. [License](#license)
2. [Sign your work](#sign-your-work)
3. [Local linting](#local-linting)

### License

Intel(R) AI for Enterprise RAG is licensed under the terms in [LICENSE](LICENSE). 
By contributing to the project, you agree to the license and copyright terms therein
and release your contribution under these terms.

### Sign your work

Please use the sign-off line at the end of the patch. Your signature certifies 
that you wrote the patch or otherwise have the right to pass it on as an 
open-source patch. The rules are pretty simple: if you can certify
the below (from [developercertificate.org](http://developercertificate.org/)):

```
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
660 York Street, Suite 102,
San Francisco, CA 94110 USA

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.

Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

Then you just add a line to every git commit message:

    Signed-off-by: Joe Smith <joe.smith@email.com>

Use your real name (sorry, no pseudonyms or anonymous contributions.)

If you set your `user.name` and `user.email` git configs, you can sign your
commit automatically with `git commit -s`.

### Local linting

This project utilizes [Super-Linter](https://github.com/super-linter/super-linter) to run as a Github Action for Pull Requests. If you would like to check before pushing your changes whether they comply with the linter's rules, you can run the linter locally.

#### Prerequisites
In order to run Super-Linter, you need to have Docker installed. Follow the instructions to install it on you machine: [docker installation](https://docs.docker.com/engine/install/).
#### Running the linter
To run Super-Linter, perform following command. It will work only on commited changes diffed against the main branch, so be sure to commit locally all of the changes you'd like to check. If you'd like to run the linter for all of the code, change `VALIDATE_ALL_CODEBASE` to `true`.
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