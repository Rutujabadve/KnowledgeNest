"""
Notification Service - Consumes events from RabbitMQ
Handles asynchronous event processing with improved error handling
"""
import json
import logging
import os
import time
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the service directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the RabbitMQ client with proper error handling
try:
    from .rabbitmq_client import RabbitMQClient
except ImportError:
    # Fallback for direct script execution
    from rabbitmq_client import RabbitMQClient

class NotificationService:
    """Service that consumes events from RabbitMQ and processes them"""
    
    def __init__(self):
        """Initialize the notification service with configuration"""
        self.exchange = os.getenv('RABBITMQ_EXCHANGE', 'knowledge_nest_events')
        self.queue_name = os.getenv('RABBITMQ_QUEUE', 'notification_queue')
        self.routing_keys = [
            'user.*',
            'course.*',
            'review.*'
        ]
        self.max_retries = int(os.getenv('RABBITMQ_MAX_RETRIES', '5'))
        self.retry_delay = int(os.getenv('RABBITMQ_RETRY_DELAY', '5'))
        self.rabbitmq = None
        self.should_reconnect = True
        
    def connect(self):
        """Establish connection to RabbitMQ with retry logic"""
        retry_count = 0
        last_exception = None
        
        while retry_count < self.max_retries and self.should_reconnect:
            try:
                self.rabbitmq = RabbitMQClient(
                    host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
                    port=int(os.getenv('RABBITMQ_PORT', '5672')),
                    username=os.getenv('RABBITMQ_USER', 'admin'),
                    password=os.getenv('RABBITMQ_PASS', 'password'),
                    max_retries=3,
                    initial_backoff=2.0
                )
                
                if self.rabbitmq.ensure_connection():
                    logger.info("✅ Successfully connected to RabbitMQ")
                    return True
                    
            except Exception as e:
                last_exception = e
                retry_count += 1
                wait_time = self.retry_delay * retry_count
                logger.warning(
                    f"⚠️ Connection attempt {retry_count}/{self.max_retries} failed. "
                    f"Retrying in {wait_time} seconds... Error: {str(e)}"
                )
                time.sleep(wait_time)
        
        logger.error(f"❌ Failed to connect to RabbitMQ after {self.max_retries} attempts")
        if last_exception:
            logger.error(f"Last error: {str(last_exception)}")
        return False
    
    def setup_queues(self):
        """Setup queues and bindings for different event types"""
        try:
            if not self.rabbitmq:
                raise RuntimeError("RabbitMQ client not initialized")
                
            # Declare exchange
            self.rabbitmq.declare_exchange(self.exchange, 'topic')
            
            # Declare the queue first
            self.rabbitmq.declare_queue(
                queue_name=self.queue_name,
                durable=True
            )
            
            # Bind the queue to the exchange with each routing key
            for routing_key in self.routing_keys:
                self.rabbitmq.bind_queue(
                    queue_name=self.queue_name,
                    exchange=self.exchange,
                    routing_key=routing_key
                )
                logger.info(f"✅ Queue '{self.queue_name}' bound to exchange '{self.exchange}' with routing key '{routing_key}'")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup queues: {str(e)}")
            return False
    
    def process_event(self, channel, method, properties, body):
        """Process incoming events with proper error handling"""
        try:
            event_data = json.loads(body) if isinstance(body, (bytes, bytearray)) else body
            if not isinstance(event_data, dict):
                event_data = json.loads(event_data)
                
            event_type = event_data.get('event_type', 'unknown')
            data = event_data.get('data', {})
            timestamp = event_data.get('timestamp', datetime.utcnow().isoformat())
            
            logger.info(f"📩 Received event: {event_type} at {timestamp}")
            logger.debug(f"Event data: {json.dumps(event_data, indent=2)}")
            
            # Process different event types
            try:
                if event_type == 'user.registered':
                    self.handle_user_registered(data)
                elif event_type == 'course.created':
                    self.handle_course_created(data)
                elif event_type == 'course.enrolled':
                    self.handle_course_enrolled(data)
                elif event_type == 'review.created':
                    self.handle_review_created(data)
                else:
                    logger.warning(f"⚠️ Unknown event type: {event_type}")
                
                # Acknowledge the message
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"✅ Successfully processed {event_type} event")
                
            except Exception as e:
                logger.error(f"❌ Error processing {event_type} event: {str(e)}")
                # Reject the message but don't requeue (to avoid poison messages)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse event JSON: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"❌ Unexpected error processing message: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Start consuming messages with reconnection logic"""
        while self.should_reconnect:
            try:
                if not self.connect() or not self.setup_queues():
                    raise RuntimeError("Failed to initialize RabbitMQ connection and queues")
                
                logger.info("🚀 Starting to consume messages...")
                
                # Set up the consumer with the queue and callback
                self.rabbitmq.setup_consumer(
                    exchange=self.exchange,
                    queue_name=self.queue_name,
                    routing_keys=self.routing_keys,
                    callback=self.process_event
                )
                
                # Start consuming messages
                self.rabbitmq.start_consuming()
                
            except KeyboardInterrupt:
                logger.info("👋 Shutdown signal received. Stopping...")
                self.should_reconnect = False
                break
            except Exception as e:
                logger.error(f"❌ Error in message consumer: {str(e)}")
                if self.should_reconnect:
                    logger.info(f"♻️ Attempting to reconnect in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    break
    
    def stop(self):
        """Gracefully stop the service"""
        self.should_reconnect = False
        if self.rabbitmq:
            self.rabbitmq.close()
    
    # Event handlers
    def handle_user_registered(self, data):
        """Handle user registration event"""
        user_id = data.get('user_id')
        email = data.get('email')
        name = data.get('name', 'User')
        logger.info(f"👋 Welcome {name} (ID: {user_id}, Email: {email})! Your account has been created successfully.")
    
    def handle_course_created(self, data):
        """Handle course creation event"""
        course_id = data.get('course_id')
        title = data.get('title', 'Untitled Course')
        logger.info(f"📚 New course created: {title} (ID: {course_id})")
    
    def handle_course_enrolled(self, data):
        """Handle course enrollment event"""
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        course_title = data.get('course_title', 'a course')
        logger.info(f"🎓 User {user_id} has enrolled in course: {course_title} (ID: {course_id})")
    
    def handle_review_created(self, data):
        """Handle review creation event"""
        review_id = data.get('review_id')
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        rating = data.get('rating')
        has_comment = data.get('has_comment', False)
        logger.info(
            f"⭐ New review (ID: {review_id}) - User {user_id} rated course {course_id} "
            f"with {rating} stars" + (" and left a comment" if has_comment else "")
        )

def main():
    """Main entry point for the notification service"""
    service = NotificationService()
    
    try:
        service.start_consuming()
    except KeyboardInterrupt:
        logger.info("👋 Shutdown signal received. Stopping gracefully...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        return 1
    finally:
        service.stop()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())