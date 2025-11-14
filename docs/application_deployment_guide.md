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

> [!IMPORTANT]
> Intel® AI for Enterprise RAG only works if your chosen storage class is set as the default.

Verify this before deployment:

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

## Change number of iwatch open descriptors

If the application is deployed with telemetry enabled, it is required to increase number of inotify user instances on every machine from the cluster. To do so, check the current number of users, by running

```sh
sudo sysctl -n fs.inotify.max_user_instances
```

To modify it, run:

```sh
cat <<EOF | sudo tee /etc/sysctl.d/99-enterprise-rag.conf
# Enterprise RAG optimizations
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
fs.file-max = 2097152
vm.max_map_count = 262144
EOF

# Apply sysctl changes
sudo sysctl --system
```

## Installation Steps

1. **Edit the configuration file:**
   - Pick a desired pipeline to run:
     - **ChatQA pipeline**: Available in [config.yaml](../deployment/inventory/sample/config.yaml)
     - **Document Summarization (Docsum) pipeline**: Available in [config_docsum.yaml](../deployment/inventory/sample/config_docsum.yaml)
   - Open chosen configuration file and modify following fields:   
      - `httpProxy` and `httpsProxy` values if you are using proxy
      - `kubeconfig`: path to your kubeconfig file 
      - `FQDN`: Provide the FQDN for the deployment, for example "erag.com"

   - If you have K8s cluster containing nodes with `Gaudi AI accelerator`, please change pipelines section as default pipeline is utilizing CPU:
     
     **For ChatQA pipeline:**
     ```yaml
     pipelines:
        - namespace: chatqa
        samplePath: chatqa/reference-hpu.yaml
        resourcesPath: chatqa/resources-reference-hpu.yaml
        modelConfigPath: chatqa/resources-model-hpu.yaml
        type: chatqa
     ```
     
     **For Docsum pipeline:**
     ```yaml
     pipelines:
        - namespace: docsum
        samplePath: docsum/reference-hpu.yaml
        resourcesPath: docsum/resources-reference-hpu.yaml
        modelConfigPath: chatqa/resources-model-hpu.yaml
        type: docsum
     ```

> [!Note]
> The default LLM for Xeon execution is `casperhansen/llama-3-8b-instruct-awq`.
> This model is publically available. However, if you choose to change the model to the gated/restricted one, remember to adjust `huggingToken` field.
> Refer to the [official Hugging Face documentation](https://huggingface.co/docs/hub/models-gated) for instructions on accessing gated models.

2. **Advanced Configuration:**
   
   For detailed configuration options and advanced settings, refer to the [Advanced Configuration Guide](./advanced_configuration.md).

3. **Run the installation:**
   ```bash
   ansible-playbook -u $USER -K playbooks/application.yaml --tags configure,install -e @<path to chosen config.yaml>
   ```
