# Intel® AI for Enterprise RAG deployment guide

This document details the deployment of Intel® AI for Enterprise RAG. By default, the guide assumes a Xeon deployment. If your hardware stack contains Gaudi, modify configuration values accordingly to deployment instructions.

## Table of Contents

1. [Intel® AI for Enterprise RAG Deployment](#intel-ai-for-enterprise-rag-deployment)
   1. [Virtual Environment Setup](#virtual-environment-setup)
   2. [Validate Hardware Requirements](#validate-hardware-requirements)
   3. [Install a Kubernetes cluster (optional - if you don't have one)](#install-a-kubernetes-cluster-optional---if-you-dont-have-one)
   4. [Install infrastructure components (storage, operators, backup tools)](#install-infrastructure-components-storage-operators-backup-tools)
   5. [Deploy the Intel® AI for Enterprise RAG application on top of the prepared infrastructure](#deploy-the-intel-ai-for-enterprise-rag-application-on-top-of-the-prepared-infrastructure)
   6. [Update application components (models, configurations) as needed](#update-application-components-models-configurations-as-needed)
   7. [Create and restore backups of user data and configurations](#create-and-restore-backups-of-user-data-and-configurations)
2. [Interact with ChatQnA](#interact-with-chatqna)
   1. [Test Deployment](#test-deployment)
   2. [Access the UI/Grafana](#access-the-uigrafana)
   3. [UI Credentials for the First Login](#ui-credentials-for-the-first-login)
   4. [Credentials for Grafana and Keycloak](#credentials-for-grafana-and-keycloak)
   5. [Credentials for Vector Store](#credentials-for-vector-store)
   6. [Credentials for Enhanced Dataprep Pipeline (EDP)](#credentials-for-enhanced-dataprep-pipeline-edp)
   7. [Data Ingestion, UI and Telemetry](#data-ingestion-ui-and-telemetry)
   8. [Configure Single Sign-On Integration Using Microsoft Entra ID](#configure-single-sign-on-integration-using-microsoft-entra-id)
3. [Remove the installation when no longer needed](#remove-the-installation-when-no-longer-needed)

---

# Intel® AI for Enterprise RAG Deployment

Intel® AI for Enterprise RAG contains [ansible playbooks](./playbooks) which provide a complete deployment workflow:

0. **Validate hardware requirements** (recommended before deployment)
1. **Install a Kubernetes cluster** (optional - if you don't have one)
2. **Install infrastructure components** (storage, operators, backup tools)
3. **Deploy the Intel® AI for Enterprise RAG application** on top of the prepared infrastructure
4. **Update application components** (models, configurations) as needed
5. **Create and restore backups** of user data and configurations
6. **Remove the installation** when no longer needed

The validation step helps ensure your hardware meets the minimum requirements for Intel® AI for Enterprise RAG before proceeding with the deployment. The following sections guide you through each of these steps.

## Virtual Environment Setup

Playbooks can be executed after creating a virtual environment and installing all prerequisites that allow running ansible on your local machine. Use the below script to create a virtual environment:

```sh
cd deployment
sudo apt-get install python3-venv
python3 -m venv erag-venv
source erag-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yaml --upgrade
```

## Validate Hardware Requirements

Before proceeding with the deployment, it's recommended to validate that your hardware meets the requirements for Intel® AI for Enterprise RAG. To perform hardware validation, you need to create an inventory.ini file first.

An example inventory.ini file structure and detailed instructions are provided in the [Cluster Deployment Guide](../docs/cluster_deployment_guide.md).

Once you have created the inventory.ini file, you can validate your hardware resources using the validate playbook located at `playbooks/validate.yaml`:

```sh
ansible-playbook playbooks/validate.yaml --tags hardware -i inventory/test-cluster/inventory.ini
```

> [!NOTE]
> If this is a Gaudi deployment, add the additional flag `-e is_gaudi_platform=true`

## Install a Kubernetes cluster (optional - if you don't have one)

Intel® AI for Enterprise RAG offers ansible automation for creating a K8s cluster. If you want to set up a K8s cluster, follow the [Cluster Deployment Guide](../docs/cluster_deployment_guide.md).

## Install infrastructure components (storage, operators, backup tools)

The Intel® AI for Enterprise RAG repository offers installation of additional infrastructure components on the deployed K8s cluster:
- **Gaudi_operator** - dedicated for K8s clusters with nodes that use Gaudi AI accelerators
- **CSI drivers** - need to dynamically provision storage for PODs
- **Velero** - installing Velero backup tool
- **Local registry** - creates a pod with registry to store Docker images, useful for multi-node setups where internal Docker registry would not be sufficient as it will be accessible from single node, not from entire K8s cluster. See [Local Image Building](../docs/advanced_configuration.md#local-image-building) for configuration details.

If your K8s cluster requires installing any of these tools, follow the [Infrastructure Components Guide](../docs/infrastructure_components_guide.md).

## Deploy the Intel® AI for Enterprise RAG application on top of the prepared infrastructure

Once you have a K8s cluster with all infrastructure components installed, you can install the Intel® AI for Enterprise RAG application on top of it. Follow the [Application Deployment Guide](../docs/application_deployment_guide.md).

## Update application components (models, configurations) as needed

After the application is installed, you can update its components (for example, change the LLM or embedding model) by editing your configuration file and running the install tag again. The deployment scripts will detect changes and update only the involved components, minimizing downtime and unnecessary redeployments.

To update the application:

1. Edit `inventory/test-cluster/config.yaml` and adjust the relevant parameters (e.g., `llm_model`, `embedding_model_name`, or other settings).
2. Run:

```sh
ansible-playbook playbooks/application.yaml --tags install -e @inventory/test-cluster/config.yaml
```

This will apply the changes and update only the affected services.

## Create and restore backups of user data and configurations

The application supports taking backups and restoring user data, including ingested vector data, ingested documents, user accounts and credentials, and chat history.

For detailed instructions on how to configure backup functionality, create backups, and restore from backups, refer to the [Backup and Restore Guide](../docs/backup.md).

# Interact with ChatQnA

## Test Deployment

To verify that the deployment was successful, run the following command:
```bash
./scripts/test_connection.sh
```
If the deployment is complete, you should observe the following output:
```
deployment.apps/client-test created
Waiting for all pods to be running and ready....All pods in the chatqa namespace are running and ready.
Connecting to the server through the pod client-test-87d6c7d7b-45vpb using URL http://router-service.chatqa.svc.cluster.local:8080...
data: '\n'
data: 'A'
data: ':'
data: ' AV'
data: 'X'
data: [DONE]
Test finished successfully
```

## Access the UI/Grafana

To access the UI, follow these steps:
1. Forward the port from the ingress pod:
    ```bash
    sudo -E kubectl port-forward --namespace ingress-nginx svc/ingress-nginx-controller 443:https
    ```
2. If you want to access the UI from another machine, tunnel the port from the host:
    ```bash
    ssh -L 443:localhost:443 user@ip
    ```
3. Update the `/etc/hosts` file on the machine where you want to access the UI to match the domain name with the externally exposed IP address of the cluster. On a Windows machine, this file is typically located at `C:\Windows\System32\drivers\etc\hosts`.

    For example, the updated file content should resemble the following:

    ```
    127.0.0.1 erag.com grafana.erag.com auth.erag.com s3.erag.com minio.erag.com
    ```

> [!NOTE]
> This is the IPv4 address of the local machine.

Once the update is complete, you can access the Intel® AI for Enterprise RAG UI by typing the following URL in your web browser:
`https://erag.com`

Keycloak can be accessed via:
`https://auth.erag.com`

Grafana can be accessed via:
`https://grafana.erag.com`

MinIO Console can be accessed via:
`https://minio.erag.com`

S3 API is exposed at:
`https://s3.erag.com`

> [!CAUTION]
> If using self-signed certificates (default configuration), access `https://s3.erag.com` in your browser before ingesting data to accept the certificate warning. This step is not required if you have configured custom SSL certificates.

## UI Credentials for the First Login

Once deployment is complete, a file named `default_credentials.txt` will be created in the `deployment/ansible-logs` folder with one-time passwords for the application admin and user. After entering the one-time password, you will be required to change the default password.

> [!CAUTION]
> Remove the `default_credentials.txt` file after the first successful login.

## Credentials for Grafana and Keycloak

Default credentials for Keycloak and Grafana:
- **username:** admin
- **password:** stored in `ansible-logs/default_credentials.yaml` file. Change passwords after first login in Grafana or Keycloak.

> [!CAUTION]
> Use ansible-vault to secure the password file `ansible-logs/default_credentials.yaml` after the first successful login by running: `ansible-vault encrypt ansible-logs/default_credentials.yaml`. After that, remember to add `--ask-vault-pass` to the `ansible-playbook` command.

## Credentials for Vector Store

Default credentials for the selected Vector Store are stored in `ansible-logs/default_credentials.yaml` and are generated on first deployment.

## Credentials for Enhanced Dataprep Pipeline (EDP)

Default credentials for Enhanced Dataprep services:

MinIO:
- For accessing MinIO either by API or Web UI (MinIO Console), use the user credentials for `erag-admin`.

Internal EDP services credentials:

Redis:
- **username:** default
- **password:** stored in `ansible-logs/default_credentials.yaml`

Postgres:
- **username:** edp
- **password:** stored in `ansible-logs/default_credentials.yaml`

## Data Ingestion, UI and Telemetry

For adding data to the knowledge base and exploring the UI interface, visit [this](../docs/UI_features.md) page.

For accessing Grafana dashboards for all services, visit [this](../docs/telemetry.md) page.

## Configure Single Sign-On Integration Using Microsoft Entra ID

For instructions on how to configure single sign-on, visit [this](../docs/single_sign_on_configuration_on_keyclock.md) page.

# Remove the installation when no longer needed

To remove Intel® AI for Enterprise RAG from your cluster, execute:

```sh
ansible-playbook playbooks/application.yaml --tags uninstall -e @inventory/test-cluster/config.yaml
```
