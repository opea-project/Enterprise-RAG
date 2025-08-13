# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

resource "random_id" "suffix" {
  byte_length = 4
}


resource "ibm_is_vpc" "new_vpc" {
  count          = var.vpc == "" ? 1 : 0
  name           = "${var.resource_prefix}-${lower(replace(var.resource_group, "_", "-"))}-vpc-${random_id.suffix.hex}"
  resource_group = data.ibm_resource_group.existing_resource_group.id
}

data "ibm_is_vpc" "existing_vpc" {
  count = var.vpc != "" ? 1 : 0
  name  = var.vpc
}

locals {
  vpc_id = var.vpc != "" ? data.ibm_is_vpc.existing_vpc[0].id : ibm_is_vpc.new_vpc[0].id
}

# Will be needed for multi-node
# data "ibm_is_public_gateway" "existing_public_gateway" {
#   count = var.vpc != "" ? 1 : 0
#   name  = var.public_gateway
# }

# resource "ibm_is_public_gateway" "new_public_gateway" {
#   count = var.vpc == "" ? 1 : 0
#   name  = "${var.resource_prefix}-${var.instance_name}-pg"
#   vpc   = local.vpc_id
#   zone  = var.instance_zone
#   resource_group = data.ibm_resource_group.existing_resource_group.id
# }

# locals {
#   pg_id = var.vpc != "" ? data.ibm_is_public_gateway.existing_public_gateway[0].id : ibm_is_public_gateway.new_public_gateway[0].id
# }

data "ibm_is_subnet" "existing_subnet" {
  count = var.subnet != "" ? 1 : 0
  name  = var.subnet
}

resource "ibm_is_subnet" "new_subnet" {
  count                     = var.subnet == "" ? 1 : 0
  name                      = "${var.resource_prefix}-${var.instance_name}-sn"
  vpc                       = local.vpc_id
#  public_gateway            = local.pg_id
  zone                      = var.instance_zone
  total_ipv4_address_count  = 256
  resource_group            = data.ibm_resource_group.existing_resource_group.id
}

locals {
  subnet_id = var.subnet != "" ? data.ibm_is_subnet.existing_subnet[0].id : ibm_is_subnet.new_subnet[0].id
}

data "ibm_is_security_group" "existing_security_group" {
  count = var.security_group != "" ? 1 : 0
  name  = var.security_group
  vpc   = local.vpc_id
}

resource "ibm_is_security_group" "new_security_group" {
  count          = var.security_group == "" ? 1 : 0
  name           = "${var.resource_prefix}-${var.instance_name}-sg"
  vpc            = local.vpc_id
  resource_group = data.ibm_resource_group.existing_resource_group.id
}

resource "ibm_is_security_group_rule" "ingress_ssh_restricted" {
    count     = var.security_group == "" ? 1 : 0
    group     = ibm_is_security_group.new_security_group[0].id
    direction = "inbound"
    remote    = var.ssh_allowed_cidr

    tcp {
      port_min = 22
      port_max = 22
    }
}

resource "ibm_is_security_group_rule" "egress_dns" {
  count     = var.security_group == "" ? 1 : 0
  group     = ibm_is_security_group.new_security_group[0].id
  direction = "outbound"
  remote    = "0.0.0.0/0"

  udp {
    port_min = 53
    port_max = 53
  }
}

resource "ibm_is_security_group_rule" "egress_https" {
  count     = var.security_group == "" ? 1 : 0
  group     = ibm_is_security_group.new_security_group[0].id
  direction = "outbound"
  remote    = "0.0.0.0/0"

  tcp {
    port_min = 443
    port_max = 443
  }
}

resource "ibm_is_security_group_rule" "egress_http" {
  count     = var.security_group == "" ? 1 : 0
  group     = ibm_is_security_group.new_security_group[0].id
  direction = "outbound"
  remote    = "0.0.0.0/0"

  tcp {
    port_min = 80
    port_max = 80
  }
}

resource "ibm_is_security_group_rule" "ingress_https" {
  count     = var.security_group == "" ? 1 : 0
  group     = ibm_is_security_group.new_security_group[0].id
  direction = "inbound"
  remote    = "0.0.0.0/0"

  tcp {
    port_min = 443
    port_max = 443
  }
}

resource "ibm_is_security_group_rule" "ingress_http" {
  count     = var.security_group == "" ? 1 : 0
  group     = ibm_is_security_group.new_security_group[0].id
  direction = "inbound"
  remote    = "0.0.0.0/0"

  tcp {
    port_min = 80
    port_max = 80
  }
}

locals {
  security_group_id = var.vpc != "" ? data.ibm_is_security_group.existing_security_group[0].id : ibm_is_security_group.new_security_group[0].id
}

data "ibm_is_image" "existing_image" {
  name = var.osimage
}

data "ibm_is_ssh_key" "existing_ssh_key_id" {
  name = var.ssh_key_name
}

data "ibm_resource_group" "existing_resource_group" {
  name = var.resource_group
}

resource "ibm_is_instance" "instance" {
  name           = var.instance_name
  vpc            = local.vpc_id
  zone           = var.instance_zone
  keys           = [data.ibm_is_ssh_key.existing_ssh_key_id.id]
  image          = data.ibm_is_image.existing_image.id
  profile        = var.instance_profile
  resource_group = data.ibm_resource_group.existing_resource_group.id

  primary_network_interface {
    subnet          = local.subnet_id
    security_groups = [local.security_group_id]
  }

  boot_volume {
    name     = "${var.instance_name}-boot-volume"
    size     = var.boot_volume_size
    profile  = "general-purpose"
  }
}

resource "ibm_is_floating_ip" "instance" {
    name    = var.instance_name
    target = ibm_is_instance.instance.primary_network_interface[0].id
    resource_group = data.ibm_resource_group.existing_resource_group.id
}

locals {
  floating_ip_address = ibm_is_floating_ip.instance.address
}

output "floating_ip" {
  value = ibm_is_floating_ip.instance.address
}

data "template_file" "ansible_inventory" {
  template = file("${path.module}/templates/inventory.ini.tpl")
  vars = {
    instance_name                  = var.instance_name
    ssh_user                       = var.ssh_user
    host_ip                        = ibm_is_instance.instance.primary_network_interface[0].primary_ip[0].address
  }
  depends_on = [
    ibm_is_instance.instance,
    ibm_is_floating_ip.instance
  ]
}

data "template_file" "erag_config" {
  template = file("${path.module}/templates/config-override.yaml.tpl")
  vars = {
    fqdn                                      = var.fqdn
    llm_model_gaudi                           = var.llm_model_gaudi
    llm_model_cpu                             = var.llm_model_cpu
    embedding_model_name                      = var.embedding_model_name
    reranking_model_name                      = var.reranking_model_name
    hugging_face_token                        = var.hugging_face_token
    deployment_type                           = var.deployment_type
  }
}

resource "null_resource" "wait_for_ssh" {
  provisioner "remote-exec" {
    inline = ["echo 'SSH is ready'"]

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_key)) ? file(var.ssh_key) : var.ssh_key
      host        = ibm_is_floating_ip.instance.address
      timeout     = "10m"

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
  }

  triggers = {
    instance_id = ibm_is_instance.instance.id
    ip_address  = ibm_is_floating_ip.instance.address
  }

  depends_on = [
    ibm_is_instance.instance,
    ibm_is_floating_ip.instance
  ]
}

resource "null_resource" "transfer_files" {
  triggers = {
    always_run = timestamp()
  }
  depends_on = [null_resource.wait_for_ssh]

  provisioner "file" {
    source      = "${path.module}/run_install.sh"
    destination = "/tmp/run_install.sh"

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_key)) ? file(var.ssh_key) : var.ssh_key
      host        = ibm_is_floating_ip.instance.address

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
  }

   provisioner "file" {
    content     = data.template_file.erag_config.rendered
    destination = "/tmp/config-override.yaml"

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_key)) ? file(var.ssh_key) : var.ssh_key
      host        = ibm_is_floating_ip.instance.address

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
      private_key = can(file(var.ssh_key)) ? file(var.ssh_key) : var.ssh_key
      host        = ibm_is_floating_ip.instance.address

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
  }
}

resource "null_resource" "run_install" {
  triggers = {
    always_run = timestamp()
  }

  depends_on = [null_resource.wait_for_ssh]
  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = can(file(var.ssh_key)) ? file(var.ssh_key) : var.ssh_key
      host        = ibm_is_floating_ip.instance.address

      proxy_scheme = var.use_proxy ? var.proxy_scheme : null
      proxy_host   = var.use_proxy ? var.proxy_host : null
      proxy_port   = var.use_proxy ? var.proxy_port : null
    }
    inline = [
      "chmod +x /tmp/run_install.sh",
      "/tmp/run_install.sh"
    ]
  }
}
