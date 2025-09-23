output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.erag_instance.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.erag_eip.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.erag_instance.private_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_eip.erag_eip.public_dns
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = local.vpc_id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = local.subnet_id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = local.security_group_id
}

output "ssh_connection_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ${var.ssh_user}@${aws_eip.erag_eip.public_ip}"
}

output "selected_ami_info" {
  description = "Information about the selected AMI"
  value = {
    ami_id         = local.selected_ami
    ubuntu_version = var.ubuntu_version
    ami_name       = var.ami_id == "" ? data.aws_ami.ubuntu[0].name : "User-specified AMI"
  }
}

