FEATURE_UI_PATH=ansible/playbooks/ui/deploy-ui.yml
KAFKA_DOCKER_PLAYBOOK_PATH=ansible/playbooks/kafka/install-kafka-docker.yml
FEATURE_PATH=ansible/playbooks/deploy-feature.yml
INVENTORY_PATH=ansible/inventories/aws/aws_ec2.yml
PYTHONAPPS_PATH=ansible/playbooks/pythonapps/deploy-apps.yml

build-server:
	cd ~/projects/patterns/p001-event-driven-kafka-backbone/infra/aws/terraform && \
	terraform init && \
	terraform apply -auto-approve

destroy-server:
	cd ~/projects/patterns/p001-event-driven-kafka-backbone/infra/aws/terraform && \
	terraform init && \
	terraform destroy -auto-approve

# Deploy Python apps to server
deploy-apps:
	ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook -i $(INVENTORY_PATH) $(PYTHONAPPS_PATH) 

install-kafka-docker:
	ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook -i $(INVENTORY_PATH) $(KAFKA_DOCKER_PLAYBOOK_PATH)

deploy-ui:
	ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook -i $(INVENTORY_PATH) $(FEATURE_UI_PATH)

deploy-feature:
	ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook -i $(INVENTORY_PATH) $(FEATURE_PATH)
