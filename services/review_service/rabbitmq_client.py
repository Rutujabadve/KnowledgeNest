"""
RabbitMQ Client with Retry Logic for Review Service
Handles connection, message publishing, and event broadcasting with automatic reconnection
"""
import pika
import json
import os
import logging
import time
import functools
from typing import Dict, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('RabbitMQClient')
logger.addHandler(logging.StreamHandler())

def retry_on_failure(max_retries: int = 3, initial_delay: float = 1.0, max_delay: float = 30.0):
    """Decorator to retry a function with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep_time = min(delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                            f"Retrying in {sleep_time:.1f}s..."
                        )
                        time.sleep(sleep_time)
            
            logger.error(f"All {max_retries} attempts failed. Last error: {str(last_exception)}")
            raise last_exception
        return wrapper
    return decorator

class RabbitMQClient:
    """RabbitMQ client with automatic reconnection and retry logic"""
    
    def __init__(self, max_retries: int = 5, initial_backoff: float = 1.0):
        self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.getenv('RABBITMQ_PORT', '5672'))
        self.username = os.getenv('RABBITMQ_USER', 'admin')
        self.password = os.getenv('RABBITMQ_PASS', 'password')
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self._connection = None
        self._channel = None
        self._is_connected = False
    
    @property
    def connection(self):
        """Lazy-loading connection property with reconnection"""
        if not self._is_connected or self._connection is None or self._connection.is_closed:
            self.connect()
        return self._connection
    
    @property
    def channel(self):
        """Lazy-loading channel property with reconnection"""
        if self._channel is None or self._channel.is_closed:
            if self.connection:
                self._channel = self.connection.channel()
        return self._channel
    
    @retry_on_failure(max_retries=3, initial_delay=1.0)
    def connect(self) -> bool:
        """Establish connection to RabbitMQ with retry logic"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                connection_attempts=3,
                retry_delay=5,
                socket_timeout=5,
                blocked_connection_timeout=300
            )
            
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            self._is_connected = True
            
            # Configure connection-level error handling
            def on_connection_error(conn, error):
                logger.error(f"Connection error: {error}")
                self._is_connected = False
                self._connection = None
                self._channel = None
            
            def on_connection_blocked(conn, method):
                logger.warning(f"Connection blocked: {method.reason}")
            
            def on_connection_unblocked(conn):
                logger.info("Connection unblocked")
            
            self._connection.add_on_connection_blocked_callback(on_connection_blocked)
            self._connection.add_on_connection_unblocked_callback(on_connection_unblocked)
            
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self._is_connected = False
            self._connection = None
            self._channel = None
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    def ensure_connection(self, retry: bool = True) -> bool:
        """Ensure connection is active, reconnect if needed"""
        if self._is_connected and self._connection and not self._connection.is_closed:
            return True
            
        if retry:
            try:
                return self.connect()
            except Exception as e:
                logger.error(f"Failed to ensure connection: {str(e)}")
                return False
        return False
    
    @retry_on_failure(max_retries=3, initial_delay=0.5)
    def declare_exchange(self, exchange_name: str, exchange_type: str = 'topic') -> bool:
        """Declare an exchange with retry logic"""
        if not self.ensure_connection():
            raise RuntimeError("Cannot declare exchange: No connection to RabbitMQ")
            
        try:
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True,
                passive=False,
                auto_delete=False,
                internal=False,
                arguments=None
            )
            logger.info(f"Exchange '{exchange_name}' declared")
            return True
            
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.error(f"Channel closed by broker while declaring exchange: {str(e)}")
            self._channel = None
            raise
            
        except pika.exceptions.AMQPChannelError as e:
            logger.error(f"Channel error while declaring exchange: {str(e)}")
            self._channel = None
            raise
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error while declaring exchange: {str(e)}")
            self._is_connected = False
            self._connection = None
            self._channel = None
            raise
    
    @retry_on_failure(max_retries=3, initial_delay=0.5)
    def publish_event(self, exchange: str, routing_key: str, event_data: Dict[Any, Any]) -> bool:
        """Publish an event to RabbitMQ with retry logic"""
        if not self.ensure_connection():
            raise RuntimeError("Cannot publish event: No connection to RabbitMQ")
        
        try:
            # Ensure exchange exists
            self.declare_exchange(exchange, 'topic')
            
            # Prepare message
            message = json.dumps(event_data)
            properties = pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                content_type='application/json',
                content_encoding='utf-8',
                timestamp=int(time.time())
            )
            
            # Publish with confirmation
            self.channel.confirm_delivery()
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message,
                properties=properties,
                mandatory=True
            )
            
            logger.debug(f"Published event: {routing_key} to exchange: {exchange}")
            return True
            
        except pika.exceptions.UnroutableError:
            logger.error(
                f"Message could not be routed (no queues bound to exchange "
                f"'{exchange}' with routing key '{routing_key}')"
            )
            return False
            
        except pika.exceptions.NackError:
            logger.error("Message was not acknowledged by broker")
            return False
            
        except pika.exceptions.AMQPChannelError as e:
            logger.error(f"Channel error while publishing: {str(e)}")
            self._channel = None
            raise
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error while publishing: {str(e)}")
            self._is_connected = False
            self._connection = None
            self._channel = None
            raise
    
    def close(self):
        """Close RabbitMQ connection"""
        self._is_connected = False
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")
        finally:
            self._connection = None
            self._channel = None

# Global instance with retry configuration
rabbitmq_client = RabbitMQClient(
    max_retries=5,
    initial_backoff=1.0
)


