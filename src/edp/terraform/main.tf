# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

resource "random_string" "suffix" {
  length = 8
  special = false
  upper = false
}

resource "aws_s3_bucket" "edp_buckets" {
  count  = length(var.bucket_names)
  bucket = "${var.bucket_names[count.index]}-${random_string.suffix.result}"
}

resource "aws_sqs_queue" "edp_queue_1" {
  name = "${var.queue_name}-${random_string.suffix.result}"
  sqs_managed_sse_enabled = true
}

resource "aws_iam_user" "edp_user" {
  name = "edp-iam-user-${random_string.suffix.result}"
}

resource "aws_iam_access_key" "edp_access_key" {
  user = aws_iam_user.edp_user.name
}

resource "aws_iam_policy" "list_all_buckets" {
  name        = "list-all-buckets-policy-${random_string.suffix.result}"
  description = "Policy for listing all S3 buckets"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:ListAllMyBuckets"]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = ["s3:*"],
        Effect = "Deny",
        Resource = "*",
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "list_all_buckets_policy" {
  user       = aws_iam_user.edp_user.name
  policy_arn = aws_iam_policy.list_all_buckets.arn
}

resource "aws_iam_policy" "receive_message_queue" {
  name        = "receive-message-queue-policy-${random_string.suffix.result}"
  description = "Policy for receiving messages from the SQS queue"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage"]
        Effect   = "Allow"
        Resource = aws_sqs_queue.edp_queue_1.arn
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "receive_message_queue_policy" {
  user       = aws_iam_user.edp_user.name
  policy_arn = aws_iam_policy.receive_message_queue.arn
}

resource "aws_iam_policy" "read_only_bucket" {
  name        = "read-bucket1-policy-${random_string.suffix.result}"
  description = "Policy for read access to the first bucket"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:GetObject"]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.edp_buckets[0].arn}/*"
      },
      {
        Action = ["s3:*"],
        Effect = "Deny",
        Resource = ["${aws_s3_bucket.edp_buckets[0].arn}/*"],
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

resource "aws_iam_policy" "read_write_bucket_1" {
  name        = "read-write-bucket1-policy-${random_string.suffix.result}"
  description = "Policy for read-write access to the first bucket"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.edp_buckets[1].arn}/*"
      },
      {
        Action = ["s3:*"],
        Effect = "Deny",
        Resource = ["${aws_s3_bucket.edp_buckets[1].arn}/*"],
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

resource "aws_iam_policy" "read_write_bucket_2" {
  name        = "read-write-bucket2-policy-${random_string.suffix.result}"
  description = "Policy for read-write access to the second bucket"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.edp_buckets[2].arn}/*"
      },
      {
        Action = ["s3:*"],
        Effect = "Deny",
        Resource = ["${aws_s3_bucket.edp_buckets[1].arn}/*"],
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_cors_configuration" "edp_buckets_cors" {
  count  = length(var.bucket_names)
  bucket = aws_s3_bucket.edp_buckets[count.index].id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["https://erag.com"]
    max_age_seconds = 3000
  }
}

resource "aws_iam_user_policy_attachment" "read_only_bucket_policy" {
  user       = aws_iam_user.edp_user.name
  policy_arn = aws_iam_policy.read_only_bucket.arn
}

resource "aws_iam_user_policy_attachment" "read_write_bucket_policy_1" {
  user       = aws_iam_user.edp_user.name
  policy_arn = aws_iam_policy.read_write_bucket_1.arn
}

resource "aws_iam_user_policy_attachment" "read_write_bucket_policy_2" {
  user       = aws_iam_user.edp_user.name
  policy_arn = aws_iam_policy.read_write_bucket_2.arn
}

resource "aws_sqs_queue_policy" "edp_queue_policy_1" {
  queue_url = aws_sqs_queue.edp_queue_1.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "*"
      Effect = "Allow"
      Principal = {
        Service = "s3.amazonaws.com"
      }
      Action   = "SQS:SendMessage"
      Resource = aws_sqs_queue.edp_queue_1.arn
      Condition = {
        ArnLike = {
          "aws:SourceArn" = [
            aws_s3_bucket.edp_buckets[0].arn,
            aws_s3_bucket.edp_buckets[1].arn,
            aws_s3_bucket.edp_buckets[2].arn
          ]
        }
      }
    }]
  })
}

resource "aws_s3_bucket_notification" "edp_notification" {
  count  = length(var.bucket_names)
  bucket = aws_s3_bucket.edp_buckets[count.index].id

  queue {
    queue_arn     = aws_sqs_queue.edp_queue_1.arn
    events        = [ "s3:ObjectCreated:*", "s3:ObjectRemoved:*" ]
  }
}

output "queue_url" {
  value = aws_sqs_queue.edp_queue_1.id
}

output "access_key" {
  value = aws_iam_access_key.edp_access_key.id
}

output "secret_key" {
  value = aws_iam_access_key.edp_access_key.secret
  sensitive = true
}

output "region" {
  value = var.region
}

output "suffix" {
  value = random_string.suffix.result
}
