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
  image_id        = "45658166-3f45-47ef-9d1c-8d8cb4658a91"
  flavor_name     = "m1.small"
  security_groups = ["${openstack_compute_secgroup_v2.secgroup_1.name}"]

  network {
    name = openstack_networking_network_v2.network_1.name
  }

  # Automação Total: Instala Docker, Clona o Repo e Sobe o App
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose git
    systemctl start docker
    systemctl enable docker
    
    cd /home/ubuntu
    git clone https://github.com/milenahamerski/theorganizer.git
    cd theorganizer
    docker-compose up -d
  EOF

  # Automação no seu PC: Atualiza o /etc/hosts automaticamente
  provisioner "local-exec" {
    command = "echo '${self.access_ip_v4} theorganizer.com' | sudo tee -a /etc/hosts"
  }
}

# Output para ver o IP fácil no terminal
output "vm_ip" {
  value = openstack_compute_instance_v2.stack_instance.access_ip_v4
}
