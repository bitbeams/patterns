# Kafka Makefile Commands

LOCAL_DIR=.
KAFKA_CONTAINER=kafka
KAFKA_BIN=/opt/bitnami/kafka/bin

## Install Python dependencies required for python scripts 
reqs:
	pip install -r ../../apps/requirements.txt

# Start/Stop the local stack
up: reqs
	docker compose up -d

down:
	docker compose down

# Create topics
topics:
	docker compose exec -T $(KAFKA_CONTAINER) bash -lc '$(KAFKA_BIN)/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic orders.v1 --partitions 3 --replication-factor 1 --config retention.ms=604800000 || true' && \
	docker compose exec -T $(KAFKA_CONTAINER) bash -lc '$(KAFKA_BIN)/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic orders.retry --partitions 3 --replication-factor 1 --config retention.ms=604800000 || true' && \
	docker compose exec -T $(KAFKA_CONTAINER) bash -lc '$(KAFKA_BIN)/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic orders.dlq --partitions 3 --replication-factor 1 --config retention.ms=604800000 || true'

# Produce test messages
produce:
	docker compose exec -T $(KAFKA_CONTAINER) bash -lc 'echo "{\"orderId\":\"o-1001\",\"amount\":42.50}" | $(KAFKA_BIN)/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic orders.v1'

# Produce test messages
produce-error:
	docker compose exec -T $(KAFKA_CONTAINER) bash -lc 'echo "{\"orderId\":\"o-1001\",\"amount\":-1}" | $(KAFKA_BIN)/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic orders.v1'

# Consume from orders.v1
consume:
    docker compose exec -T $(KAFKA_CONTAINER) bash -lc '$(KAFKA_BIN)/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic orders.v1 --from-beginning --group smoke-test --max-messages 10'

# Run main consumer (orders.v1 -> orders.retry on failure)
consume-main:
	python3 /opt/consumer-python/consumer.py --mode main --fail-if-amount-lt 0

# Run retry consumer (orders.retry -> orders.dlq after max retries)
consume-retry:
	python3 /opt/consumer-python/consumer.py --mode retry --max-retries 3 --fail-if-amount-lt 0
