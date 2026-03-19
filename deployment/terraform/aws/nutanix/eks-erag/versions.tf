# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
terraform {
  required_version = ">= 1.5.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.9"
    }
  }
}
