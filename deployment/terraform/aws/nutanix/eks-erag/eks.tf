# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
module "ebs_csi_driver_irsa" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.2"
  name = "${local.name}-ebs-csi"

  attach_ebs_csi_policy = true

  oidc_providers = {
    this = {
      provider_arn               = module.eks_al2023.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
  tags = local.tags
}

module "efs_csi_driver_irsa" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.2"
  name = "${local.name}-efs-csi"

  attach_efs_csi_policy = true

  oidc_providers = {
    this = {
      provider_arn               = module.eks_al2023.oidc_provider_arn
      namespace_service_accounts = ["kube-system:efs-csi-controller-sa"]
    }
  }
  tags = local.tags
}

module "eks_al2023" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = "${local.name}-eks"
  kubernetes_version = "1.34"
  
  # Endpoint Access
  endpoint_public_access = true
  endpoint_public_access_cidrs  = local.endpoint_public_access_cidrs
  enable_cluster_creator_admin_permissions = true

  # EKS Addons
  addons = {
    aws-ebs-csi-driver = {
      service_account_role_arn = module.ebs_csi_driver_irsa.arn
    }
    aws-efs-csi-driver = {
      service_account_role_arn = module.efs_csi_driver_irsa.arn
    }
    coredns = {}
    eks-pod-identity-agent = {
      before_compute = true
    }
    kube-proxy = {}
    vpc-cni = {
      before_compute = true
    }
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    example = {
      # Starting on 1.30, AL2023 is the default AMI type for EKS managed node groups
      instance_types = local.instance_types
      ami_type       = "AL2023_x86_64_STANDARD"
      min_size = 2
      max_size = 8
      # This value is ignored after the initial creation
      # https://github.com/bryantbiggs/eks-desired-size-hack
      desired_size = 2

      # Increase Default Disk Size
      ebs_optimized = true
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 200
            volume_type           = "gp3"
            delete_on_termination = true
          }
        }
      }

      # This is not required - demonstrates how to pass additional configuration to nodeadm
      # Ref https://awslabs.github.io/amazon-eks-ami/nodeadm/doc/api/
      cloudinit_pre_nodeadm = [
        {
          content_type = "application/node.eks.aws"
          content      = <<-EOT
            ---
            apiVersion: node.eks.aws/v1alpha1
            kind: NodeConfig
            spec:
              kubelet:
                config:
                  shutdownGracePeriod: 30s
          EOT
        }
      ]
    }
  }

  tags = local.tags
}

################################################################################
# EFS File System
################################################################################

# Security Group for EFS
resource "aws_security_group" "efs" {
  name_prefix = "${local.name}-efs-"
  description = "Security group for EFS mount targets"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "NFS from EKS nodes"
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    security_groups = [module.eks_al2023.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name}-efs-sg"
  })
}

# EFS File System
resource "aws_efs_file_system" "main" {
  creation_token = "${local.name}-efs"
  
  # Performance and throughput settings
  performance_mode                = "generalPurpose"
  throughput_mode                 = "provisioned"
  provisioned_throughput_in_mibps = 50

  # Encryption
  encrypted = true

  # Lifecycle policy
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  lifecycle_policy {
    transition_to_primary_storage_class = "AFTER_1_ACCESS"
  }

  tags = merge(local.tags, {
    Name = "${local.name}-efs"
  })
}

# EFS Mount Targets (one per private subnet)
resource "aws_efs_mount_target" "main" {
  count           = length(module.vpc.private_subnets)
  file_system_id  = aws_efs_file_system.main.id
  subnet_id       = module.vpc.private_subnets[count.index]
  security_groups = [aws_security_group.efs.id]
}

# EFS Access Point for applications
resource "aws_efs_access_point" "main" {
  file_system_id = aws_efs_file_system.main.id

  posix_user {
    gid = 1001
    uid = 1001
  }

  root_directory {
    path = "/shared-data"
    
    creation_info {
      owner_gid   = 1001
      owner_uid   = 1001
      permissions = "755"
    }
  }

  tags = merge(local.tags, {
    Name = "${local.name}-efs-access-point"
  })
}

# Security Group Rule to allow EKS cluster security group to access EFS
resource "aws_security_group_rule" "eks_to_efs" {
  type                     = "egress"
  from_port                = 2049
  to_port                  = 2049
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.efs.id
  security_group_id        = module.eks_al2023.cluster_security_group_id
  description              = "Allow EKS cluster to access EFS"
}
