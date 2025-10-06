# Intel® AI for Enterprise RAG Application Deployment Guide

This document describes how to install Intel® AI for Enterprise RAG application on K8s cluster.

## Checking all pods are in running state

**Verify System Status**

   Before proceeding, run the following command:
   ```bash
   kubectl get pods -A
   ```

   and make sure all pods are in running state.

## Checking Your Default Storage Class

**Critical**: Intel® AI for Enterprise RAG only works if your chosen storage class is set as the default. Verify this before deployment:

```bash
# Check current default storage class
kubectl get storageclass

# Look for one marked with (default)
NAME                 PROVISIONER                    RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path           rancher.io/local-path          Delete          WaitForFirstConsumer   false                  5d
nfs-csi (default)    nfs.csi.k8s.io                 Delete          Immediate              false                  2d

# If your desired storage class is not default, set it:
kubectl patch storageclass <your-storage-class-name> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Remove default from other storage classes if needed:
kubectl patch storageclass <other-storage-class> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

## Installation Steps

1. **Edit the configuration file:**
   - Open `inventory/test-cluster/config.yaml`
   - Fill in the required values:
     - `huggingToken` - Your Hugging Face API token
> [!Note]
> The default LLM for Xeon execution is `casperhansen/llama-3-8b-instruct-awq`.
> Ensure your HUGGINGFACEHUB_API_TOKEN grants access to this model.  
> Refer to the [official Hugging Face documentation](https://huggingface.co/docs/hub/models-gated) for instructions on accessing gated models.
     - `httpProxy` and `httpsProxy` values if you are using proxy
     - `kubeconfig`: path to your kubeconfig file 
     - `FQDN`: Provide the FQDN for the deployment, for example "erag.com"

     - If you have K8s cluster containing nodes with `Gaudi AI accelerator`, please change pipelines section as default pipeline is utilizing CPU:
     ```
     pipelines:
       - namespace: chatqa
         samplePath: chatqa/reference-hpu.yaml
         resourcesPath: chatqa/resources-reference-hpu.yaml
         modelConfigPath: chatqa/resources-model-hpu.yaml
         type: chatqa
         ```
2. **Advanced Configuration:**
   
   For detailed configuration options and advanced settings, refer to the [Advanced Configuration Guide](./advanced_configuration.md).

3. **Run the installation:**
   ```bash
   ansible-playbook -u $USER -K playbooks/application.yaml --tags configure,install -e @inventory/test-cluster/config.yaml
   ```
