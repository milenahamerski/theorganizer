# Definição da Rede
resource "openstack_networking_network_v2" "network_1" {
  name           = "theorganizer_net"
  admin_state_up = "true"
}

# Definição da Sub-rede
resource "openstack_networking_subnet_v2" "subnet_1" {
  name       = "theorganizer_subnet"
  network_id = openstack_networking_network_v2.network_1.id
  cidr       = "192.168.10.0/24"
  ip_version = 4
}

# Definição do Grupo de Segurança
resource "openstack_compute_secgroup_v2" "secgroup_1" {
  name        = "theorganizer_sg"
  description = "Grupo de seguranca para o projeto TheOrganizer"

  rule {
    from_port   = 22
    to_port     = 22
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }

  rule {
    from_port   = 80
    to_port     = 80
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }

  rule {
    from_port   = 443
    to_port     = 443
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }

  rule {
    from_port   = 8000
    to_port     = 8000
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

# VM Única para tudo (App + DB via Docker Compose)
resource "openstack_compute_instance_v2" "stack_instance" {
  name            = "theorganizer_stack"
  image_id        = "45658166-3f45-47ef-9d1c-8d8cb4658a91" # Usando o ID para não ter erro de busca
  flavor_name     = "m1.small"                   # Flavor m1.small para aguentar o Ubuntu + Docker
  security_groups = ["${openstack_compute_secgroup_v2.secgroup_1.name}"]

  network {
    name = openstack_networking_network_v2.network_1.name
  }
}
