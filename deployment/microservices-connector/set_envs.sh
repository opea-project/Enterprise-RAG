#!/bin/bash

HUG_TOKEN=$1 #because he is sad
GMC_MANAGER_IMAGE="localhost:5000/opea/gmcmanager" #notag
GMC_ROUTER_IMAGE="localhost:5000/opea/gmcrouter:latest"


function get_CIDR() {
    kubectl cluster-info dump | grep -oP "$1\K[^,]+" | tr -d '",' | head -n 1
}

cluster_CIDR=$(get_CIDR 'service-cluster-ip-range=')
cluster_IPv4Address=$(get_CIDR 'projectcalico.org/IPv4Address": "')
#ensure you've got proper proxy env's
no_proxy_k8s=$no_proxy,.svc,.svc.cluster.local,.pod.cluster.local,$cluster_CIDR,$cluster_IPv4Address

for yamlfile in $(find config/manifests/ -name '*.yaml' -type f) ; do
    sed -i -E "s#(.*http_proxy:\s*).*#\1 \"${http_proxy}\"#g" $yamlfile
    sed -i -E "s#(.*https_proxy:\s*).*#\1 \"${https_proxy}\"#g" $yamlfile
    sed -i -E "s#(.*no_proxy:\s*).*#\1 \"${no_proxy_k8s}\"#g" $yamlfile
    sed -i -E "s/(HF_TOKEN|HUGGINGFACEHUB_API_TOKEN): \"(.*)\"/\1: \"$HUG_TOKEN\"/g" $yamlfile
done

sed -i -E "s#(repository: ).*#\1$GMC_MANAGER_IMAGE#g" helm/values.yaml
sed -i -E "s#(tag: ).*#\1latest#g" helm/values.yaml #latest hardcode is greatest
sed -i -E "s#(image: ).*#\1$GMC_ROUTER_IMAGE#g" helm/gmc-router.yaml

