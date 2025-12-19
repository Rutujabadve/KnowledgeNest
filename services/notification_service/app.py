"""
Notification Service - Consumes events from RabbitMQ
Demonstrates event-driven architecture by processing events and logging notifications
"""
import json
import logging
import os
import time
from datetime import datetime

# Import the RabbitMQ client
from rabbitmq_client import RabbitMQClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationService:
    """Service that consumes events from RabbitMQ and processes them"""
    
    def __init__(self):
        self.exchange = 'knowledge_nest_events'
        self.queue_name = 'notification_queue'
        self.routing_keys = ['user.*', 'course.*', 'review.*']
        self.rabbitmq = RabbitMQClient()
        
    def connect(self):
        """Establish connection to RabbitMQ with retry logic"""
        try:
            # The RabbitMQ client handles reconnection internally
            return self.rabbitmq.ensure_connection()
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def setup_queues(self):
        """Setup queues and bindings for different event types"""
        try:
            # Set up the consumer with the appropriate routing keys and callback
            self.rabbitmq.setup_consumer(
                exchange=self.exchange,
                queue_name=self.queue_name,
                routing_keys=self.routing_keys,
                callback=self.process_event
            )
            return self.queue_name
            
        except Exception as e:
            logger.error(f"Failed to setup queues: {str(e)}")
            raise
    
    def process_event(self, channel, method, properties, body):
        """Process incoming events"""
        try:
            event_data = body if isinstance(body, dict) else json.loads(body)
            event_type = event_data.get('event_type', 'unknown')
            data = event_data.get('data', {})
            timestamp = event_data.get('timestamp', datetime.utcnow().isoformat())
            
            logger.info(f"📩 Received event: {event_type} at {timestamp}")
            logger.debug(f"Event data: {event_data}")
            
            # Process different event types
            if event_type == 'user.registered':
                logger.info(f"👤 Processing user registration for user_id: {data.get('user_id')}")
                self.handle_user_registered(data)
            elif event_type == 'course.created':
                logger.info(f"📚 Processing new course: {data.get('title')} (ID: {data.get('course_id')})")
                self.handle_course_created(data)
            elif event_type == 'course.enrolled':
                logger.info(f"🎓 Processing enrollment: user {data.get('user_id')} in course {data.get('course_id')}")
                self.handle_course_enrolled(data)
            elif event_type == 'review.created':
                logger.info(f"⭐ Processing review: {data.get('review_id')} for course {data.get('course_id')}")
                self.handle_review_created(data)
            else:
                logger.warning(f"⚠️ Unknown event type: {event_type}")
            
            # Acknowledge message only after successful processing
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"✅ Successfully processed {event_type} event")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse event JSON: {str(e)}")
            # Reject the message without requeuing (to avoid poison messages)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"❌ Error processing event: {str(e)}")
            # Reject the message and requeue it for retry
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
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
        logger.info("Starting Notification Service...")
        
        if not self.connect():
            logger.error("Failed to connect to RabbitMQ. Exiting.")
            time.sleep(5)  # Wait before exit to avoid rapid restart loops
            return

        try:
            # Setup queues and bindings
            self.setup_queues()
            
            logger.info("Notification Service started. Waiting for events...")
            logger.info("Press CTRL+C to exit")
            
            # Start consuming messages
            self.rabbitmq.start_consuming()
                
        except KeyboardInterrupt:
            logger.info("Stopping notification service...")
            self.rabbitmq.stop_consuming()
            logger.info("Notification service stopped")
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
            # The RabbitMQ client handles reconnection internally
            time.sleep(5)
            self.start_consuming()

if __name__ == '__main__':
    service = NotificationService()
    service.start_consuming()

