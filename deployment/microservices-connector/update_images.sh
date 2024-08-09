#!/bin/bash
make build
make docker.build

docker run -d -p 5000:5000 --name local-registry registry:2
docker tag opea/gmcmanager:latest localhost:5000/opea/gmcmanager:latest
docker push localhost:5000/opea/gmcmanager:latest
docker tag opea/gmcrouter:latest localhost:5000/opea/gmcrouter:latest
docker push localhost:5000/opea/gmcrouter:latest
