# producer.py - Kafka JSON Producer for orders topics

import json      # For encoding event payloads
import uuid      # For generating trace and idempotency keys
import argparse  # For parsing command-line arguments
from confluent_kafka import Producer

# Callback to report message delivery result
def delivery_report(err, msg):
    """
    Reports message delivery result.
    """
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    else:
        print(f"✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Create an idempotent Kafka producer
def create_producer(bootstrap_servers):
    """
    Create an idempotent Kafka producer with recommended settings.
    """
    return Producer({
        'bootstrap.servers': bootstrap_servers,
        'enable.idempotence': True,
        'acks': 'all',
        'retries': 5,
        'linger.ms': 5,
        'batch.num.messages': 100,
    })

# Generate message headers for traceability and idempotence
def build_headers():
    """
    Generate message headers for traceability and idempotence.
    """
    trace_id = str(uuid.uuid4())
    idempotency_key = str(uuid.uuid4())
    schema_version = "1.0"
    return [
        ('trace_id', trace_id.encode('utf-8')),
        ('idempotency_key', idempotency_key.encode('utf-8')),
        ('schema_version', schema_version.encode('utf-8'))
    ]

# Main entry point: parses arguments, builds event, and produces to Kafka
def main():
    parser = argparse.ArgumentParser(description="Kafka JSON Producer")
    parser.add_argument('--bootstrap-servers', default='localhost:9094', help='Kafka bootstrap servers')
    parser.add_argument('--topic', default='orders.v1', help='Kafka topic name')
    parser.add_argument('--order-id', required=True, help='Order ID')
    parser.add_argument('--amount', type=float, required=True, help='Order amount')
    args = parser.parse_args()

    # Create Kafka producer
    producer = create_producer(args.bootstrap_servers)

    # Build event payload
    event = {
        "orderId": args.order_id,
        "amount": args.amount
    }

    # Build headers for traceability
    headers = build_headers()

    # Produce message to Kafka
    producer.produce(
        topic=args.topic,
        value=json.dumps(event).encode('utf-8'),
        headers=headers,
        callback=delivery_report
    )

    # Wait for all messages to be delivered
    producer.flush()

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
