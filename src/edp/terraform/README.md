This is an example configuration to create an S3 Bucket and SQS. This terraform code also configures the S3 bucket to send notification events on SQS.

To create this example infrastructure on your AWS account, ensure you have AWS credentials in `~/.aws/credentials` file.

To configure your bucket names or region, edit the `variables.tf` file or pass appropriate variables to `plan` and `apply` commands using `-var="foo=bar"` arguments.

To run this terraform code, run the following command:

```
cd src/edp/terraform
terraform init
terraform plan
terraform apply
```

`terraform apply` will output key and queue uri, to get secret key run the following command:
```
terraform output secret_key
```

To use them in deployment export those variables before running `install_chatqna.sh` as following:

```
cd src/edp/terraform
export edp_storage_type="s3"
export s3_access_key=$(terraform output -raw access_key)
export s3_secret_key=$(terraform output -raw secret_key)
export s3_sqs_queue=$(terraform output -raw queue_url)
export s3_region=$(terraform output -raw region)

# Optional: regex pattern to filter S3 bucket names, so only matching buckets will be displayed in the Web UI
export s3_bucket_name_regex_filter="your-regex-pattern-here"

cd ../../../deployment
./install_chatqna.sh --auth --deploy xeon_torch --ui --upgrade --kind
```

To remove created infrastructure run
```
cd src/edp/terraform
terraform destroy
```
