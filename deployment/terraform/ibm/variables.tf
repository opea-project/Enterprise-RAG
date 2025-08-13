# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

variable "api_key" {
  description = "IBM Cloud API key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "IBM Cloud region to deploy resources"
  type        = string
}

variable "ssh_key" {
  description = "SSH private key path for the instance"
  type        = string
}

variable "ssh_key_name" {
  description = "SSH key name for the instance"
  type        = string
}

variable "instance_name" {
  description = "IBM Cloud instance name"
  type        = string
}

variable "instance_zone" {
  description = "IBM Cloud instance zone"
  type        = string
}

variable "instance_profile" {
  description = "IBM Cloud instance profile"
  type        = string
  default     = "gx3d-160x1792x8gaudi3"
}

variable "vpc" {
  description = "IBM Cloud VPC"
  type        = string
  default     = ""
}

variable "security_group" {
  description = "IBM Cloud security_group"
  type        = string
  default     = ""
}

# Will be needed for multi-node
# variable "public_gateway" {
#   description = "IBM Cloud public_gateway"
#   type        = string
#   default     = ""
# }

variable "subnet" {
  description = "IBM Cloud subnet"
  type        = string
  default     = ""
}

variable "osimage" {
  description = "IBM Cloud instance image"
  type        = string
  default     = "ibm-ubuntu-24-04-2-minimal-amd64-5"
}

variable "resource_group" {
  description = "IBM Cloud resource_group"
  type        = string
}

variable "ssh_user" {
  description = "Username for SSH access to the instances"
  type        = string
  default     = "ubuntu"
}

variable "hugging_face_token" {
  description = "This variable specifies the hf token."
  type        = string
  sensitive   = true
}

variable "boot_volume_size" {
  description = "Boot volume size in GB(100-250)"
  type        = number
  default     = 100
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
  description = "Fully Qualified Domain Name for the eRAG deployment"
  type        = string
  default     = "erag.com"
}

variable "llm_model_cpu" {
  description = "VLLM CPU model name"
  type        = string
  default     = ""
}

variable "llm_model_gaudi" {
  description = "VLLM Gaudi model name"
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
  description = "This variable specifies where the model should be running (cpu/hpu)"
  type        = string
  default     = "hpu"
}
