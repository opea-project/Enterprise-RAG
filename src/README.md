# Adding new microservices and tests
## Expected structure

This structure must be followed:

src/comps/MICROSERVICE/VENDOR/SUBVENDOR/ where
`
MICROSERVICE is service name,
VENDOR is a specific vendor and
SUBVENDOR (optional) is a vendor different version or different component from vendor
`

Example: src/comps/dataprep/redis/langchain

Also a bash script test *MUST* exist in src/tests, following this structure "test_MICROSERVICE_VENDOR_SUBVENDOR.sh". This is important so CI/CD can know which test run.

Example: src/tests/test_dataprep_redis_langchain.sh

## Expected test script behavior

OPEA follows a structure when creating a test which follow these rules:
- Must be a bash script, *.sh
- Every container started inside a script must contain this prefix name: "test-comps-MICROSERVICE-VENDOR-SUBVENDOR-*" so CI/CD can clean up them when finished and avoid having orphan containers or remnants in gaudi clusters. [Example](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/86f6aba4cc43e0b066b7f5aae40ba165c0001277/src/tests/test_embeddings_llama_index.sh#L10)
- Logs must be created during execution of tests with extensions .log and placed under ./tests so CI/CD can pick them and upload them in github actions. [Example](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/86f6aba4cc43e0b066b7f5aae40ba165c0001277/src/tests/test_embeddings_llama_index.sh#L46)

## ARs
Although OPEA has a similar structure those rules are not followed and there is some work to do to be compliant with them.
- [ ] Revisit all src/tests scripts and verify names follow expected structure rule, some bash script dont't match with microservice name in src/comps.
- [ ] Revisist all src/tests scripts and verify expected test script behavior is followed. I did a quick verification and not even half of them follow these rules so we need to change them.
- [ ] Also notice some tests are not working at all (missing dependencies, typos, etc) so we may need to fix them too.