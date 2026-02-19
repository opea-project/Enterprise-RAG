# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

variable "region" {
    description = "The AWS region"
    type        = string
    default     = "us-west-2"
}

variable "bucket_names" {
  description = "The names of the S3 buckets"
  type        = list(string)
  default     = ["edp-s3-read-only-bucket", "edp-s3-read-write-bucket-1", "edp-s3-read-write-bucket-2"]
}

variable "queue_name" {
  description = "The name of the SQS queue"
  type        = string
  default     = "edp-s3-notificaiton-queue"
}
