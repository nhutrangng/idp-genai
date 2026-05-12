terraform {
  
  backend "s3" {
    bucket       = "genai-idp-tf-state-bucket"
    key          = "${{ values.name }}/terraform.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
        source = "hashicorp/aws"
        version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-1"
}

resource "aws_instance" "app_server" {
    ami = "ami-02dd44faa40720bb8"
    instance_type = "t3.micro"

    tags = {
    Name        = "${{ values.name }}-server"
    ManagedBy   = "GenAI-IDP-Terraform"
    }
  
}