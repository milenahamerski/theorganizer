# 📄 TheOrganizer - Deploy com OpenStack + Multipass

🧠 **Visão Geral**

Este projeto implementa uma arquitetura de nuvem privada utilizando três máquinas virtuais. Aqui está o passo a passo completo, sequencial e detalhado para você colocar a aplicação "TheOrganizer" no ar do zero!

```mermaid
flowchart LR

    subgraph LOCAL["💻 Máquina Local (Host)"]
        USER["Usuário / Navegador"]
    end

    subgraph DOMAIN["🌐 VM: domain (DNS + CA)"]
        DNS["Bind9 (DNS)"]
        CA["Certificadora (Easy-RSA)"]
    end

    subgraph OPENSTACK["☁️ VM: openstack"]
        DEVSTACK["DevStack"]
        HORIZON["Horizon (Dashboard)"]
        NETWORK["Rede (Neutron)"]
        COMPUTE["Compute (Nova)"]
    end

    subgraph STACK["⚙️ VM: stack"]
        TERRAFORM["Terraform"]
        
        subgraph INSTANCIA_WEB["⚙️ VM instanciada no OpenStack"]
            NGINX["Nginx (Proxy HTTPS)"]
            DOCKER["Docker"]
            FASTAPI["TheOrganizer"]
        end
    end

    %% Fluxos
    USER -->|Acessa https://theorganizer.com| DNS
    DNS -->|Resolve domínio| NGINX

    NGINX --> FASTAPI

    %% OpenStack integração
    TERRAFORM -->|Provisiona VM Web via API| OPENSTACK
    OPENSTACK --> NETWORK
    OPENSTACK --> COMPUTE

    %% Certificado
    CA -->|Gera certificado SSL| NGINX
    CA -.->|Exporta CA Root| LOCAL
```

---

## 🖥️ 1. Infraestrutura Base (Criação das VMs)

> [!NOTE]
> **Onde executar:** Terminal da sua máquina real (Host / Localhost).

Vamos criar 3 VMs usando o Multipass com as especificações recomendadas para cada serviço.

```bash
multipass launch -c 8 -m 8G -d 80G -n openstack lts
multipass launch -c 1 -m 2G -d 10G -n domain lts
multipass launch -c 1 -m 2G -d 10G -n stack lts
```

Verifique os IPs de cada máquina que acabou de criar:
```bash
multipass list
```
*(Anote os IPs de `openstack`, `domain` e `stack`, pois você usará eles bastante).*

---

## ☁️ 2. OpenStack (DevStack)

> [!NOTE]
> **Onde executar:** Dentro da VM **openstack** (`multipass shell openstack`)

Vamos instalar o OpenStack em um modo minimalista (DevStack).

### 2.1 Clone do DevStack e Neutron
```bash
git clone https://opendev.org/openstack/devstack.git
sudo ./devstack/tools/create-stack-user.sh

sudo cp -r devstack /opt/stack
sudo chown -R stack:stack /opt/stack/devstack
sudo su - stack
cd /opt/stack
git clone https://opendev.org/openstack/neutron.git
```

### 2.2 Configurando `local.conf`
```bash
cd devstack
cp ../neutron/devstack/ml2-ovs-local.conf.sample local.conf
nano local.conf
```

Dentro do editor:
1. Busque a linha `HOST_IP=` e descomente colocando o **IP da sua VM openstack**. Exemplo: `HOST_IP=10.x.x.x`
2. Comente a seguinte linha adicionando `#` na frente dela:
   `#disable_service cinder c-sch c-api c-vol`

Salve (Ctrl+O, Enter) e saia (Ctrl+X).

### 2.3 Instalação
```bash
./stack.sh
```
*(Este passo demora bastante. Vá tomar um café! ☕)*

### 2.4 Arrumando possíveis quebras do DevStack (Troubleshooting)

**1) Parar e reiniciar o Serviço N_CPU!**
Se a máquina ficar dando problema ao reiniciar:
```bash
sudo nano /etc/init.d/restart-devstack-n-cpu.sh
```
Cole o script:
```bash
#!/bin/bash
sleep 60
sudo systemctl restart devstack@n-cpu.service
```
Dê permissão e coloque na inicialização:
```bash
sudo chmod +rx /etc/init.d/restart-devstack-n-cpu.sh
sudo update-rc.d restart-devstack-n-cpu.sh defaults
```

**2) Perdeu o IP da bridge br-ex! (172.24.4.1)**
```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```
Crie/Adicione a configuração de `bridges` (atenção à indentação correta):
```yaml
network:
  version: 2
  ethernets:
    default:
      match:
        macaddress: "SEU_MAC_AQUI" # (Não mude a linha macaddress que já existe)
      dhcp-identifier: mac
      dhcp4: true

  bridges:
    br-ex:
      interfaces: [default]
      addresses: [172.24.4.1/24]
      openvswitch: {}
```
Aplique:
```bash
sudo netplan apply
```

**3) Perde a entrada NAT iptables! (172.24.4.x - roteador)**
Verifique as rotas `sudo iptables -L -n -v -t nat`. Para consertar definitivamente:
```bash
sudo apt-get install iptables-persistent -y
sudo nano /etc/iptables/rules.v4
```
Cole:
```bash
*nat
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 172.24.4.0/24 -o ens3 -j MASQUERADE
COMMIT
```
Restaurar:
```bash
sudo iptables-restore < /etc/iptables/rules.v4
```

### 2.5 Configurações Iniciais no Horizon (Dashboard)

> [!NOTE]
> **Onde acessar:** Navegador do seu computador, acessando `http://IP_DA_VM_OPENSTACK`

1. Faça Login no Dashboard do OpenStack:
   - **User:** `admin`
   - **Password:** `password` (ou a senha que apareceu no final do stack.sh)
2. Acesse: `Identity` > `Projects` > **Create Project** -> Nomeie como `theorganizer`.
3. Acesse: `Identity` > `Users` > **Create User** -> Crie o user `devops` com a senha `devops` e atribua o projeto `theorganizer` a ele.
4. **Baixar Imagem Ubuntu Jammy:**
   - Acesse: `https://cloud-images.ubuntu.com/jammy/current/`
   - Baixe o arquivo `.img` (Exemplo: `jammy-server-cloudimg-amd64.img`).
5. **Upload da Imagem no Horizon:**
   - Vá em `Admin` > `Compute` > `Images` > **Create Image**.
   - Coloque o nome da Imagem.
   - Faça o upload do arquivo `.img` que você baixou.
6. **Baixar o arquivo RC (Variáveis de Ambiente):**
   - Acesse o projeto `theorganizer` logado como usuário `devops` (Faça logout do admin e entre como devops).
   - Clique no canto superior direito no seu usuário > **OpenStack RC File** (ou `api_access/openrc/`). Isso fará o download de um arquivo shell (ex: `theorganizer-openrc.sh`). **Guarde este arquivo**.

---

## 🌐 3. Domain (DNS e CA)

> [!NOTE]
> **Onde executar:** Dentro da VM **domain** (`multipass shell domain`)

### 3.1 Instalação Automática do BIND9 (DNS)

Crie o arquivo `setup_dns.sh` na máquina `domain`:
```bash
nano setup_dns.sh
```

Cole o conteúdo ajustando os IPs para os da sua rede:
```bash
#!/bin/bash
set -e

# ===== CONFIGURAÇÕES =====
ZONA="theorganizer.com"
EMAIL_ADMIN="admin.theorganizer.com"

# COLOQUE OS IPs REAIS DAS SUAS MÁQUINAS AQUI
IP_DNS="10.x.x.x"       # IP da VM domain
IP_DOMAIN="10.x.x.x"    # IP da VM domain
IP_OPENSTACK="10.x.x.x" # IP da VM openstack
IP_STACK="10.x.x.x"     # IP da VM stack
IP_WEB="172.24.4.x"     # IP que a VM web do OpenStack vai receber (Floating IP)

# ===== INSTALAR BIND9 =====
sudo apt-get update
sudo apt-get install -y bind9

# ===== CONFIGURAR named.conf.options =====
sudo tee /etc/bind/named.conf.options > /dev/null <<EOF
options {
        directory "/var/cache/bind";
        dnssec-validation no;
        allow-query { any; };
        listen-on-v6 { any; };
};
EOF

sudo systemctl restart bind9

# ===== CONFIGURAR named.conf.local =====
sudo tee /etc/bind/named.conf.local > /dev/null <<EOF
zone "$ZONA" IN {
    type master;
    file "db.$ZONA";
};
EOF

# ===== CRIAR ARQUIVO DA ZONA =====
SERIAL=$(date +%Y%m%d01)

sudo tee /var/cache/bind/db.$ZONA > /dev/null <<EOF
\$ORIGIN $ZONA.
\$TTL 300

@ IN SOA domain.$ZONA. $EMAIL_ADMIN. (
    $SERIAL  ; Serial
    3600     ; Refresh
    1800     ; Retry
    604800   ; Expire
    86400    ; Minimum TTL
)

@               IN NS domain.$ZONA.

; Registros A
@               IN A $IP_WEB
domain          IN A $IP_DOMAIN
openstack       IN A $IP_OPENSTACK
stack           IN A $IP_STACK
web             IN A $IP_WEB

; Alias
www             IN CNAME @
EOF

# ===== CHECAR ZONA =====
sudo named-checkzone "$ZONA" "/var/cache/bind/db.$ZONA"

# ===== REINICIAR SERVIÇO =====
sudo systemctl restart bind9
sudo systemctl status bind9 --no-pager

echo "✅ Bind9 configurado com sucesso para a zona $ZONA."
```
Dê permissão e rode:
```bash
chmod +x setup_dns.sh
sudo ./setup_dns.sh
```

### 3.2 Configurando o DNS no seu Host (Micro-Cliente / Local)

> [!IMPORTANT]
> **Onde executar:** Terminal da sua MÁQUINA REAL (utfpr@utfpr). NÃO rode isso dentro da VM.

Para que o seu PC enxergue o DNS recém-criado:
```bash
sudo nano /etc/systemd/resolved.conf 
```
Localize a linha `DNS=`, descomente e coloque o IP da VM `domain`:
```ini
DNS=10.x.x.x  # <-- IP da VM domain
```
Reinicie o serviço no seu computador:
```bash
sudo systemctl restart systemd-resolved.service
```

### 3.3 Configurando a Certificadora (CA) e Gerando o Certificado

> [!NOTE]
> **Onde executar:** VM **domain**

**Script para Inicializar a CA (certificadora.sh):**
```bash
nano certificadora.sh
```
```bash
#!/bin/bash
set -e

CA_DIR=~/certificadora
EASYRSA_DIR="$CA_DIR/easy-rsa"

echo "[INFO] Instalando Easy-RSA..."
sudo apt-get install -y easy-rsa

echo "[INFO] Criando diretório da CA..."
mkdir -p "$CA_DIR"
cp -R /usr/share/easy-rsa "$CA_DIR"
sudo chown -R $USER:$USER "$EASYRSA_DIR"

cd "$EASYRSA_DIR"

echo "[INFO] Gerando arquivo vars com dados da CA..."
cat > vars <<EOF
set_var EASYRSA_DN             "org"
set_var EASYRSA_REQ_COUNTRY    "BR"
set_var EASYRSA_REQ_PROVINCE   "PR"
set_var EASYRSA_REQ_CITY       "Guarapuava"
set_var EASYRSA_REQ_ORG        "TheOrganizer CA"
set_var EASYRSA_REQ_EMAIL      "admin@theorganizer.com"
set_var EASYRSA_REQ_OU         "IT Department"
EOF

echo "[INFO OK] Inicializando PKI..."
./easyrsa init-pki

echo "[INFO] Criando a CA (será solicitada uma senha)..."
./easyrsa build-ca

echo "✅ CA criada com sucesso!"
```
Execute `chmod +x certificadora.sh && ./certificadora.sh` e preencha o `Common Name` da CA (Ex: `Easy-RSA CA theorganizer`).

**Script para o Certificado do Domínio (certificado.sh):**
```bash
nano certificado.sh
```
```bash
#!/bin/bash
set -e

cd ~/certificadora/easy-rsa

echo "[INFO] Gerando requisição e Certificado do Domínio..."
./easyrsa gen-req theorganizer nopass

echo "[INFO] Assinando o certificado com a CA..."
./easyrsa sign-req server theorganizer

echo "[INFO] Copiando para pastas do sistema..."
sudo cp pki/issued/theorganizer.crt /etc/ssl/certs
sudo cp pki/private/theorganizer.key /etc/ssl/private

echo "✅ Certificado theorganizer.crt criado com sucesso!"
```
Execute `chmod +x certificado.sh && ./certificado.sh` e preencha o `Common Name` (Ex: `*.theorganizer.com`).

### 3.4 Exportando o Certificado da CA para o seu PC (Host / Navegador)

> [!IMPORTANT]
> **Onde executar:** Terminal da sua MÁQUINA REAL (utfpr@utfpr).

Para o seu Firefox não dar aviso de "Site Inseguro", vamos puxar o certificado da VM para o seu PC usando o comando oficial do Multipass:

**1. Baixe o certificado via Multipass Transfer:**
```bash
multipass transfer domain:/home/ubuntu/certificadora/easy-rsa/pki/ca.crt ~/Downloads/ca.crt
```

**2. Importe no Firefox do seu PC:**
*   Abra o **Firefox**.
*   Vá em `Configurações` -> `Privacidade e Segurança`.
*   Role até o fim em `Certificados` -> `Ver Certificados`.
*   Aba `Autoridades` -> `Importar`.
*   Selecione o `ca.crt` que está na sua pasta `Downloads`.
*   Marque a caixa: **"Confiar nesta CA para identificar sites"**.

### 3.5 Transferindo Certificados para a Instância Final

> [!IMPORTANT]
> **Onde executar:** Terminal da sua MÁQUINA REAL (Host).
> Como a instância web está dentro de uma rede isolada do OpenStack, usaremos o Host como ponte para mover os certificados da VM `domain` para lá.

**1. Baixe os certificados da VM `domain` para o seu PC:**
```bash
multipass transfer domain:/home/ubuntu/certificadora/easy-rsa/pki/issued/theorganizer.crt ~/Downloads/
multipass transfer domain:/home/ubuntu/certificadora/easy-rsa/pki/private/theorganizer.key ~/Downloads/
```

**2. Envie os certificados para a instância web (após ela ter sido criada pelo Terraform):**
*(Use o Floating IP que você anotou no Passo 4.4)*
```bash
scp ~/Downloads/theorganizer.crt ubuntu@IP_FLOATING_WEB:/home/ubuntu/
scp ~/Downloads/theorganizer.key ubuntu@IP_FLOATING_WEB:/home/ubuntu/
```

---

## ⚙️ 4. Stack (DevOps e Deploy)

> [!NOTE]
> **Onde executar:** Dentro da VM **stack** (`multipass shell stack`)

### 4.1 Roteamento e Preparação
Para a VM Stack achar a rede privada do OpenStack:
```bash
sudo ip route add 172.24.4.0/24 via IP_DA_VM_OPENSTACK
```
E repita este comando também no **Terminal do Host (seu PC local)** se for acessar a instância direto!

### 4.2 Instalar o Terraform

Rode este bloco de comandos para instalar o repositório oficial da Hashicorp e o Terraform:

```bash
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common && \
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null && \
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list && \
sudo apt-get update && sudo apt-get install terraform -y
```

### 4.3 Configurar o Projeto Terraform

```bash
mkdir theorganizer-tf
cd theorganizer-tf
```

#### Arquivo `providers.tf`:
```bash
nano providers.tf
```
```hcl
terraform {
  required_version = ">= 0.14.0"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.53.0"
    }
  }
}

provider "openstack" {
  user_name   = "devops"
  tenant_name = "theorganizer"
  password    = "devops"
  auth_url    = "http://IP_DA_SUA_VM_OPENSTACK/identity"
  region      = "RegionOne"
}
```
*(As credenciais estão no arquivo `theorganizer-openrc.sh` que você baixou no passo 2).*

#### Arquivo `main.tf`:
```bash
nano main.tf
```
> [!IMPORTANT]
> - `external_network_id`: Precisa pegar no Horizon (ID da rede pública do OpenStack).
> - `image_id` e UUID do `block_device`: É o ID da imagem Jammy que você subiu no Horizon.
> - `public_key`: Coloque a SUA chave SSH pública (`cat ~/.ssh/id_rsa.pub` da VM stack).

```hcl
resource "openstack_networking_network_v2" "network_theorganizer" {
  name           = "network_theorganizer"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "subnet_theorganizer" {
  name       = "subnet_theorganizer"
  network_id = openstack_networking_network_v2.network_theorganizer.id
  cidr       = "10.10.10.0/24"
  ip_version = 4
  dns_nameservers = ["IP_DA_VM_DOMAIN"]
  enable_dhcp     = true
  gateway_ip      = "10.10.10.1"
  
  allocation_pool {
    start = "10.10.10.200"
    end   = "10.10.10.254"
  }
}

resource "openstack_networking_router_v2" "router_theorganizer" {
  name                = "router_theorganizer"
  admin_state_up      = true
  external_network_id = "ID_DA_REDE_PUBLICA_NO_OPENSTACK" # <-- Altere isto!
}

resource "openstack_networking_router_interface_v2" "router_int_theorganizer" {
  router_id = openstack_networking_router_v2.router_theorganizer.id
  subnet_id = openstack_networking_subnet_v2.subnet_theorganizer.id
}

resource "openstack_compute_keypair_v2" "ubuntu_stack" {
  name       = "ubuntu_stack"
  public_key = "ssh-ed25519 AAAAC3... ubuntu@stack" # <-- Altere isto!
}

resource "openstack_networking_secgroup_v2" "secgroup_access" {
  name        = "secgroup_access"
  description = "Ping and SSH"
}

resource "openstack_networking_secgroup_rule_v2" "secgroup_rule_ssh" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.secgroup_access.id
}

resource "openstack_networking_secgroup_rule_v2" "secgroup_rule_ping" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "icmp"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.secgroup_access.id
}

resource "openstack_networking_secgroup_v2" "secgroup_webserver" {
  name        = "secgroup_webserver"
  description = "Web HTTP/HTTPS"
}

resource "openstack_networking_secgroup_rule_v2" "secgroup_rule_http" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.secgroup_webserver.id
}

resource "openstack_networking_secgroup_rule_v2" "secgroup_rule_https" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.secgroup_webserver.id
}

resource "openstack_compute_instance_v2" "instance_web" {
  name            = "instance_web"
  image_id        = "ID_DA_IMAGEM_JAMMY_NO_OPENSTACK" # <-- Altere isto!
  flavor_id       = "d4" # (Ou outro sabor configurado)
  key_pair        = "ubuntu_stack"
  security_groups = ["default", "secgroup_access", "secgroup_webserver"]
  
  block_device {
    uuid                  = "ID_DA_IMAGEM_JAMMY_NO_OPENSTACK" # <-- Altere isto!
    source_type           = "image"
    destination_type      = "local"
    boot_index            = 0
    delete_on_termination = true
  }

  block_device {
    source_type           = "blank"
    destination_type      = "volume"
    volume_size           = 15
    boot_index            = 1
    delete_on_termination = true
  }

  network {
    name = "network_theorganizer"
  }
  
  depends_on = [
      openstack_networking_subnet_v2.subnet_theorganizer
  ]
}

resource "openstack_networking_floatingip_v2" "floatip_web" {
  pool = "public"
}

resource "openstack_compute_floatingip_associate_v2" "myip_web" {
  floating_ip = openstack_networking_floatingip_v2.floatip_web.address
  instance_id = openstack_compute_instance_v2.instance_web.id
}
```

### 4.4 Aplicando o Terraform
Ainda na pasta `theorganizer-tf` da VM `stack`:
```bash
terraform init
terraform validate
terraform plan
terraform apply
```
*Digite `yes` para confirmar a criação.*

---

## 🚀 5. Acesso à Aplicação Web (Instância criada)

> [!NOTE]
> **Onde executar:** SSH para dentro da Instância recém-criada (a partir da VM Stack ou Host).

Acesse a instância Web que o Terraform acabou de criar:
```bash
ssh ubuntu@IP_FLOATING_WEB
```

### 5.1 Configurando Nginx e Proxy (Script Automático)

Crie o arquivo `setup_nginx.sh` na instância:
```bash
nano setup_nginx.sh
```

```bash
#!/bin/bash
set -e

# ===== CONFIGURAÇÕES =====
DOMINIO="theorganizer.com"
RAIZ_APP="/var/www/theorganizer/public"
PROXY_PORT="8000" # Porta da Aplicação Dockerizada
CERT_PATH="/etc/ssl/certs/theorganizer.crt"
KEY_PATH="/etc/ssl/private/theorganizer.key"
LOG_DIR="/var/www/logs"

# ===== INSTALAR NGINX =====
sudo apt-get update
sudo apt-get install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# ===== CRIAR ARQUIVO DE CONFIGURAÇÃO DO SITE =====
CONF_PATH="/etc/nginx/sites-available/$DOMINIO"

sudo tee "$CONF_PATH" > /dev/null <<EOF
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMINIO www.$DOMINIO;

    ssl_certificate $CERT_PATH;
    ssl_certificate_key $KEY_PATH;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";

    root $RAIZ_APP;

    location / {
        proxy_pass http://0.0.0.0:$PROXY_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    error_page 500 502 503 504 /500.html;
    client_max_body_size 4G;
    keepalive_timeout 10;

    access_log $LOG_DIR/nginx_access.log;
    error_log $LOG_DIR/nginx_error.log;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMINIO www.$DOMINIO;
    return 301 https://$DOMINIO\$request_uri;
}
EOF

# ===== CRIAR DIRETÓRIO E LOGS =====
sudo mkdir -p "$LOG_DIR"
sudo touch "$LOG_DIR/nginx_access.log" "$LOG_DIR/nginx_error.log"

# ===== ATIVAR CONFIGURAÇÃO =====
sudo ln -sf "$CONF_PATH" "/etc/nginx/sites-enabled/$DOMINIO"

# ===== TESTAR E REINICIAR NGINX =====
sudo nginx -t
sudo systemctl restart nginx

echo "✅ NGINX configurado com sucesso para $DOMINIO"
```
Execute:
```bash
chmod +x setup_nginx.sh
sudo ./setup_nginx.sh
```

*(Como você enviou os certificados para `/home/ubuntu` no passo 3.5, agora mova-os para as pastas do sistema na instância web):*
```bash
sudo mv ~/theorganizer.crt /etc/ssl/certs/
sudo mv ~/theorganizer.key /etc/ssl/private/
```

### 5.2 Instalar Docker na Instância Web e Subir a App

Crie o arquivo `install_docker.sh`:
```bash
nano install_docker.sh
```

```bash
#!/bin/bash
set -e

echo "🐳 Instalando Docker (modo rápido)..."

# 1. Dependências mínimas
sudo apt update
sudo apt install -y ca-certificates curl gnupg

# 2. Chave GPG
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. Repositório Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 5. Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# 6. Docker sem sudo
sudo usermod -aG docker $USER

echo "✅ Docker instalado! Saia (exit) e entre novamente no SSH para usar sem sudo."
```

Execute:
```bash
chmod +x install_docker.sh
./install_docker.sh
```

Saia e entre novamente no SSH. Em seguida, suba o container:
```bash
git clone https://github.com/milenahamerski/theorganizer.git
cd theorganizer
docker compose up -d
```

---

## 🎯 6. Acesso Final (Teste de Sucesso)

Se você já configurou o DNS no `resolved.conf` local (Passo 3.2), é só acessar no navegador do seu Host:

`https://theorganizer.com`

**Parabéns! Sua nuvem privada e a aplicação TheOrganizer estão no ar! 🚀**

---

## 🔑 Anexos: Exemplos de Chave e Certificado (Referência)

Estes são os conteúdos originais (em Base64) gerados caso precise validar a integridade.

### `theorganizer.key`
```bash
-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC2klIR9Z8OJ+es
BzrhJ6i0i6B8IXUNTc+IkEKw9vX0hnAxQJjTVlbU6MoQ5RokUys/+lJWmLDzZaoy
6KRAdolS5axtRPuai5MLVvQR15aRVV/jPl+de8mVyUABTYCQix1j61snGn0GpHV+
yUlYcitdO3SCfzVH07IiPlx/OkpRUq4duKSLTUCJS/XsQO9t/bbuyoI1vmmsPkVA
gOldkOytCIgInuAI3d6+VFkgFW/z3DVy3yeECJ2eeJB1xc/KAZmjfctLK0U8HLCP
YJW3RdRXtKxVuWBP/LgTs4SmoHb52ow79txO2fJ35hK0Kp7PSrhL3TT5DMrj6XrH
vQvFiC/1AgMBAAECggEAJ1IQrG8I1FjqV73P482xkz7uL8XZ6qVbQOeHAYuS0dkB
gU4PDBcwiNbhLC3XiULDUhpk0OM+WxGGjEPYGk0dStYN4pPEl5afcwYFd3FF66Om
TPAyUh3mvuSS7STmv1rC1/II1f1pt3xElOufqRWfusrzDyb8D+3rU943+CvS9Tv6
sseGRkjaOWipeMkEUGYiD05QBLNhN88B+T6f5ixcwlWZ0H6H/nFvYtnTZgLkhj5j
9TJJGWMFP/adm0sH2QN/CqvFmcrXbeDbmBZJ7oacQ+NZepEA8eNpRTW4AiA1pcoF
tiXTnw4uhI7yPh6RyBSqKvS1Q4hDBCAmGBm6GZoAUQKBgQDrA0tSYjKRzfBzamoT
Xm0VhPft5L+UTliXxIfv8NEP159w6eBXB2bB4BPHvXyJucnsqUdAYVe61r1Fvfcr
11OESR8CUGXjkxPixDIu6wCFV+3JT1YwDxzTv5anFYZF9MDXK23qVkZnjfn1OOTj
fhR72VNfcImOvo4M/X+bTM3oRQKBgQDG4CYM5zSZqTMl34Wc5T9lON0pNllzw2pN
5uXVJAiEMJMNXqTYIQw3T7Rox3vf9mmlmQW/xmTTXS7yMVPXR5GcnJHBHIjBHbyR
3q5DTpymwDIECAihRZs+q+xq3vJ3ZEfVlx7J5jmncGHNEdhYKexmc12rwl6PmeFU
rLrO36Bb8QKBgGAdScnYtVviQMvDIrznKm/ZoNhfbGbIH/15+CqOb8It6lxwmjqd
oU37Sbuv6GYfYND0blqLNSkJuAD070iz2MlKam802GbZeRGOMgP0QpNGYc6qLtKa
66xCN+f/qpmjvtaBQYPMYyDo9Ohwq1PK9a+tMybeTLPfhRMU/gJSyAeNAoGAS077
+azftURmMvRGk1gYPote7ElBbF3WdnN2GtUPSIdgWBK714AEMTnEdlz74p5b+TJO
BAXrjkJeEaZuOjpGwIhlhTv56S8Khi5NzP0KwvZKuk4UfoVuOTg/SWTtahqWPSKB
rTC6KlabIl2ckB4n/8+16+GpjzVVJ4xVHRt/jPECgYASU3i0yxdWNtEhEyCD+y/Q
IRP91iMzpAsbWKhvCma/oerGRNmMW3p1E7Hf8d7kcr14T3m2mAH6N/xazkWwfHr/
hGA7fcNL0h9skR9aMctjvMQfUz+gwC4SaZEZaqNvk5cxz9vdcFSvo952TjE7qcRL
oVxqgj0HmfI0FkuE0hzdAA==
-----END PRIVATE KEY-----
```

### `theorganizer.crt`
```bash
-----BEGIN CERTIFICATE-----
MIIE8DCCA9igAwIBAgIRAP5ke1tBTEJRaove2r+RikIwDQYJKoZIhvcNAQELBQAw
gZUxCzAJBgNVBAYTAlVTMRMwEQYDVQQIDApDYWxpZm9ybmlhMRYwFAYDVQQHDA1T
YW4gRnJhbmNpc2NvMRIwEAYDVQQKDAlDQU1BREEgU0ExEjAQBgNVBAsMCUNBTUFE
QSBTQTETMBEGA1UEAwwKY2FtYWRhLm5ldDEcMBoGCSqGSIb3DQEJARYNbWVAY2Ft
YWRhLm5ldDAeFw0yNTEyMTQxNzU5MTVaFw0yODAzMTgxNzU5MTVaMIGIMQswCQYD
VQQGEwJCUjEKMAgGA1UECAwBXTETMBEGA1UEBwwKR3VhcmFwdWF2YTEPMA0GA1UE
CgwGZy1wcm9kMQ8wDQYDVQQLDAZnLXByb2QxGDAWBgNVBAMMDyouZy1wcm9kLmNv
bS5icjEcMBoGCSqGSIb3DQEJARYNbWVAZy1wcm9kLmNvbTCCASIwDQYJKoZIhvcN
AQEBBQADggEPADCCAQoCggEBALaSUhH1nw4n56wHOuEnqLSLoHwhdQ1Nz4iQQrD2
9fSGcDFAmNNWVtToyhDlGiRTKz/6UlaYsPNlqjLopEB2iVLlrG1E+5qLkwtW9BHX
lpFVX+M+X517yZXJQAFNgJCLHWPrWycafQakdX7JSVhyK107dIJ/NUfTsiI+XH86
SlFSrh24pItNQIlL9exA7239tu7KgjW+aaw+RUCA6V2Q7K0IiAie4Ajd3r5UWSAV
b/PcNXLfJ4QInZ54kHXFz8oBmaN9y0srRTwcsI9glbdF1Fe0rFW5YE/8uBOzhKag
dvnajDv23E7Z8nfmErQqns9KuEvdNPkMyuPpese9C8WIL/UCAwEAAaOCAUQwggFA
MAkGA1UdEwQCMAAwHQYDVR0OBBYEFFm7SYtIkvebASHCDsCDf3zx+e1UMIHVBgNV
HSMEgc0wgcqAFKS6qhk+tBRgrmGAWdSL64JBGocBoYGbpIGYMIGVMQswCQYDVQQG
EwJVUzETMBEGA1UECAwKQ2FsaWZvcm5pYTEWMBQGA1UEBwwNU2FuIEZyYW5jaXNj
bzESMBAGA1UECgwJQ0FNQURBIFNBMRIwEAYDVQQLDAlDQU1BREEgU0ExEzARBgNV
BAMMCmNhbWFkYS5uZXQxHDAaBgkqhkiG9w0BCQEWDW1lQGNhbWFkYS5uZXSCFAgB
+lDEsE6uYBUR3esR13yIgfv5MBMGA1UdJQQMMAoGCCsGAQUFBwMBMAsGA1UdDwQE
AwIFoDAaBgNVHREEEzARgg8qLmctcHJvZC5jb20uYnIwDQYJKoZIhvcNAQELBQAD
ggEBAD00lpgCn4ndg1OphgE3gy9wa9FA9hLCECKTILAdteBXPxhy2OubsoX5vNFu
N6i6QuS/hU4oCn5rzIPTBZhKxHlTRv7M2HBABPPbfy8dDKOMKnyh/+iUF19G/Bwr
cYVeL5DZ7MDpNpXrVLjxPSdksK9N8n/NnwwI6rL4H8hyFHCwM4o1xI4QDN1nYO1p
mgoWN+V7HWQqykJVImWb1LbRWDMnLn8LpRfkT1jukV6h1WJ2jy68gEnSlIW0Gqru
t0vyFAVZFhSYrIghcXwWAo3iIqDCUwdcEXmPOeqsWRyZqI1PPjyyuT/xm8aeWq3v
ulGtjZnF9wmX5wtUy0T1z9kBBBk=
-----END CERTIFICATE-----
```
