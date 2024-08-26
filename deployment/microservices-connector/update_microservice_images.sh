#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# not pretty , but this is tmp script
cd ../../src/comps/embeddings/impl/model-server/torchserve && \
docker build -f docker/Dockerfile . -t pl-qna-rag-embedding-torchserve --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg no_proxy=localhosti && \
cd -

docker tag pl-qna-rag-embedding-torchserve:latest localhost:5000/test/pl-qna-rag-embedding-torchserve:latest
docker push localhost:5000/test/pl-qna-rag-embedding-torchserve:latest

cd ../../src && \
docker build -t test/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/redis/docker/Dockerfile . && \
cd -

docker tag test/retriever-redis:latest localhost:5000/test/retriever-redis:latest
docker push localhost:5000/test/retriever-redis:latest

cd ../../src && \
docker build -t test/embedding-test-langchain:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/impl/microservice/Dockerfile --target langchain . && \
cd -

docker tag test/embedding-test-langchain:latest localhost:5000/test/embedding-test-langchain:latest
docker push localhost:5000/test/embedding-test-langchain:latest
