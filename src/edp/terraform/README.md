# Setting Up S3 Bucket and SQS with Terraform

This Terraform configuration creates an S3 bucket and an SQS queue on AWS. It also sets up the S3 bucket to send notification events to the SQS queue.

## Prerequisites
 - **Terraform** must be installed to initialize, plan, and apply infrastructure as code.
 - **AWS credentials** must be properly configured in your `~/.aws/credentials` file. Ensure they are associated with sufficient IAM permissions to create and manage S3 buckets, SQS queues, and associated resources.

### Required IAM Permissions
The following IAM policy outlines the minimum required permissions to successfully provision the infrastructure:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:DeleteQueue",
        "sqs:GetQueueAttributes",
        "sqs:SetQueueAttributes",
        "sqs:ListQueueTags",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:PutBucketPolicy",
        "s3:GetBucketPolicy",
        "s3:DeleteBucketPolicy",
        "s3:GetBucketNotification",
        "s3:PutBucketNotification",
        "s3:GetBucketCORS",
        "s3:PutBucketCORS",
        "s3:ListBucket",
        "s3:GetBucketLogging",
        "s3:GetBucketTagging",
        "s3:GetBucketAcl",
        "s3:GetBucketWebsite",
        "s3:GetBucketVersioning",
        "s3:GetAccelerateConfiguration",
        "s3:GetBucketRequestPayment",
        "s3:GetReplicationConfiguration",
        "s3:GetEncryptionConfiguration",
        "s3:GetBucketObjectLockConfiguration",
        "s3:GetLifecycleConfiguration",
        "iam:CreateUser",
        "iam:GetUser",
        "iam:DeleteUser",
        "iam:CreatePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:DeletePolicy",
        "iam:ListGroupsForUser",
        "iam:AttachUserPolicy",
        "iam:ListAttachedUserPolicies",
        "iam:DetachUserPolicy",
        "iam:CreateAccessKey",
        "iam:ListAccessKeys",
        "iam:DeleteAccessKey"
      ],
      "Resource": "*"
    }
  ]
}
```
✅ Tip: If possible, assign this policy to a dedicated IAM role or user specifically for infrastructure provisioning, to follow the principle of least privilege.

## Configuration
To configure your bucket names or region, edit the `variables.tf` file or pass appropriate variables to `plan` and `apply` commands using `-var="key=value"` option.

## Usage
To run this terraform code, run the following command:

```
cd src/edp/terraform
terraform init
terraform plan
terraform apply
```

After `terraform apply` completes, it outputs the access key and SQS queue URL. To retrieve the secret key, run:

```bash
terraform output secret_key
```

### Passing Terraform Outputs to ERAG Deployment
To use them in [deployment](../../../deployment/README.md), retrieve their values using the `terraform output -raw <output_name>` commands. Then, copy these output values and paste them into your config.yaml file under the appropriate fields before running the deployment.

For example, get the outputs with:

```bash
terraform output -raw access_key
terraform output -raw secret_key
terraform output -raw queue_url
terraform output -raw region
```

Then insert these values into config.yaml like this:

```yaml
edp:
  enabled: true
  storageType: s3
  s3:
    accessKey: "<paste access_key here>"
    secretKey: "<paste secret_key here>"
    sqsQueue: "<paste queue_url here>"
    region: "<paste region here>"
    bucketNameRegexFilter: ".*"
```

Then run deployment as usual, an example for installation:
```bash
ansible-playbook playbooks/application.yaml --tags install -e @path/to/your/config.yaml
```

## Cleanup
To destroy the created infrastructure, run:

```bash
cd src/edp/terraform
terraform destroy
```
