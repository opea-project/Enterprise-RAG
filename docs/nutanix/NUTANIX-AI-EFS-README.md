# EFS Integration with EKS Cluster

This configuration provides a complete setup for using AWS Elastic File System (EFS) with your EKS cluster named "eks_al2023".

## Overview

The setup includes:

1. **EFS File System** - A scalable, elastic file system for shared storage
2. **EFS Mount Targets** - One mount target per private subnet for high availability
3. **EFS Access Point** - Managed access point with POSIX permissions
4. **Security Groups** - Proper network access controls between EKS and EFS
5. **IAM Roles** - Service account roles for the EFS CSI driver
6. **Kubernetes Examples** - Ready-to-use YAML manifests

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   EKS Cluster   │    │  Security Group  │    │   EFS System    │
│                 │    │                  │    │                 │
│  ┌───────────┐  │    │  ┌────────────┐  │    │  ┌───────────┐  │
│  │    Pod    │◄─┼────┼─►│    Rule    │◄─┼────┼─►│Mount Point│  │
│  └───────────┘  │    │  │ Port: 2049 │  │    │  └───────────┘  │
│                 │    │  └────────────┘  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Features Configured

### EFS File System
- **Performance Mode**: General Purpose (for most workloads)
- **Throughput Mode**: Provisioned (500 MiB/s)
- **Encryption**: Enabled at rest
- **Lifecycle Policy**: Transition to IA after 30 days

### Security
- Dedicated security group for EFS with NFS access (port 2049)
- Security group rules allowing EKS nodes to access EFS
- Egress rules for EKS cluster to reach EFS

### Access Point
- **Path**: `/shared-data`
- **POSIX User**: UID/GID 1001
- **Permissions**: 755

## Deployment Steps

### 1. Deploy Infrastructure
```bash
# Navigate to the terraform directory
cd Enterprise-RAG/deployment/terraform/aws/nutanix/eks-nutanix-ai

# Initialize and apply Terraform
terraform init
terraform plan
terraform apply
```

### 2. Configure kubectl
```bash
# Update kubeconfig to connect to the EKS cluster
aws eks update-kubeconfig --region us-east-1 --name $(terraform output -raw cluster_name)

# Verify connection
kubectl get nodes
```

### 3. Deploy Kubernetes Resources
```bash
# Use the provided script to deploy EFS-enabled resources
chmod +x ./deploy-efs-k8s.sh
sed -i 's/\r$//' ./deploy-efs-k8s.sh
./deploy-efs-k8s.sh
```

Or manually:
```bash
# Get the EFS values from Terraform
EFS_FILE_SYSTEM_ID=$(terraform output -raw efs_file_system_id)
EFS_ACCESS_POINT_ID=$(terraform output -raw efs_access_point_id)

# Edit efs-example.yaml with actual values and apply
kubectl apply -f efs-example.yaml
```

## Verification

### Check EFS CSI Driver
```bash
# Verify EFS CSI driver is running
kubectl get pods -n kube-system | grep efs-csi

# Check CSI driver addon
kubectl get addon -A
```

### Test Storage
```bash
# Check storage class
kubectl get storageclass efs-sc

# Check persistent volume
kubectl get pv efs-pv

# Check persistent volume claim
kubectl get pvc efs-claim

# Check test pod
kubectl get pod efs-app
kubectl logs efs-app
kubectl exec -it efs-app -- ls -la /data/
```

### Test Shared Storage
```bash
# Check deployment with multiple replicas
kubectl get deployment efs-shared-app
kubectl get pods -l app=efs-shared-app

# Test file sharing between pods
kubectl exec -it <pod-name-1> -- echo "Hello from pod 1" > /usr/share/nginx/html/test.txt
kubectl exec -it <pod-name-2> -- cat /usr/share/nginx/html/test.txt
```

## Kubernetes Resources Included

### Storage Class (`efs-sc`)
- Provisions EFS access points dynamically
- Configured for the created EFS file system

### Persistent Volume (`efs-pv`)
- Uses the EFS access point for managed access
- ReadWriteMany access mode for shared storage

### Example Applications
1. **Single Pod** (`efs-app`) - Writes timestamped data to shared storage
2. **Multi-replica Deployment** (`efs-shared-app`) - Nginx pods sharing content via EFS

## Important Notes

### Security
- EFS is only accessible from EKS worker nodes via security groups
- Network access is restricted to NFS port 2049
- Encryption is enabled for data at rest

### Performance
- Provisioned throughput mode is configured for consistent performance
- General Purpose performance mode suitable for most workloads
- Consider Provisioned throughput adjustments based on your needs

### Access Patterns
- Use ReadWriteMany for shared access across multiple pods
- EFS access points provide isolation and security
- Lifecycle policies help manage storage costs

## Troubleshooting

### EFS CSI Driver Issues
```bash
# Check CSI driver pods
kubectl describe pods -n kube-system -l app=efs-csi-controller
kubectl logs -n kube-system -l app=efs-csi-controller

# Check node driver
kubectl describe pods -n kube-system -l app=efs-csi-node
```

### Mount Issues
```bash
# Check mount targets
aws efs describe-mount-targets --file-system-id $(terraform output -raw efs_file_system_id)

# Check security groups
aws ec2 describe-security-groups --group-ids $(terraform output -raw efs_security_group_id)
```

### Pod Issues
```bash
# Check pod events
kubectl describe pod <pod-name>

# Check PVC status
kubectl describe pvc efs-claim
```

## Customization

### Adjusting Performance
Modify the EFS configuration in `eks-al2023.tf`:
```hcl
resource "aws_efs_file_system" "main" {
  performance_mode                = "maxIO"  # For higher levels of aggregate throughput
  throughput_mode                 = "provisioned"
  provisioned_throughput_in_mibps = 1000     # Adjust as needed
  # ... other settings
}
```

### Adding More Access Points
```hcl
resource "aws_efs_access_point" "additional" {
  file_system_id = aws_efs_file_system.main.id
  
  posix_user {
    gid = 2001
    uid = 2001
  }
  
  root_directory {
    path = "/app-data"
    creation_info {
      owner_gid   = 2001
      owner_uid   = 2001
      permissions = "755"
    }
  }
}
```

## Cost Optimization

- Lifecycle policies transition infrequently accessed files to Infrequent Access (IA)
- Monitor throughput usage and adjust provisioned throughput accordingly
- Use EFS Intelligent-Tiering for automatic cost optimization

## Support

For issues specific to:
- **Terraform**: Check the AWS provider documentation
- **EKS**: Refer to AWS EKS documentation
- **EFS CSI Driver**: Check the AWS EFS CSI driver GitHub repository
- **Kubernetes**: Consult Kubernetes storage documentation