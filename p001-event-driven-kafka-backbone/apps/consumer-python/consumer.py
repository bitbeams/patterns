# consumer.py - Kafka consumer with retry and DLQ logic for orders topics

import argparse  # For command-line argument parsing
import json      # For decoding Kafka message payloads
import sys       # For error output
import time      # For sleep and timing
from typing import Dict, List, Tuple, Optional
from confluent_kafka import Consumer, Producer, KafkaError, Message

# Kafka broker address
BOOTSTRAP = "localhost:9094"

# Convert Kafka message headers from list of tuples to a dictionary
def to_headers_dict(headers: Optional[List[Tuple[str, Optional[bytes]]]]) -> Dict[str, str]:
    """
    Convert Kafka message headers from list of tuples to a dictionary.
    """
    d: Dict[str, str] = {}
    if headers:
        for k, v in headers:
            d[k] = v.decode("utf-8") if isinstance(v, (bytes, bytearray)) and v is not None else (v or "")
    return d

# Convert a dictionary of headers to a list of tuples for Kafka producer
def to_headers_list(d: Dict[str, str]) -> List[Tuple[str, bytes]]:
    """
    Convert a dictionary of headers to a list of tuples for Kafka producer.
    """
    return [(k, str(v).encode("utf-8")) for k, v in d.items()]

# Create and configure a Kafka consumer
def make_consumer(group_id: str, auto_offset_reset="earliest") -> Consumer:
    """
    Create and configure a Kafka consumer.
    """
    return Consumer({
        "bootstrap.servers": BOOTSTRAP,
        "group.id": group_id,
        "enable.auto.commit": False,
        "auto.offset.reset": auto_offset_reset
    })

# Create and configure a Kafka producer
def make_producer() -> Producer:
    """
    Create and configure a Kafka producer.
    """
    return Producer({
        "bootstrap.servers": BOOTSTRAP,
        "enable.idempotence": True,
        "acks": "all"
    })

# Business logic for processing a single event
# Raises an exception if the amount is below the threshold
def process_event(event: Dict, fail_if_amount_lt: Optional[float]) -> None:
    """
    Business logic for processing a single event.
    Raises an exception if the amount is below the threshold.
    """
    print("Processing event:", event)
    print("Fail Amount:", fail_if_amount_lt)
    print("Amount:", event.get("amount", 0))
    if fail_if_amount_lt is not None:
        amount = float(event.get("amount", 0))
        print(f"[DEBUG] Processing event: {event}, extracted amount: {amount}, threshold: {fail_if_amount_lt}", flush=True)
        if amount < fail_if_amount_lt:
            print(f"[DEBUG] Amount {amount} is below threshold {fail_if_amount_lt}, raising exception.", flush=True)
            raise ValueError(f"Amount {amount} is below threshold {fail_if_amount_lt}")
        else:
            print(f"[DEBUG] Amount {amount} is above or equal to threshold {fail_if_amount_lt}, processing normally.", flush=True)
        # Put real processing here
    return

# Forward a message to another Kafka topic, preserving headers
def forward(producer: Producer, dest_topic: str, value: bytes, headers: Dict[str, str]) -> None:
    """
    Forward a message to another Kafka topic, preserving headers.
    """
    producer.produce(dest_topic, value=value, headers=to_headers_list(headers))
    producer.flush()

# Handle a single Kafka message: process, retry, or send to DLQ as needed
# Returns 'committed' or 'skipped'
def handle_message(msg: Message, mode: str, producer: Producer, max_retries: int, retry_topic: str, dlq_topic: str, fail_if_amount_lt: Optional[float]) -> str:
    """
    Handle a single Kafka message: process, retry, or send to DLQ as needed.
    Returns 'committed' or 'skipped'.
    """
    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            return "skipped"
        else:
            raise msg.error()

    value_bytes = msg.value()
    headers_map = to_headers_dict(msg.headers())
    payload = json.loads(value_bytes.decode("utf-8"))

    # Ensure standard headers exist
    headers_map.setdefault("trace_id", headers_map.get("trace_id", ""))
    headers_map.setdefault("schema_version", headers_map.get("schema_version", "1.0"))
    headers_map.setdefault("idempotency_key", headers_map.get("idempotency_key", ""))

    retry_count = int(headers_map.get("retry_count", "0"))

    try:
        process_event(payload, fail_if_amount_lt)
        return "committed"

    except Exception as ex:
        error_reason = str(ex)
        if mode == "main":
            # First level failure. Send to retry with retry_count = 1
            headers_map["retry_count"] = str(retry_count + 1)
            headers_map["last_error"] = error_reason
            forward(producer, retry_topic, value_bytes, headers_map)
            return "committed"

        elif mode == "retry":
            next_retry = retry_count + 1
            headers_map["retry_count"] = str(next_retry)
            headers_map["last_error"] = error_reason
            if next_retry >= max_retries:
                # Give up to DLQ
                forward(producer, dlq_topic, value_bytes, headers_map)
                return "committed"
            else:
                # Requeue to retry for another attempt
                forward(producer, retry_topic, value_bytes, headers_map)
                return "committed"

        else:
            raise RuntimeError(f"Unknown mode {mode}")

# Main entry point: parses arguments, sets up consumer/producer, and runs the message loop
def main():
    """
    Main entry point: parses arguments, sets up consumer/producer, and runs the message loop.
    """
    parser = argparse.ArgumentParser(description="Kafka consumer with retry and DLQ")
    parser.add_argument("--mode", choices=["main", "retry"], default="main",
                        help="main consumes from orders.v1, retry consumes from orders.retry")
    parser.add_argument("--group", default=None, help="consumer group id. Defaults per mode")
    parser.add_argument("--source-topic", default=None, help="override source topic")
    parser.add_argument("--retry-topic", default="orders.retry")
    parser.add_argument("--dlq-topic", default="orders.dlq")
    parser.add_argument("--max-retries", type=int, default=3, help="max attempts before DLQ in retry mode")
    parser.add_argument("--fail-if-amount-lt", type=float, default=1.0,
                        help="simulate failure if amount is less than this value")
    parser.add_argument("--poll-timeout", type=float, default=1.0)

    args = parser.parse_args()

    # Determine source topic and group ID based on mode
    source_topic = args.source_topic or ("orders.v1" if args.mode == "main" else "orders.retry")
    group_id = args.group or (f"{args.mode}-consumer-group")

    consumer = make_consumer(group_id)
    producer = make_producer()

    consumer.subscribe([source_topic])
    time.sleep(1)
    print(f"Consuming from {source_topic} in {args.mode} mode. Group {group_id}. Ctrl+C to exit.")

    try:
        while True:
            msg = consumer.poll(args.poll_timeout)
            # print(consumer.assignment())

            if msg is None:
                print("No message received")
                continue
            try:
                print("Processing message...")
                result = handle_message(
                    msg=msg,
                    mode=args.mode,
                    producer=producer,
                    max_retries=args.max_retries,
                    retry_topic=args.retry_topic,
                    dlq_topic=args.dlq_topic,
                    fail_if_amount_lt=args.fail_if_amount_lt
                )
                if result == "committed":
                    consumer.commit(msg)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                # Unexpected processing error. Do not commit. Log and continue.
                print(f"Unexpected error: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        consumer.close()

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
