#!/bin/bash

kubectl delete ns chatqa
kubectl delete -k config/samples/
helm delete -n system gmc
kubectl delete crd gmconnectors.gmc.opea.io

