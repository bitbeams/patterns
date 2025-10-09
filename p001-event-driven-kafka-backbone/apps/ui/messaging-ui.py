"""
messaging-ui.py
Flask web UI for producing and consuming Kafka messages for orders.v1, orders.retry, and orders.dlq topics.
"""

import threading
import time
from flask import Flask, render_template, request, jsonify
from confluent_kafka import Producer, Consumer, KafkaException

app = Flask(__name__)

# In-memory stores for each topic
consumed_orders = []  # Messages from orders.v1
consumed_retry = []   # Messages from orders.retry
consumed_dlq = []     # Messages from orders.dlq

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9094'
KAFKA_GROUP = 'ui-consumer-group'

# Map topics to their in-memory stores
TOPICS = {
    'orders.v1': consumed_orders,
    'orders.retry': consumed_retry,
    'orders.dlq': consumed_dlq
}

def start_consumer(topic, store):
    """
    Background thread function to consume messages from a Kafka topic and store them in memory.
    """
    consumer_conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': f'{KAFKA_GROUP}-{topic}',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error on {topic}: {msg.error()}")
            continue
        # Store all messages (consider limiting in production)
        store.append({
            'key': msg.key().decode() if msg.key() else '',
            'value': msg.value().decode(),
            'partition': msg.partition(),
            'offset': msg.offset(),
            'timestamp': msg.timestamp()[1]
        })

# Start a consumer thread for each topic
for topic, store in TOPICS.items():
    threading.Thread(target=start_consumer, args=(topic, store), daemon=True).start()

# Kafka producer setup
producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

@app.route('/', methods=['GET'])
def index():
    """
    Render the main UI page.
    """
    return render_template('index.html')

@app.route('/produce', methods=['POST'])
def produce():
    """
    Produce a message to the orders.v1 topic.
    """
    value = request.form['value']
    key = request.form.get('key', None)
    try:
        producer.produce('orders.v1', value=value, key=key)
        producer.flush()
        return 'Message produced!', 200
    except Exception as e:
        return f'Error: {e}', 500

@app.route('/messages', methods=['GET'])
def get_messages():
    """
    Return all consumed messages from each topic as JSON.
    """
    return jsonify({
        'orders': consumed_orders,
        'retry': consumed_retry,
        'dlq': consumed_dlq
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)