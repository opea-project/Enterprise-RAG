#!/bin/bash

kubectl get ns chatqa > /dev/null 2>&1 && kubectl delete ns chatqa
kubectl get ns dataprep > /dev/null 2>&1 && kubectl delete ns dataprep
helm status -n system gmc > /dev/null 2>&1 && helm delete -n system gmc
kubectl get crd gmconnectors.gmc.opea.io > /dev/null 2>&1 && kubectl delete crd gmconnectors.gmc.opea.io
