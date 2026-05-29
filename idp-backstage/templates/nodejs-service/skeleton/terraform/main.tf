terraform {
  backend "s3" {}

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

output "public_ip" {
  value = aws_instance.app_server.public_ip
}