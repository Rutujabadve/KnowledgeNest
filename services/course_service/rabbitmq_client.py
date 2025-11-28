"""
RabbitMQ Client Utility for Course Service
Handles connection, message publishing, and event broadcasting
"""
import pika
import json
import os
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RabbitMQClient:
    """RabbitMQ client for publishing events"""
    
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', '5672'))
        self.username = os.getenv('RABBITMQ_USER', 'admin')
        self.password = os.getenv('RABBITMQ_PASS', 'password')
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
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def ensure_connection(self):
        """Ensure connection is active, reconnect if needed"""
        if self.connection is None or self.connection.is_closed:
            return self.connect()
        return True
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = 'topic'):
        """Declare an exchange"""
        if not self.ensure_connection():
            return False
        try:
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True
            )
            logger.info(f"Exchange '{exchange_name}' declared")
            return True
        except Exception as e:
            logger.error(f"Failed to declare exchange: {str(e)}")
            return False
    
    def publish_event(self, exchange: str, routing_key: str, event_data: Dict[Any, Any]):
        """
        Publish an event to RabbitMQ
        
        Args:
            exchange: Exchange name
            routing_key: Routing key (e.g., 'user.registered', 'course.enrolled')
            event_data: Event payload as dictionary
        """
        if not self.ensure_connection():
            logger.warning("Cannot publish event: RabbitMQ connection failed")
            return False
        
        try:
            # Declare exchange if not exists
            self.declare_exchange(exchange, 'topic')
            
            # Publish message
            message = json.dumps(event_data)
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Published event: {routing_key} to exchange: {exchange}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")
            return False
    
    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")

# Global instance
rabbitmq_client = RabbitMQClient()

