# Intel® AI for Enterprise RAG Application Deployment Guide

This document describes how to install Intel® AI for Enterprise RAG application on K8s cluster.

## Version Management and Upgrades

Intel® AI for Enterprise RAG includes version tracking and upgrade validation:
- The solution tracks deployed versions via a deployment manifest stored in the cluster.
- Upgrades to newer versions are supported and validated before execution.
- Downgrades are blocked by default to prevent data loss and compatibility issues.
   - In cases when downgrade is a necessity, it's possible to force installation mode by enabling the *forced installation mode* with parameter: `-e force_install_mode=true`.
- Version checks occur automatically during deployment to ensure compatibility.

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

## System Limits Configuration

> [!NOTE]
> System limits are automatically configured when using the `pre-install` or `install` tag during infrastructure. Manual configuration is only needed if you're not using the playbooks or want to verify the settings.

If the application is deployed with telemetry enabled, it is required to increase number of inotify user instances on every machine from the cluster. These limits are automatically applied using:

```sh
# For infrastructure deployment
ansible-playbook -K playbooks/infrastructure.yaml --tags pre-install -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
```

To manually verify or configure the limits, check the current number:

```sh
sudo sysctl -n fs.inotify.max_user_instances
```

To manually modify it, run:

```sh
cat <<EOF | sudo tee /etc/sysctl.d/99-enterprise-rag.conf
# Enterprise RAG optimizations
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
fs.file-max = 2097152
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

     **To enable AudioQnA solution for ChatQnA pipelines**, set the `audio.enabled` field to `true`:
     ```yaml
     audio:
       enabled: true
       namespace: audio
       asr_model: "openai/whisper-small"
       tts_model: "microsoft/speecht5_tts"
     ```

     For more details about AudioQnA configuration, see the [Advanced Configuration Guide](./advanced_configuration.md#audioqna-solution).

    - If you are deploying on `Intel® Arc™ B-Series (XPU)`, use XPU pipeline references and ensure these config settings are present:
    
       > [!WARNING]
       > **Intel® Arc™ B-Series (XPU/Battlemage) support is experimental** and intended for testing and evaluation purposes only. Not recommended for production use.
       
       - `is_bmg_platform_enable: true`
       - `intel_gpu_plugin: true` (if plugin is not already installed in cluster)
       - `minimal_configuration: true` for constrained single-user setups (32 logical cores / 64 GB RAM)

       **For ChatQA pipeline on XPU:**
       ```yaml
       pipelines:
          - namespace: chatqa
             samplePath: chatqa/reference-xpu.yaml
             resourcesPath: chatqa/resources-reference-xpu.yaml
             modelConfigPath: chatqa/resources-model-xpu.yaml
             type: chatqa
       ```

       **For Docsum pipeline on XPU:**
       ```yaml
       pipelines:
          - namespace: docsum
             samplePath: docsum/reference-xpu.yaml
             resourcesPath: docsum/resources-reference-xpu.yaml
             modelConfigPath: chatqa/resources-model-xpu.yaml
             type: docsum
       ```

> [!Note]
> The default LLM for Xeon execution is `casperhansen/llama-3-8b-instruct-awq`.
> This model is publicly available. However, if you choose to change the model to the gated/restricted one, remember to adjust `huggingToken` field.
> Refer to the [official Hugging Face documentation](https://huggingface.co/docs/hub/models-gated) for instructions on accessing gated models.

> [!Note]
> If application will be deployed on Nutanix Kubernetes Platform (NKP), it is recommended to disable telemetry, as it 
> might collide with existing telemetry on NKP. You can do that by changing `enabled` field in `telemetry` section in chosen pipeline config


2. **Advanced Configuration:**
   
   For detailed configuration options and advanced settings, refer to the [Advanced Configuration Guide](./advanced_configuration.md).

3. **Run the installation:**
   ```bash
   ansible-playbook -u $USER -K playbooks/application.yaml --tags configure,install -e @<path to chosen config.yaml>
   ```

   For Intel® Arc™ B-Series deployments (experimental, testing purposes only), append:

   ```bash
   -e is_bmg_platform=true
   ```

   Example:

   ```bash
   ansible-playbook -u $USER -K playbooks/application.yaml --tags configure,install -i inventory/localhost/inventory.ini -e @inventory/localhost/config_minimal.yaml -e is_bmg_platform=true
   ```

   > [!NOTE]
   > For XPU deployments, ensure your config sets `is_bmg_platform_enable: true`, `llm_model_xpu`, and the appropriate XPU pipeline references. See [deployment/README.md](../deployment/README.md) for the full list of required changes.
