# Kafka Main–Retry–DLQ Pattern: Reliable Event Processing

## Pattern Overview
This pattern implements robust, fault-tolerant event processing in Apache Kafka using three topics:
- **orders.v1**: Main topic for new order events.
- **orders.retry**: Holds events that failed initial processing and require another attempt.
- **orders.dlq**: Dead Letter Queue for events that could not be processed after multiple retries.

## How It Works
1. **Main Flow**: Orders are produced to `orders.v1`. A consumer processes each event. If successful, processing ends here.
2. **Retry Logic**: If processing fails (e.g., due to a transient error), the event is sent to `orders.retry`. A retry consumer attempts to process these events, with a configurable number of retries.
3. **Dead Letter Queue**: If an event fails all retry attempts, it is moved to `orders.dlq` for manual inspection and intervention.

## Benefits
- **Resilience**: Automatic retries for transient failures.
- **Transparency**: Clear event flow and error handling.
- **Safety**: No message is lost; all failures are captured.
- **Simplicity**: Easy to understand, maintain, and extend.

## Example Workflow
1. Order event is produced to `orders.v1`.
2. Main consumer fails to process (e.g., payment timeout) → event moves to `orders.retry`.
3. Retry consumer processes the event. If it succeeds, the workflow ends. If it fails after max retries, the event is sent to `orders.dlq`.
4. Operations or support teams review DLQ events for resolution.

## Conclusion
The main–retry–DLQ pattern is a proven approach for building reliable, observable, and maintainable event-driven systems with Kafka. It ensures that all events are processed or accounted for, supporting both operational excellence and customer satisfaction.
