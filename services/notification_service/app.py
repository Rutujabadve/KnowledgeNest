"""
Notification Service - Consumes events from RabbitMQ
Demonstrates event-driven architecture by processing events and logging notifications
"""
import pika
import json
import os
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationService:
    """Service that consumes events from RabbitMQ and processes them"""
    
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', '5672'))
        self.username = os.getenv('RABBITMQ_USER', 'admin')
        self.password = os.getenv('RABBITMQ_PASS', 'password')
        self.exchange = 'knowledge_nest_events'
        self.connection = None
        self.channel = None
        
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='topic',
                durable=True
            )
            
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def setup_queues(self):
        """Setup queues and bindings for different event types"""
        # Queue for all events
        queue_name = 'notification_queue'
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind to different routing keys
        routing_keys = [
            'user.registered',
            'course.created',
            'course.enrolled',
            'review.created'
        ]
        
        for routing_key in routing_keys:
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=queue_name,
                routing_key=routing_key
            )
            logger.info(f"Bound queue '{queue_name}' to routing key '{routing_key}'")
        
        return queue_name
    
    def process_event(self, ch, method, properties, body):
        """Process incoming events"""
        try:
            event_data = json.loads(body)
            event_type = event_data.get('event_type', 'unknown')
            data = event_data.get('data', {})
            timestamp = event_data.get('timestamp', datetime.utcnow().isoformat())
            
            logger.info(f"Received event: {event_type} at {timestamp}")
            
            # Process different event types
            if event_type == 'user.registered':
                self.handle_user_registered(data)
            elif event_type == 'course.created':
                self.handle_course_created(data)
            elif event_type == 'course.enrolled':
                self.handle_course_enrolled(data)
            elif event_type == 'review.created':
                self.handle_review_created(data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse event JSON: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def handle_user_registered(self, data):
        """Handle user registration event"""
        user_id = data.get('user_id')
        email = data.get('email')
        name = data.get('name', 'User')
        
        logger.info(f"📧 Sending welcome email to {email} (User ID: {user_id})")
        logger.info(f"   Welcome {name}! Thank you for joining KnowledgeNest!")
        # In production, this would send an actual email
    
    def handle_course_created(self, data):
        """Handle course creation event"""
        course_id = data.get('course_id')
        title = data.get('title')
        
        logger.info(f"📚 New course created: '{title}' (Course ID: {course_id})")
        logger.info(f"   Course added to catalog and available for enrollment")
        # In production, this could trigger notifications to interested users
    
    def handle_course_enrolled(self, data):
        """Handle course enrollment event"""
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        course_title = data.get('course_title', 'Course')
        
        logger.info(f"🎓 User {user_id} enrolled in course: '{course_title}' (Course ID: {course_id})")
        logger.info(f"   Sending enrollment confirmation and course materials")
        # In production, this would send enrollment confirmation email
    
    def handle_review_created(self, data):
        """Handle review creation event"""
        review_id = data.get('review_id')
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        rating = data.get('rating')
        
        logger.info(f"⭐ Review created: User {user_id} rated course {course_id} with {rating} stars (Review ID: {review_id})")
        logger.info(f"   Review processed and course rating updated")
        # In production, this could update course average rating in real-time
    
    def start_consuming(self):
        """Start consuming events"""
        if not self.connect():
            logger.error("Failed to connect to RabbitMQ. Exiting.")
            return
        
        queue_name = self.setup_queues()
        
        # Set QoS to process one message at a time
        self.channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=self.process_event
        )
        
        logger.info("Notification Service started. Waiting for events...")
        logger.info("Press CTRL+C to exit")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping notification service...")
            self.channel.stop_consuming()
            self.connection.close()
            logger.info("Notification service stopped")

if __name__ == '__main__':
    service = NotificationService()
    service.start_consuming()

