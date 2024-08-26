#! /bin/bash

helm install -n system --create-namespace gmc helm
kubectl create ns chatqa
kubectl apply -f $(pwd)/config/samples/chatQnA_$1.yaml
kubectl create deployment client-test -n chatqa --image=python:3.8.13 -- sleep infinity
