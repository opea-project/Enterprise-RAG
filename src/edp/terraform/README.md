# Setting Up S3 Bucket and SQS with Terraform

This Terraform configuration creates an S3 bucket and an SQS queue on AWS. It also sets up the S3 bucket to send notification events to the SQS queue.

## Prerequisites
 - Terraform installed to initialize, plan, and apply the infrastructure code.
 - Ensure your AWS credentials are configured in the `~/.aws/credentials` file with **sufficient IAM permissions to create and manage S3 buckets, SQS queues, and associated resources**. Make sure the credentials correspond to an IAM user or role with appropriate policies attached.

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
