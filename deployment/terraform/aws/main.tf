# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

resource "random_id" "suffix" {
  byte_length = 4
}

# Data source for existing VPC
data "aws_vpc" "existing_vpc" {
  count = var.vpc_id != "" ? 1 : 0
  id    = var.vpc_id
}

# Create new VPC if not provided
resource "aws_vpc" "new_vpc" {
  count                = var.vpc_id == "" ? 1 : 0
  cidr_block          = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support  = true

  tags = merge(var.tags, {
    Name = "${var.resource_prefix}-${var.instance_name}-vpc-${random_id.suffix.hex}"
  })
}

locals {
  vpc_id = var.vpc_id != "" ? data.aws_vpc.existing_vpc[0].id : aws_vpc.new_vpc[0].id
}

# Internet Gateway for new VPC
resource "aws_internet_gateway" "new_igw" {
  count  = var.vpc_id == "" ? 1 : 0
  vpc_id = aws_vpc.new_vpc[0].id

  tags = merge(var.tags, {
    Name = "${var.resource_prefix}-${var.instance_name}-igw-${random_id.suffix.hex}"
  })
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Data source for existing subnet
data "aws_subnet" "existing_subnet" {
  count = var.subnet_id != "" ? 1 : 0
  id    = var.subnet_id
}

# Create new subnet if not provided
resource "aws_subnet" "new_subnet" {
  count                   = var.subnet_id == "" ? 1 : 0
  vpc_id                  = local.vpc_id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = var.instance_zone != "" ? var.instance_zone : data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.resource_prefix}-${var.instance_name}-subnet-${random_id.suffix.hex}"
  })
}

locals {
  subnet_id = var.subnet_id != "" ? data.aws_subnet.existing_subnet[0].id : aws_subnet.new_subnet[0].id
}

# Route table for new subnet
resource "aws_route_table" "new_rt" {
  count  = var.subnet_id == "" ? 1 : 0
  vpc_id = local.vpc_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.new_igw[0].id
  }

  tags = merge(var.tags, {
    Name = "${var.resource_prefix}-${var.instance_name}-rt-${random_id.suffix.hex}"
  })
}

# Route table association for new subnet
resource "aws_route_table_association" "new_rta" {
  count          = var.subnet_id == "" ? 1 : 0
  subnet_id      = aws_subnet.new_subnet[0].id
  route_table_id = aws_route_table.new_rt[0].id
}

# Data source for existing security group
data "aws_security_group" "existing_sg" {
  count = var.security_group_id != "" ? 1 : 0
  id    = var.security_group_id
}

# Create new security group if not provided
resource "aws_security_group" "new_sg" {
  count       = var.security_group_id == "" ? 1 : 0
  name_prefix = "${var.resource_prefix}-${var.instance_name}-sg"
  vpc_id      = local.vpc_id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  # HTTP access for services
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access for services
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Kubernetes API server
  ingress {
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.resource_prefix}-${var.instance_name}-sg-${random_id.suffix.hex}"
  })
}

locals {
  security_group_id = var.security_group_id != "" ? data.aws_security_group.existing_sg[0].id : aws_security_group.new_sg[0].id
}

# Data source for Ubuntu AMI
data "aws_ami" "ubuntu" {
  count       = var.ami_id == "" ? 1 : 0
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-${var.ubuntu_version}-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

locals {
  selected_ami = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu[0].id
}


# EC2 Instance
resource "aws_instance" "erag_instance" {
  ami                    = local.selected_ami
  instance_type          = var.instance_type
  key_name              = var.ssh_key_name
  subnet_id             = local.subnet_id
  vpc_security_group_ids = [local.security_group_id]
  availability_zone     = var.instance_zone != "" ? var.instance_zone : data.aws_availability_zones.available.names[0]

  root_block_device {
    volume_size = var.root_volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(var.tags, {
    Name = "${var.resource_prefix}-${var.instance_name}-${random_id.suffix.hex}"
  })
}

# Elastic IP for the instance
resource "aws_eip" "erag_eip" {
  instance = aws_instance.erag_instance.id
  domain   = "vpc"

  tags = merge(var.tags, {
    Name = "${var.resource_prefix}-${var.instance_name}-eip-${random_id.suffix.hex}"
  })

  depends_on = [aws_internet_gateway.new_igw]
}

data "template_file" "ansible_inventory" {
  template = file("${path.module}/../templates/inventory.ini.tpl")
  vars = {
    host_ip                     = aws_eip.erag_eip.public_ip
    ssh_user                    = var.ssh_user
    instance_name               = var.instance_name
  }
}

data "template_file" "erag_config" {
  template = file("${path.module}/../templates/config-override.yaml.tpl")
  vars = {
    fqdn                   = var.fqdn
    hugging_face_token     = var.hugging_face_token
    llm_model_cpu          = var.llm_model_cpu
    llm_model_gaudi        = ""
    embedding_model_name   = var.embedding_model_name
    reranking_model_name   = var.reranking_model_name
    deployment_type        = var.deployment_type
    vllm_size_vcpu         = var.vllm_size_vcpu
  }
}

# Wait for SSH to be ready
resource "null_resource" "wait_for_ssh" {
  provisioner "remote-exec" {
    inline = ["echo 'SSH is ready'"]

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_private_key)) ? file(var.ssh_private_key) : var.ssh_private_key
      host        = aws_eip.erag_eip.public_ip
      timeout     = "10m"

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
  }

  triggers = {
    instance_id = aws_instance.erag_instance.id
    ip_address  = aws_eip.erag_eip.public_ip
  }

  depends_on = [
    aws_instance.erag_instance,
    aws_eip.erag_eip
  ]

  # Transfer config files to the instance
  provisioner "file" {
    content     = data.template_file.erag_config.rendered

    destination = "/tmp/config-override.yaml"

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_private_key)) ? file(var.ssh_private_key) : var.ssh_private_key
      host        = aws_eip.erag_eip.public_ip

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
  }

  provisioner "file" {
    content     = data.template_file.ansible_inventory.rendered
    destination = "/tmp/inventory.ini"

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_private_key)) ? file(var.ssh_private_key) : var.ssh_private_key
      host        = aws_eip.erag_eip.public_ip

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
  }

  provisioner "file" {
    source      = "${path.module}/../scripts/run_install.sh"
    destination = "/tmp/run_install.sh"

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_private_key)) ? file(var.ssh_private_key) : var.ssh_private_key
      host        = aws_eip.erag_eip.public_ip

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
  }
}

# Run system installation stage
resource "null_resource" "run_install_system" {
  count = var.auto_install ? 1 : 0

  triggers = {
    always_run = timestamp()
  }

  depends_on = [null_resource.wait_for_ssh]

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_private_key)) ? file(var.ssh_private_key) : var.ssh_private_key
      host        = aws_eip.erag_eip.public_ip

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
    inline = [
      "chmod +x /tmp/run_install.sh",
      "/tmp/run_install.sh --platform aws --stage system"
    ]
  }
}

# Run cluster installation stage
resource "null_resource" "run_install_cluster" {
  count = var.auto_install ? 1 : 0

  triggers = {
    always_run = timestamp()
  }

  depends_on = [null_resource.run_install_system]

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_private_key)) ? file(var.ssh_private_key) : var.ssh_private_key
      host        = aws_eip.erag_eip.public_ip

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
    inline = [
      "/tmp/run_install.sh --platform aws --stage cluster"
    ]
  }
}

# Run application installation stage
resource "null_resource" "run_install_application" {
  count = var.auto_install ? 1 : 0

  triggers = {
    always_run = timestamp()
  }

  depends_on = [null_resource.run_install_cluster]

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_private_key)) ? file(var.ssh_private_key) : var.ssh_private_key
      host        = aws_eip.erag_eip.public_ip

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
    inline = [
      "/tmp/run_install.sh --platform aws --stage application"
    ]
  }
}
