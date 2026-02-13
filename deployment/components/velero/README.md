# Velero Integration

## Table of Contents

1. [Introduction](#introduction)
1. [Velero Requirements](#velero-requirements)
1. [Backup and Restore Configuration Variants](#backup-and-restore-configuration-variants)
1. [Complete Backup of User Data](#complete-backup-of-user-data)
1. [Complete Restore of User Data](#complete-restore-of-user-data)
1. [Understanding the Backup and Restore Operation](#understanding-the-backup-and-restore-operation)
1. [Removal of Velero from the Cluster](#removal-of-velero-from-the-cluster)
1. [Backup Links](#backup-links)

## Introduction

> [!NOTE]
> The backup and restore feature is disabled by default - due to the necessary configuration and maintenance efforts.

Backup functionality is based on the VMware Velero solution version 1.16.<br> It has been added to Intel&reg; AI for Enterprise RAG to offer protection and reduce downtime in case of accidents.

The recommended way to enable Velero is to plan for it up front before deploying a Kubernetes cluster, as certain prerequisites need to be met.


## Velero Requirements

To have a working backup and restore functionality, the following items need to be ensured:

1. Installation of a `StorageClass` with support for volume snapshots.<br>
   Velero works with volumes provisioned with a dedicated `StorageClass`, supporting volume snapshots.


   - One option is to install the NFS server and storage driver in the cluster.
     Simplified approach to achieve this has been described in the [User Data Backup](../../../docs/backup.md) overview document.

     Briefly, this requires the following entry in the cluster `config.yaml`:
     ```yaml
     install_csi: nfs
     ```

   - The second option is to install a storage driver into the cluster directly before deploying the application with Velero enabled. The driver needs to have an associated `VolumeSnapshotClass` labeled for Velero with a command:
     ```sh
     kubectl label volumesnapshotclass SNAPSHOTCLASS \
       velero.io/csi-volumesnapshot-class="true".
     ```
     Where `SNAPSHOTCLASS` is the id of the resource in the cluster.
> [!NOTE]
> `StorageClass` of choice must be consistently used for the provisioning of new persistent volumes; it translates to making it the default StorageClass.

2. Enabling VMware Velero for backup operations.<br>
   Velero can be either pre-installed in the cluster outside of the application or installed by using the `infrastructure.yaml` Ansible playbook.
   - To install the Velero with Ansible playbook, update the cluster config file `config.yaml` to have at least these parameters set accordingly:
     ```yaml
     velero:
       enabled: true  # enable the backup operations
       namespace: velero

       velero_pod_labels:
         app.kubernetes.io/instance: velero
         app.kubernetes.io/name: velero

       install_server: true
       install_client: true
     ```
     Please review the sample cluster config file comments for details.

   - To use the pre-installed Velero instance, the cluster config file `config.yaml` needs to have the following config parameters updated:
     ```yaml
     velero:
       enabled: true  # enable the backup operations
       namespace: VELERO_NAMESPACE  # needs to point to namespace where Velero has been deployed

       velero_pod_labels:
         app.kubernetes.io/instance: velero
         app.kubernetes.io/name: velero

       install_server: false  # set to false as the server is already installed
       install_client: true
     ```

1. Ensuring suitable object storage for backups.<br>
   Backup functionality uses SeaweedFS as the S3-compatible object storage backend.

## Backup and Restore Configuration Variants

  - Deployment of the Velero server after the cluster has already been set up:<br>
    - Update the cluster `config.yaml` as explained in [Velero Requirements](#velero-requirements).
    - Start a post-installation configuration process with the infrastructure Ansible playbook:
      ```sh
      ansible-playbook playbooks/infrastructure.yaml --tags post-install \
        -i inventory/test-cluster/inventory.ini \
        -e @inventory/test-cluster/config.yaml \
        -e deploy_k8s=false
      ```
    - Velero server and client will be installed, enabling the backup and restore operations.

  - Install a Velero client<br>
    Review [Velero release](https://github.com/vmware-tanzu/velero/releases/tag/v1.16.1) for the installation of the Velero command line binary if it wasn't installed during the cluster deployment.

## Complete Backup of User Data

This paragraph describes steps that are necessary to secure data coming from the user. These include:
- The ingested vector data.
- The ingested documents.
- The user accounts and credentials.
- The chat history.

Backup operation is directly supported by the invocation of a `backup.yaml` Ansible playbook.<br>
Backup can be requested with the following command:
```sh
ansible-playbook playbooks/backup.yaml --tags backup,monitor_backup -e @inventory/test-cluster/config.yaml
```

The backup process will now start and will be monitored until completion (tag `monitor_backup` is optional).
As a result, a `backup` object will be created in the specified backup namespace (review `config.yaml`) that can be described with `kubectl`:
```sh
# list backup resources
kubectl get backup -n velero
NAME                     AGE
backup-20250916t114315   21h
backup-20250916t112104   21h

# describe a backup resource to view the details
kubectl describe backup backup-20250916t114315 -n velero
Name:         backup-20250916t114315
Namespace:    backup
# (details omitted for clarity)
Status:
  Backup Item Operations Attempted:  7
  Backup Item Operations Completed:  7
  Completion Timestamp:              2025-09-16T11:43:15Z
  Csi Volume Snapshots Attempted:    7
  Csi Volume Snapshots Completed:    7
  Expiration:                        2025-10-15T11:43:15Z
  Format Version:                    1.1.0
  Hook Status:
  Phase:  Completed
  Progress:
    Items Backed Up:  452
    Total Items:      452

```

Details can also be viewed with a `velero` command:
```sh
velero backup describe backup-20250916t114315 --details
```

The name of the backup resource must be unique - that's why the backup resource names are generated by the `backup` playbook.<br>
The names follow the pattern `(BACKUP_RESOURCE_PREFIX)-(TIMESTAMP)` where:<br>
- `BACKUP_RESOURCE_PREFIX` is the `config.yaml` setting `velero.backup.prefix`,
- `TIMESTAMP` is a compact time and date representation.

## Complete Restore of User Data

This paragraph describes the steps that are necessary to restore data from a complete backup created in the previous step.

Restore operation is directly supported by the invocation of a `backup.yaml` Ansible playbook.<br>
Restore can be requested with the following command:
  ```sh
  ansible-playbook playbooks/backup.yaml --tags restore,monitor_restore -e @inventory/test-cluster/config.yaml
  ```

The restore process will now start and will be monitored until completion (tag `monitor_restore` is optional).<br>
The `backup` resource to restore will be the most recently completed backup resource. Furthermore, the backup resource can be filtered by matching Kubernetes resource labels specified in `config.yaml` for the backup resource.

To select a specific backup to restore from (not necessarily the most recent), the following command may be used:
```sh
ansible-playbook playbooks/backup.yaml --tags restore,monitor_restore \
  -e @inventory/test-cluster/config.yaml \
  -e '{"velero": {"restore_from": BACKUP_RESOURCE_ID} }'
```
where `BACKUP_RESOURCE_ID` is the name of Kubernetes `backup` resource to restore from.

As a result, a `restore` object will be created in the specified backup namespace (review `config.yaml`) that can be described with `kubectl`:
  ```sh
  # list restore resources
  kubectl get restore -n velero
  NAME                      AGE
  restore-20250907t054204   21h
  restore-20250917t052410   21h

  # describe a restore resource to view details
  kubectl describe restore restore-20250917t052410 -n velero
  Name:         restore-20250917t052410
  Namespace:    backup
  Labels:       restore-reason=recovery
  # (details omitted for clarity)
  Status:
    Completion Timestamp:  2025-09-17T05:37:44Z
    Hook Status:
    Phase:  Completed
    Progress:
      Items Restored:  378
      Total Items:     378
  ```

* Details can also be viewed with the `velero` command:
  ```sh
  velero restore describe restore-20250917t052410
  ```

* To gather further details:
  ```bash
  velero restore describe restore-20250917t052410 --details
  ```

## Understanding the Backup and Restore Operation

Backup and restore operate on instances of services along with their data. It's not only the data that is backed up and restored - the complete microservices are being processed.

This has an impact on the complexity of the restore operation.<br>
Specifically, the deployments hosting the user data need to be **removed** before being restored from saved objects and stored volume snapshots.

This results in a period of unavailability of services, including but not limited to:
- The authorization services (Keycloak instance).
- The data ingestion pipelines (`edp` namespace).

For a better overview of the operation, the monitoring mode can be enabled with the optional ansible tag `monitor_restore`.<br>
The monitor process won't finish until both the restore process on Velero side and microservices pods have recovered.

> [!NOTE]
>
> When planning to use backup and restore, it's recommended to make a copy of the `ansible-logs` folder from the original deployment. It might be necessary to properly set up credentials for services such as `fingerprint`, `chat history`, and `edp` and restore them from the backup. <br>
> In case it's necessary to uninstall the deployment to retry installation and restore from backup, that folder should be restored before starting the recovery install of RAG again.

## Removal of Velero from the Cluster

Either of the following approaches to removing Velero will result in the removal of the backup and restore objects created with the use of the Velero.

* Normally, Velero will be removed along with the cluster deletion:
  ```sh
  ansible-playbook -K playbooks/infrastructure.yaml --tags delete \
    -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
  ```

* Removing only the installed instance of Velero without deleting the cluster:
  ```sh
  ansible-playbook playbooks/infrastructure.yaml --tags velero-delete \
    -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml \
    -e deploy_k8s=false
  ```

## Backup Links

- [Kubernetes CSI Documentation](https://kubernetes-csi.github.io/docs/)
- [Velero documentation for version 1.16](https://velero.io/docs/v1.16/)
