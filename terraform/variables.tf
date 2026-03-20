variable "vpc_cidr" {
  default = "10.0.0.0/16"
}
variable "public_subnet_1a_cidr" {
  default = "10.0.1.0/24"
}
variable "public_subnet_1c_cidr" {
  default = "10.0.2.0/24"
}
variable "private_subnet_1a_cidr" {
  default = "10.0.10.0/24"
}
variable "private_subnet_1c_cidr" {
  default = "10.0.11.0/24"
}
variable "s3_bucket_name" {
  description = "為替レートデータを格納する S3 バケット名"
  default     = "takaken94-exchange-rate"
  type        = string
}
variable "s3_prefix" {
  description = "S3 オブジェクトのプレフィックス"
  default     = "rate-data"
  type        = string
}