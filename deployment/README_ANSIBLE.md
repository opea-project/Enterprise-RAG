# Deploy Intel&reg; AI for Enterprise RAG via Ansible (Preview)

⚠️ **Please note that this deployment method is currently in PREVIEW and is not yet fully supported for production use.**

## Prerequisites

### Setting Up a Python Virtual Environment

```bash
sudo apt-get install python3-venv
python3 -m venv erag-venv
source erag-venv/bin/activate
pip install --upgrade pip
```

> **NOTE**: If you open a new terminal window, don't forget to activate your virtual environment using `source` command.

### Install Dependencies and Ansible Collections

The following commands assume you are in the deployment directory:
```bash
cd deployment
```

Then, install the required dependencies:
```bash
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yaml --upgrade
```

> **NOTE**: If you encounter an error such as `ERROR: Ansible could not initialize the preferred locale`, it means the system’s locale settings are either not properly configured or not supported by Ansible. To resolve this issue, set the correct locale by running the following command: `export LC_ALL=C.UTF-8`. After applying the fix, retry running the `ansible-galaxy` command.

### Create ansible-vault password file

Prepare file with your ansible-vault password that will be used to encrypt auto-generated password:

```bash
echo "HERE_PUT_YOUR_PASSWORD" > vault.txt
```
**Important**: The path to this `vault.txt` file will be needed later in the configuration process (in the config.yaml file), so make sure to keep it accessible.

If you need to manually access or view encrypted passwords later, you can use the `ansible-vault view` command. For more details about credentials, refer to the section below [Logs and credentials](#logs-and-credentials).

### Create your configuration file

Copy the configuration file sample directory:
```bash
cp -r inventory/sample inventory/test-cluster
```

Next,
- edit `inventory/test-cluster/config.yaml` to configure your setup by adding the Hugging Face token, proxy settings, vault password file, kubeconfig path and defining the pipeline.

#### Cleaning Up Istio CRDs

Due to changes in ownership metadata for Istio CRDs, manual removal is required.

To verify if there is any Istio CRDs already on your setup, list them with the following command:
```bash
kubectl get crds | grep istio.io # for verification if crds need to be removed at all
```
Example output:
```
kubectlauthorizationpolicies.security.istio.io        2025-03-24T19:36:08Z
destinationrules.networking.istio.io                  2025-03-24T19:36:08Z
envoyfilters.networking.istio.io                      2025-03-24T19:36:08Z
gateways.networking.istio.io                          2025-03-24T19:36:08Z
peerauthentications.security.istio.io                 2025-03-24T19:36:08Z
proxyconfigs.networking.istio.io                      2025-03-24T19:36:08Z
requestauthentications.security.istio.io              2025-03-24T19:36:08Z
serviceentries.networking.istio.io                    2025-03-24T19:36:08Z
sidecars.networking.istio.io                          2025-03-24T19:36:08Z
telemetries.telemetry.istio.io                        2025-03-24T19:36:08Z
virtualservices.networking.istio.io                   2025-03-24T19:36:08Z
wasmplugins.extensions.istio.io                       2025-03-24T19:36:08Z
workloadentries.networking.istio.io                   2025-03-24T19:36:08Z
workloadgroups.networking.istio.io                    2025-03-24T19:36:08Z
```

If the previous command shows existing CRDs, you should remove them. If the command did not output anything, you can skip this step and proceed with the new setup.

To remove the CRDs, run the following command:
```bash
kubectl get crd -o name | grep 'istio.io' | xargs kubectl delete # removing crds
```

> Note: If there are no resources to delete, the following error `You must provide one or more resources by argument or filename` is expected.


### Running the Ansible Playbook

#### Install
To install the application, use the following Ansible command:
```bash
ansible-playbook playbooks/application.yaml -e @inventory/test-cluster/config.yaml --tags install
```
Run `kubectl get pods -A` to verify that the expected pods are running. For more details, refer to the [Verify Services](README.md#verify-services)

**Important**: In case of any failure, it's better to proceed with an [uninstall](#uninstall) first, as something may have already been deployed (check `kubectl get pods -A`), and the next installation attempt will fail for sure.

> [!NOTE]
> The default LLM for Xeon execution is `meta-llama/Llama-3.1-8B-Instruct`. 
> Ensure your HF_TOKEN grants access to this model.
> Refer to the [official Hugging Face documentation](https://huggingface.co/docs/hub/models-gated) for instructions on accessing gated models.

#### Uninstall
To uninstall the application, use the following Ansible command:
```bash
ansible-playbook playbooks/application.yaml -e @inventory/test-cluster/config.yaml --tags uninstall
```


### Logs and Credentials
Credentials and logs related to the deployment process will be stored in the `ansible-logs` directory. To view the contents of a secret file, use `ansible-vault view` command. You will be prompted to enter the vault password. Once entered, the encrypted file will be decrypted and displayed.

Example:
```
ansible-vault view ansible-logs/grafana-password.txt                                                                                                            sdp@node1
Vault password: # prompt to enter the Vault password
password: XXXXXXXXXX  # displayed Grafana password
```

> NOTE: The location of this directory may change in the future after the testing phase is complete.
