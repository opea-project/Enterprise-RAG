# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

variable "aws_access_key" {
  description = "AWS Access Key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "instance_name" {
  description = "Instance name identifier"
  type        = string
  default     = "erag"
}

variable "instance_type" {
  description = "AWS instance type for CPU deployment"
  type        = string
  default     = "r8i.48xlarge"
}

variable "instance_zone" {
  description = "AWS availability zone"
  type        = string
  default     = ""
}

variable "vpc_id" {
  description = "Existing VPC ID (leave empty to create new VPC)"
  type        = string
  default     = ""
}

variable "subnet_id" {
  description = "Existing subnet ID (leave empty to create new subnet)"
  type        = string
  default     = ""
}

variable "security_group_id" {
  description = "Existing security group ID (leave empty to create new security group)"
  type        = string
  default     = ""
}

variable "ami_id" {
  description = "AMI ID for the instance (leave empty for auto-selection)"
  type        = string
  default     = ""
}

variable "ubuntu_version" {
  description = "Ubuntu version (24.04 or 22.04)"
  type        = string
  default     = "24.04"
  validation {
    condition     = contains(["24.04", "22.04"], var.ubuntu_version)
    error_message = "Ubuntu version must be either 24.04 or 22.04"
  }
}

variable "ssh_user" {
  description = "Username for SSH access to the instances"
  type        = string
  default     = "ubuntu"
}

variable "hugging_face_token" {
  description = "Hugging Face token for model access"
  type        = string
  sensitive   = true
}

variable "root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 300
}

variable "use_proxy" {
  description = "Whether to use proxy for SSH connections"
  type        = bool
  default     = false
}

variable "proxy_scheme" {
  description = "Proxy scheme (e.g., socks5, http)"
  type        = string
  default     = "socks5"
}

variable "proxy_host" {
  description = "Proxy host address"
  type        = string
  default     = ""
}

variable "proxy_port" {
  description = "Proxy port number"
  type        = number
  default     = 1080
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access"
  type        = string
  default     = "0.0.0.0/0"
}

variable "resource_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "erag"
}

variable "fqdn" {
  description = "Fully Qualified Domain Name for the Intel® AI for Enterprise RAG deployment"
  type        = string
  default     = "erag.com"
}

variable "llm_model_cpu" {
  description = "VLLM CPU model name"
  type        = string
  default     = ""
}

variable "reranking_model_name" {
  description = "Reranking model name"
  type        = string
  default     = ""
}

variable "embedding_model_name" {
  description = "Embedding model name"
  type        = string
  default     = ""
}

variable "deployment_type" {
  description = "This variable specifies where the model should be running (cpu for AWS)"
  type        = string
  default     = "cpu"
}

variable "ssh_key_name" {
  description = "AWS Key Pair name for SSH access"
  type        = string
}

variable "ssh_private_key" {
  description = "Path to the SSH private key file"
  type        = string
  default     = "~/.ssh/id_rsa"
}

variable "auto_install" {
  description = "Automatically run the installation script after instance creation"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project = "Enterprise-RAG"
    Terraform = "true"
  }
}

variable "osimage" {
  description = "Operating system image for the instance"
  type        = string
  default     = "ubuntu/images/hvm-ssd/ubuntu-24.04-amd64-server-*"
}

variable "vllm_size_vcpu" {
  description = "Number of vCPUs for the VLLM service"
  type        = number
  default     = 24
}

variable "solution_version" {
  description = "Intel® AI for Enterprise RAG solution version to deploy - can be a tag (e.g., 'release-2.0.0') or branch name (e.g., 'main', 'develop')"
  type        = string
  default     = "release-2.0.0"
}
