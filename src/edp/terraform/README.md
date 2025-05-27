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

### Passing Terraform Outputs to ERAG Ansible Deployment
To use them in [Ansible-based deployment](../../../deployment/README.md), retrieve their values using the `terraform output -raw <output_name>` commands. Then, copy these output values and paste them into your config.yaml file under the appropriate fields before running the Ansible deployment.

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

### Passing Terraform Outputs to ERAG Bash-based Deployment
To use Terraform outputs with the [bash-based install_chatqna.sh deployment](../../../deployment/README_bash.md), export the variables before running `install_chatqna.sh` as shown below.

> Note: The `install_chatqna.sh` deployment script is deprecated and will be removed in version 1.3.0. It is recommended to use the Ansible-based deployment.

```bash
cd src/edp/terraform
export edp_storage_type="s3"
export s3_access_key=$(terraform output -raw access_key)
export s3_secret_key=$(terraform output -raw secret_key)
export s3_sqs_queue=$(terraform output -raw queue_url)
export s3_region=$(terraform output -raw region)

# Optional: regex pattern to filter S3 bucket names, so only matching buckets will be displayed in the Web UI
export s3_bucket_name_regex_filter="your-regex-pattern-here"
```

Then run the deployment script, for example:
```bash
cd ../../../deployment
./install_chatqna.sh --auth --deploy reference-cpu.yaml  --ui --kind
```

## Cleanup
To destroy the created infrastructure, run:

```bash
cd src/edp/terraform
terraform destroy
```
