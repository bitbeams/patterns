output "kafka_vm_ip" {
  value = aws_instance.kafka_vm.public_ip
}