variable "aws_region" {
  default = "eu-west-1"
}

variable "ami_id" {
  default = "ami-0a7e505f26c66ccb1" # Ubuntu Server 22.04 LTS (HVM), SSD Volume Type, eu-west-1 (August 2025)
}

variable "instance_type" {
  default = "t3.micro"
}

variable "key_name" {
  description = "Name of the existing key pair"
  type        = string
}

variable "public_key_path" {
  description = "Path to your public SSH key"
  type        = string
}