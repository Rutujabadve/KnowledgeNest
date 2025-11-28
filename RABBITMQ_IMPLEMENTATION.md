# RabbitMQ Implementation Guide

## Overview

KnowledgeNest uses **RabbitMQ** as a message broker to implement an **event-driven architecture** for asynchronous communication between microservices. This enables loose coupling, scalability, and real-time event processing.

## Architecture

### Event-Driven Communication Flow

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│ Auth Service│─────▶│   RabbitMQ   │─────▶│Notification     │
│             │      │   Exchange   │      │Service          │
└─────────────┘      │              │      └─────────────────┘
                     │              │
┌─────────────┐      │              │      ┌─────────────────┐
│Course Service│────▶│              │─────▶│Analytics Service│
│             │      │              │      │(Future)         │
└─────────────┘      └──────────────┘      └─────────────────┘
                     │
┌─────────────┐      │
│Review Service│─────▶│
│             │      │
└─────────────┘      │
```

## Implementation Details

### 1. Exchange and Routing Keys

**Exchange Name:** `knowledge_nest_events`  
**Exchange Type:** `topic` (allows flexible routing based on patterns)

**Routing Keys:**
- `user.registered` - When a new user registers
- `course.created` - When a new course is created
- `course.enrolled` - When a user enrolls in a course
- `review.created` - When a user submits a review

### 2. RabbitMQ Client Utility

Each service that publishes events has a `rabbitmq_client.py` module with:

- **Connection Management**: Handles connection, reconnection, and error handling
- **Exchange Declaration**: Automatically declares exchanges if they don't exist
- **Event Publishing**: Publishes events with persistent delivery mode
- **Error Handling**: Graceful degradation if RabbitMQ is unavailable

**Key Features:**
- Automatic reconnection on connection loss
- Persistent messages (survive broker restarts)
- JSON message format
- Configurable via environment variables

### 3. Event Publishers

#### Auth Service (`services/auth_service/app.py`)
- **Event:** `user.registered`
- **Triggered:** After successful user registration
- **Payload:**
  ```json
  {
    "event_type": "user.registered",
    "timestamp": "2024-01-15T10:30:00",
    "data": {
      "user_id": 123,
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
  ```

#### Course Service (`services/course_service/app.py`)
- **Events:** 
  - `course.created` - When a new course is created
  - `course.enrolled` - When a user enrolls in a course
- **Payloads:**
  ```json
  {
    "event_type": "course.enrolled",
    "timestamp": "2024-01-15T10:35:00",
    "data": {
      "enrollment_id": 456,
      "user_id": 123,
      "course_id": 789,
      "course_title": "Python Fundamentals"
    }
  }
  ```

#### Review Service (`services/review_service/app.py`)
- **Event:** `review.created`
- **Triggered:** After a review is successfully created
- **Payload:**
  ```json
  {
    "event_type": "review.created",
    "timestamp": "2024-01-15T10:40:00",
    "data": {
      "review_id": 101,
      "user_id": 123,
      "course_id": 789,
      "rating": 5,
      "has_comment": true
    }
  }
  ```

### 4. Event Consumer: Notification Service

The **Notification Service** (`services/notification_service/app.py`) demonstrates event consumption:

**Features:**
- Consumes all events from the `knowledge_nest_events` exchange
- Processes events asynchronously
- Handles different event types with specific handlers
- Implements message acknowledgment for reliability
- Logs notifications (can be extended to send emails, SMS, etc.)

**Event Handlers:**
1. `handle_user_registered()` - Sends welcome email
2. `handle_course_created()` - Notifies about new courses
3. `handle_course_enrolled()` - Sends enrollment confirmation
4. `handle_review_created()` - Processes review and updates ratings

## Configuration

### Environment Variables

All services use these environment variables for RabbitMQ connection:

```bash
RABBITMQ_HOST=rabbitmq      # Service name in Docker, 'localhost' for local dev
RABBITMQ_PORT=5672          # AMQP port
RABBITMQ_USER=admin         # RabbitMQ username
RABBITMQ_PASS=password      # RabbitMQ password
```

### Docker Compose Configuration

RabbitMQ is configured in `ci_cd/docker-compose.yml`:

```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports:
    - "5672:5672"      # AMQP port
    - "15672:15672"    # Management UI
  environment:
    - RABBITMQ_DEFAULT_USER=admin
    - RABBITMQ_DEFAULT_PASS=password
```

## Benefits of This Implementation

### 1. **Loose Coupling**
- Services don't need to know about each other
- New consumers can be added without modifying publishers

### 2. **Scalability**
- Multiple consumers can process events in parallel
- Services can scale independently

### 3. **Reliability**
- Messages are persistent (survive broker restarts)
- Message acknowledgment ensures processing
- Failed messages can be requeued

### 4. **Asynchronous Processing**
- Non-blocking event publishing
- Long-running tasks don't block API responses

### 5. **Event Sourcing Ready**
- All events are logged and can be replayed
- Enables audit trails and analytics

## Usage Examples

### Publishing an Event (from any service)

```python
from rabbitmq_client import rabbitmq_client

event_data = {
    "event_type": "custom.event",
    "timestamp": datetime.utcnow().isoformat(),
    "data": {
        "key": "value"
    }
}

rabbitmq_client.publish_event(
    exchange="knowledge_nest_events",
    routing_key="custom.event",
    event_data=event_data
)
```

### Consuming Events (Notification Service pattern)

```python
def process_event(ch, method, properties, body):
    event_data = json.loads(body)
    # Process event
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(
    queue='my_queue',
    on_message_callback=process_event
)
```

## Monitoring

### RabbitMQ Management UI

Access the management interface at: `http://localhost:15672`

**Credentials:**
- Username: `admin`
- Password: `password`

**Features:**
- View queues, exchanges, and bindings
- Monitor message rates
- View message contents
- Manage connections and channels

### Logs

All services log RabbitMQ operations:
- Connection status
- Published events
- Consumed events
- Errors and warnings

## Future Enhancements

1. **Dead Letter Queue (DLQ)**: Handle failed messages
2. **Message TTL**: Set expiration for time-sensitive events
3. **Priority Queues**: Prioritize important events
4. **Clustering**: High availability setup
5. **Analytics Service**: Process events for business intelligence
6. **Email Service**: Send actual emails based on events
7. **Real-time Dashboard**: WebSocket-based event monitoring

## Troubleshooting

### Connection Issues

If services can't connect to RabbitMQ:
1. Check RabbitMQ is running: `docker ps | grep rabbitmq`
2. Verify environment variables are set correctly
3. Check network connectivity in Docker Compose
4. Review service logs for connection errors

### Message Not Received

1. Check exchange and queue bindings in Management UI
2. Verify routing keys match
3. Check consumer is running and connected
4. Review consumer logs for errors

### Performance Issues

1. Monitor queue lengths in Management UI
2. Increase consumer instances for parallel processing
3. Adjust prefetch count for better throughput
4. Consider message batching for high-volume events

## Testing

### Manual Testing

1. Start all services: `docker-compose up`
2. Register a user via API
3. Check Notification Service logs for `user.registered` event
4. Enroll in a course
5. Check logs for `course.enrolled` event
6. View messages in RabbitMQ Management UI

### Integration Testing

Test event flow:
```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# Check notification service logs should show welcome message
```

## Code Structure

```
services/
├── auth_service/
│   ├── rabbitmq_client.py      # RabbitMQ publisher utility
│   └── app.py                   # Publishes user.registered events
├── course_service/
│   ├── rabbitmq_client.py       # RabbitMQ publisher utility
│   └── app.py                   # Publishes course.* events
├── review_service/
│   ├── rabbitmq_client.py       # RabbitMQ publisher utility
│   └── app.py                   # Publishes review.created events
└── notification_service/
    └── app.py                   # Consumes all events
```

## Summary

This RabbitMQ implementation provides a robust, scalable foundation for event-driven communication in KnowledgeNest. It enables:

- ✅ Asynchronous event processing
- ✅ Service decoupling
- ✅ Real-time notifications
- ✅ Extensible architecture
- ✅ Production-ready reliability

The implementation follows best practices for microservices communication and can be easily extended for additional event types and consumers.

