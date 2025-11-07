# User Data Backup and Restore

This document gives a brief introduction to backup and restore operations in Intel&reg; AI for Enterprise RAG.

## Table of Contents

1. [Introduction](#introduction)
1. [Installation](#installation)
1. [User Data Backup](#user-data-backup)
1. [User Data Restore](#user-data-restore)

## Introduction

> [!NOTE]
> The backup and restore feature is disabled by default - due to the necessary configuration and maintenance efforts.

Backup and restore is based on the VMware Velero solution.<br>
The feature is not enabled by default but evaluation of the functionality is possible by following the steps described in this document.

## Installation

> [!IMPORTANT]
> Velero installation requires a dedicated `StorageClass` to be set up as default in the cluster before installing the solution. Furthermore, it needs support for volume snapshots, like the NFS storage driver offered by the infrastructure Ansible playbook. Instructions listed in this section need to be accounted for before installing the cluster and the RAG solution.

To have a working backup and restore functionality, the following items need to be ensured:

- Deploying the cluster with a `StorageClass` that supports volume snapshots.<br>
  Velero works with volumes provisioned with a dedicated `StorageClass`, supporting volume snapshots. <br>
  Good choice for evaluation might be an installation of NFS server and storage driver in the cluster. A simplified approach to achieve this in the cluster is offered by the infrastructure Ansible playbook `deployment/playbooks/infrastructure.yaml`.
  At a minimum, the following values need to be set in cluster `config.yaml` before starting the infrastructure Ansible playbook:
  ```yaml
  install_csi: nfs
  ```
  See the Multi-Node Support and Storage Requirements section in the [Advanced Configuration Guide](advanced_configuration.md#multi-node-support-and-storage-requirements) for detailed configuration instructions.

- Enabling the installation of VMware Velero along with the RAG solution.<br>
  To ensure that Velero is installed during the deployment of the cluster, update `config.yaml` to have at least these parameters set accordingly:
  ```yaml
  velero:
    enabled: true
    namespace: velero

    velero_pod_labels:
      app.kubernetes.io/instance: velero
      app.kubernetes.io/name: velero

    install_server: true
    install_client: true
  ```
  Please review the cluster config file `deployment/inventory/sample/config.yaml` for details.

## User Data Backup

Application supports taking backup and restoring user data, including ingested vector data, ingested documents, user accounts, credentials, and chat history.

With backup enabled and configured in the cluster, the backup can be taken with the following command:
```sh
ansible-playbook -u $USER -K playbooks/backup.yaml --tags backup,monitor_backup \
  -e @inventory/test-cluster/config.yaml
```
Where the path `@inventory/test-cluster/config.yaml` needs to be replaced with the path to the cluster config file.

Backup process will now start and will be monitored until completion (tag `monitor_backup` is optional). As a result, a backup object will be created in the `velero` namespace that can be listed with the `kubectl` command:

```sh
kubectl get backups -n velero

NAME                     AGE
backup-20250916t114315   21h
backup-20250916t112104   21h
```

`velero` namespace is used by default; review `config.yaml` to see where it can be changed.

## User Data Restore

With Velero configured correctly, the data restore process can be started with the following command:
```sh
ansible-playbook -u $USER -K playbooks/backup.yaml --tags restore,monitor_restore \
-e @inventory/test-cluster/config.yaml # this needs to be replaced with the path to the cluster config file
```

This will restore the application from the latest backup resource. To restore from a specific backup, the target resource needs to be provided as an extra variable:
```sh
ansible-playbook -u $USER -K playbooks/backup.yaml --tags restore,monitor_restore \
  -e @inventory/test-cluster/config.yaml \
  -e '{"velero": {"restore_from": BACKUP_RESOURCE_ID} }'

```
Where `BACKUP_RESOURCE_ID` is the name of the Kubernetes `backup` resource to restore from.
