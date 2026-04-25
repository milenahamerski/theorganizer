terraform {
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
  auth_url    = "http://IP_OPENSTACK/identity"
  region      = "RegionOne"
}
