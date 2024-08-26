#! /bin/bash

export CLIENT_POD=$(kubectl get pod -A -l app=client-test -o jsonpath={.items..metadata.name})
export accessUrl=$(kubectl get gmc -n chatqa -o jsonpath="{.items[?(@.metadata.name=='chatqa')].status.accessUrl}")
kubectl exec "$CLIENT_POD" -n chatqa -- curl --no-buffer -s $accessUrl  -X POST  -d '{"text":"How about Nike in 2023?","parameters":{"max_new_tokens":17, "do_sample": true, "streaming":true }}' -H 'Content-Type: application/json'
