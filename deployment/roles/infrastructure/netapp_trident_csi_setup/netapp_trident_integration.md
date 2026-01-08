# NetApp Trident CSI Integration for Enterprise RAG

This document describes the NetApp Trident CSI driver integration implemented for the Intel Enterprise RAG project to support AIPod Mini deployments with NetApp ONTAP storage.

## Overview

NetApp Trident is a dynamic storage orchestrator for Kubernetes that enables persistent storage for containerized applications using NetApp storage systems. This integration adds support for NetApp ONTAP storage as a CSI driver option in the Enterprise RAG deployment.

## Integration Summary

### Purpose
Integrate NetApp Trident CSI deployment automation into the Intel Enterprise RAG project to provide enterprise-grade persistent storage capabilities using NetApp ONTAP systems.

### Key Features
- Automated Trident operator installation using Helm
- ONTAP NAS backend configuration
- Dynamic StorageClass creation with ReadWriteMany support
- Seamless integration with existing Enterprise RAG deployment workflow
- Ubuntu-specific NFS utilities installation for Trident prerequisites

## Current Project Structure

### Enterprise RAG Deployment Architecture

The Enterprise RAG project follows a structured Ansible-based deployment approach with the following key components:

```
Enterprise-RAG/
├── deployment/
│   ├── playbooks/
│   │   ├── infrastructure.yaml           # Infrastructure setup playbook
│   │   ├── application.yaml              # Application deployment playbook
│   │   └── validate.yaml                 # Validation playbook
│   ├── roles/
│   │   ├── application/                  # Application-specific roles
│   │   ├── common/                       # Shared utilities and validation
│   │   │   └── validate_config/          # Configuration validation
│   │   └── infrastructure/               # Infrastructure roles
│   │       ├── cluster/                  # Kubernetes cluster management
│   │       │   └── tasks/
│   │       │       └── post_installation.yaml  # Post-install tasks
│   │       ├── gaudi_operator/           # Intel Gaudi support
│   │       ├── k8s_local_registry/       # Local container registry
│   │       ├── nfs_server_csi_setup/     # NFS CSI driver (existing)
│   │       └── velero/                   # Backup solution
│   └── inventory/
│       └── sample/
│           └── config.yaml               # Sample configuration file
├── docs/                                 # Project documentation
└── src/                                  # Source code components
```

### Current CSI Driver Support

Before Trident integration, Enterprise RAG supported:

1. **`local-path-provisioner`**: For single-node deployments
   - Location: Built into Kubespray
   - Use case: Development and single-node setups
   - Access modes: ReadWriteOnce only

2. **`nfs`**: For multi-node deployments
   - Location: [`deployment/roles/infrastructure/nfs_server_csi_setup/`](https://github.com/sushma-m1/Enterprise-RAG/tree/main/deployment/roles/infrastructure/nfs_server_csi_setup)
   - Use case: Multi-node clusters requiring ReadWriteMany
   - Implementation: In-cluster NFS server + CSI driver

### Configuration Flow

1. **User Configuration**: Users modify [`inventory/sample/config.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/inventory/sample/config.yaml)
2. **Validation**: [`roles/common/validate_config/`](https://github.com/sushma-m1/Enterprise-RAG/tree/main/deployment/roles/common/validate_config) validates settings
3. **Infrastructure Setup**: [`playbooks/infrastructure.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/playbooks/infrastructure.yaml) handles Kubernetes and CSI setup
4. **Post-Installation**: [`roles/infrastructure/cluster/tasks/post_installation.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/roles/infrastructure/cluster/tasks/post_installation.yaml) manages CSI drivers
5. **Application Deployment**: [`playbooks/application.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/playbooks/application.yaml) deploys Enterprise RAG components

## Files Modified/Created

### 1. Infrastructure Playbook
**File**: [`deployment/playbooks/infrastructure.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/playbooks/infrastructure.yaml)

**Changes Made**:
- Added NFS utilities installation section for Ubuntu systems
- Conditional installation when `install_csi == "netapp-trident"`
- Installs `nfs-common` and `nfs-kernel-server` packages for NFS client utilities and NFS server utilities (required for Trident NFS backends) respectively.

```yaml
- name: Install NFS utilities
  hosts: k8s_cluster
  become: true
  tags:
    - install
    - post-install
  tasks:
    - name: Install NFS utilities on Ubuntu
      ansible.builtin.package:
        name:
          - nfs-common
          - nfs-kernel-server
        state: present
        update_cache: true
      when: 
        - ansible_distribution == "Ubuntu"
        - install_csi == "netapp-trident"
```

### 2. Post-Installation Tasks
**File**: [`deployment/roles/infrastructure/cluster/tasks/post_installation.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/roles/infrastructure/cluster/tasks/post_installation.yaml)

**Changes Made**:
- Added NetApp Trident CSI role inclusion for installation
- Added uninstall task for cleanup operations

```yaml
- name: NetApp Trident CSI role
  ansible.builtin.include_role:
    name: netapp_trident_csi_setup
  when: install_csi == "netapp-trident"
  tags:
    - install
    - post-install

- name: Uninstall NetApp Trident
  ansible.builtin.include_role:
    name: netapp_trident_csi_setup
  when: install_csi == "netapp-trident"
  tags:
    - delete
```

### 3. Configuration Validation
**File**: [`deployment/roles/common/validate_config/tasks/main.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/roles/common/validate_config/tasks/main.yaml)

**Changes Made**:
- Updated CSI driver validation to include "netapp-trident" as valid option

```yaml
# Before
install_csi not in ['local-path-provisioner', 'nfs']

# After  
install_csi not in ['local-path-provisioner', 'nfs', 'netapp-trident']
```

### 4. Sample Configuration
**File**: [`deployment/inventory/sample/config.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/inventory/sample/config.yaml)

**Changes Made**:
- Added "netapp-trident" to available CSI options documentation
- Added comprehensive Trident configuration section with ONTAP parameters

```yaml
# Available options:
# - "netapp-trident": Use for NetApp ONTAP storage with Trident CSI driver

# Setup when install_csi is "netapp-trident"
trident_operator_version: "2506.0"
trident_namespace: "trident"
trident_storage_class: "netapp-trident"
trident_backend_name: "ontap-nas"
ontap_management_lif: ""
ontap_data_lif: ""
ontap_svm: ""
ontap_username: ""
ontap_password: ""
```

## New Ansible Role Created

### Role Structure
```
deployment/roles/infrastructure/netapp_trident_csi_setup/
├── defaults/main.yaml
├── tasks/main.yaml
├── templates/
│   ├── trident-backend.yaml.j2
│   └── trident-storageclass.yaml.j2
└── README.md
```

### Role Components

#### [defaults/main.yaml](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/roles/infrastructure/netapp_trident_csi_setup/defaults/main.yaml)
Default variables for Trident configuration including:
- Trident operator version (25.06)
- Namespace and StorageClass names
- ONTAP backend connection parameters

#### [tasks/main.yaml](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/roles/infrastructure/netapp_trident_csi_setup/tasks/main.yaml)
Main Ansible tasks including:
- **Install Tasks**:
  - Create Trident namespace
  - Add official NetApp Helm repository
  - Install Trident operator via Helm
  - Create ONTAP NAS backend configuration
  - Create StorageClass with ReadWriteMany support
  - Manage default StorageClass annotations

- **Delete Tasks**:
  - Uninstall Trident operator
  - Remove Trident namespace

#### Templates

[**trident-backend.yaml.j2**](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/roles/infrastructure/netapp_trident_csi_setup/templates/trident-backend.yaml.j2): TridentBackendConfig CRD for ONTAP NAS
```yaml
apiVersion: trident.netapp.io/v1
kind: TridentBackendConfig
metadata:
  name: {{ trident_backend_name }}
  namespace: {{ trident_namespace }}
spec:
  version: 1
  storageDriverName: ontap-nas
  managementLIF: {{ ontap_management_lif }}
  dataLIF: {{ ontap_data_lif }}
  svm: {{ ontap_svm }}
  username: {{ ontap_username }}
  password: {{ ontap_password }}
```

[**trident-storageclass.yaml.j2**](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/roles/infrastructure/netapp_trident_csi_setup/templates/trident-storageclass.yaml.j2): Kubernetes StorageClass
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: {{ trident_storage_class }}
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: csi.trident.netapp.io
parameters:
  backendType: ontap-nas
  fsType: nfs
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
```

## Configuration Requirements

### Prerequisites
1. **NetApp ONTAP System**: Configured ONTAP cluster with:
   - Storage Virtual Machine (SVM) configured
   - NFS protocol enabled
   - Data and management LIFs configured
   - Aggregate with available space

2. **Kubernetes Cluster**: Running Kubernetes cluster with:
   - Helm 3.x installed
   - Ubuntu nodes (for NFS utilities installation)
   - Network connectivity to ONTAP system

3. **Authentication**: ONTAP credentials with administrative privileges

### Required Configuration Parameters

Users must provide the following ONTAP-specific parameters in their [`config.yaml`](https://github.com/sushma-m1/Enterprise-RAG/blob/main/deployment/inventory/sample/config.yaml):

```yaml
install_csi: "netapp-trident"
ontap_management_lif: "192.168.1.100"    # ONTAP management interface IP
ontap_data_lif: "192.168.1.101"          # ONTAP data interface IP
ontap_svm: "svm_ai"                       # Storage Virtual Machine name
ontap_username: "admin"                   # ONTAP admin username
ontap_password: "password123"             # ONTAP admin password
```

## Deployment Process

### Step 1: Configure Parameters
1. Copy sample configuration:
   ```bash
   cp -r inventory/sample inventory/my-cluster
   ```

2. Edit `inventory/my-cluster/config.yaml`:
   - Set `install_csi: "netapp-trident"`
   - Fill in all ONTAP connection parameters
   - Configure other Enterprise RAG settings

### Step 2: Deploy Infrastructure
```bash
ansible-playbook -K playbooks/infrastructure.yaml \
  --tags post-install \
  -i inventory/my-cluster/inventory.ini \
  -e @inventory/my-cluster/config.yaml
```

### Step 3: Deploy Enterprise RAG Application
```bash
ansible-playbook playbooks/application.yaml \
  -i inventory/my-cluster/inventory.ini \
  -e @inventory/my-cluster/config.yaml
```

## Storage Capabilities

### ReadWriteMany Support
The Trident CSI driver with ONTAP NAS backend provides:
- **ReadWriteMany (RWX)**: Multiple pods can mount the same volume with read-write access
- **ReadWriteOnce (RWO)**: Single pod exclusive access
- **ReadOnlyMany (ROX)**: Multiple pods with read-only access

### Dynamic Provisioning
- Automatic volume creation on-demand
- Volume expansion support
- Snapshot capabilities (with VolumeSnapshotClass)
- Backup integration with Velero

## Integration Benefits

### For Enterprise RAG
- **Multi-node Support**: RWX capability enables pod scheduling across multiple nodes
- **Enterprise Storage**: Production-grade NetApp ONTAP storage backend
- **Data Protection**: Built-in ONTAP features (snapshots, replication, backup)
- **Performance**: High-performance NFS storage for AI workloads
- **Scalability**: Dynamic volume provisioning and expansion

### For AIPod Mini
- **Simplified Deployment**: Automated Trident installation and configuration
- **Consistent Storage**: Standardized storage across AIPod deployments
- **Enterprise Integration**: Seamless integration with existing NetApp infrastructure
- **Support Matrix**: Supported configuration for enterprise deployments

## Troubleshooting

### Common Issues

1. **NFS Utilities Installation Fails**
   - Ensure nodes are running Ubuntu
   - Check network connectivity for package downloads
   - Verify sudo/root privileges

2. **Trident Installation Fails**
   - Verify Helm repository accessibility
   - Check Kubernetes cluster connectivity
   - Ensure sufficient cluster resources

3. **Backend Configuration Fails**
   - Verify ONTAP connectivity (management and data LIFs)
   - Check ONTAP credentials and permissions
   - Ensure SVM and aggregate exist
   - Verify NFS protocol is enabled on SVM

4. **StorageClass Issues**
   - Check if Trident CSI driver pods are running
   - Verify backend is registered with Trident
   - Check for conflicting default StorageClasses

### Verification Commands

```bash
# Check Trident installation
kubectl get pods -n trident

# Check StorageClass
kubectl get storageclass

# Check Trident backends
kubectl get tridentbackendconfig -n trident

# Check volume provisioning
kubectl get pvc --all-namespaces
```

## Security Considerations

1. **Credential Management**: ONTAP credentials are stored in Kubernetes secrets
2. **Network Security**: Ensure secure communication between Kubernetes and ONTAP
3. **RBAC**: Implement proper Kubernetes RBAC for Trident resources
4. **Storage Security**: Configure ONTAP security features (encryption, access controls)

## Version Compatibility

- **Trident Version**: 25.06 (Helm chart version 100.2506.0)
- **Kubernetes**: 1.31+ (as supported by Enterprise RAG)
- **ONTAP**: 9.8+ (recommended for full feature support)
- **Ubuntu**: 22.04/24.04 (for NFS utilities)

## Future Enhancements

Potential areas for future development:

1. **Additional Storage Drivers**: Support for ONTAP SAN (iSCSI, FC)
2. **Advanced Features**: Integration with ONTAP snapshots and clones
3. **Performance Tuning**: Optimized configurations for AI workloads
4. **Monitoring**: Integration with NetApp monitoring tools
5. **GenAI Examples**: Sample applications demonstrating Trident storage usage

## Support and Documentation

- **NetApp Trident Documentation**: https://docs.netapp.com/us-en/trident/
- **Helm Installation Guide**: https://docs.netapp.com/us-en/trident/trident-get-started/kubernetes-deploy-helm.html
- **Enterprise RAG Documentation**: See main project README.md

---

*This integration was developed as part of NetApp's contribution to the OPEA Enterprise RAG project in support of AIPod Mini deployments.*
