"""
RabbitMQ Client with Retry Logic for Notification Service
Handles connection, message publishing, and event broadcasting with automatic reconnection
"""
import pika
import json
import os
import logging
import time
import functools
from typing import Dict, Any, Optional, Callable, Union, List, Tuple

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
    """RabbitMQ client with automatic reconnection and retry logic for Notification Service"""
    
    def __init__(self, host: str = None, port: int = None, username: str = None, password: str = None, 
                 max_retries: int = 5, initial_backoff: float = 1.0):
        """Initialize RabbitMQ client with connection parameters and retry settings.
        
        Args:
            host: RabbitMQ server hostname or IP
            port: RabbitMQ server port
            username: RabbitMQ username
            password: RabbitMQ password
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial delay between retries in seconds
        """
        self.host = host or os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(port) if port is not None else int(os.getenv('RABBITMQ_PORT', '5672'))
        self.username = username or os.getenv('RABBITMQ_USER', 'admin')
        self.password = password or os.getenv('RABBITMQ_PASS', 'password')
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self._connection = None
        self._channel = None
        self._is_connected = False
        self._consuming = False
        self._consumer_tag = None
        self._queue_name = None
        self._consumer_callback = None
    
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
    def declare_queue(self, queue_name: str, durable: bool = True, 
                     exclusive: bool = False, auto_delete: bool = False, 
                     arguments: Optional[Dict] = None) -> str:
        """Declare a queue with retry logic"""
        if not self.ensure_connection():
            raise RuntimeError("Cannot declare queue: No connection to RabbitMQ")
            
        try:
            result = self.channel.queue_declare(
                queue=queue_name,
                durable=durable,
                exclusive=exclusive,
                auto_delete=auto_delete,
                arguments=arguments
            )
            self._queue_name = result.method.queue
            logger.info(f"Queue '{self._queue_name}' declared")
            return self._queue_name
            
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.error(f"Channel closed by broker while declaring queue: {str(e)}")
            self._channel = None
            raise
            
        except pika.exceptions.AMQPChannelError as e:
            logger.error(f"Channel error while declaring queue: {str(e)}")
            self._channel = None
            raise
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error while declaring queue: {str(e)}")
            self._is_connected = False
            self._connection = None
            self._channel = None
            raise
    
    @retry_on_failure(max_retries=3, initial_delay=0.5)
    def bind_queue(self, queue_name: str, exchange: str, routing_key: str) -> bool:
        """Bind a queue to an exchange with a routing key"""
        if not self.ensure_connection():
            raise RuntimeError("Cannot bind queue: No connection to RabbitMQ")
            
        try:
            self.channel.queue_bind(
                queue=queue_name,
                exchange=exchange,
                routing_key=routing_key
            )
            logger.info(f"Queue '{queue_name}' bound to exchange '{exchange}' with key '{routing_key}'")
            return True
            
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.error(f"Channel closed by broker while binding queue: {str(e)}")
            self._channel = None
            raise
            
        except pika.exceptions.AMQPChannelError as e:
            logger.error(f"Channel error while binding queue: {str(e)}")
            self._channel = None
            raise
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error while binding queue: {str(e)}")
            self._is_connected = False
            self._connection = None
            self._channel = None
            raise
    
    def setup_consumer(self, exchange: str, queue_name: str, routing_keys: List[str], 
                      callback: Callable, prefetch_count: int = 1) -> bool:
        """Set up a consumer with the given callback"""
        try:
            # Declare exchange and queue
            self.declare_exchange(exchange, 'topic')
            self.declare_queue(queue_name, durable=True)
            
            # Bind queue to exchange with each routing key
            for routing_key in routing_keys:
                self.bind_queue(queue_name, exchange, routing_key)
            
            # Set QoS for fair dispatch
            self.channel.basic_qos(prefetch_count=prefetch_count)
            
            # Set up consumer
            self._consumer_callback = callback
            self._consumer_tag = self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self._on_message,
                auto_ack=False
            )
            
            logger.info(f"Consumer set up on queue '{queue_name}' with routing keys: {routing_keys}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up consumer: {str(e)}")
            return False
    
    def _on_message(self, channel, method, properties, body):
        """Internal method to handle incoming messages"""
        try:
            # Parse message
            try:
                message = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message: {str(e)}")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Process message with callback
            if self._consumer_callback:
                try:
                    self._consumer_callback(channel, method, properties, message)
                except Exception as e:
                    logger.error(f"Error in consumer callback: {str(e)}")
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                logger.warning("No consumer callback set, message will be rejected")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
        except Exception as e:
            logger.error(f"Unexpected error processing message: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Start consuming messages"""
        if not self._consumer_tag:
            raise RuntimeError("Consumer not set up, call setup_consumer first")
            
        self._consuming = True
        logger.info("Starting consumer...")
        
        try:
            while self._consuming:
                try:
                    self.connection.process_data_events(time_limit=1)
                except pika.exceptions.AMQPConnectionError as e:
                    logger.error(f"Connection error while consuming: {str(e)}")
                    if self._consuming and self.ensure_connection():
                        # Re-setup consumer if connection was re-established
                        self.setup_consumer(
                            exchange='knowledge_nest_events',
                            queue_name=self._queue_name,
                            routing_keys=['user.*', 'course.*', 'review.*'],
                            callback=self._consumer_callback
                        )
                    else:
                        raise
                except Exception as e:
                    logger.error(f"Error while consuming: {str(e)}")
                    time.sleep(5)  # Prevent tight loop on errors
        except KeyboardInterrupt:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming messages"""
        if self._consuming:
            logger.info("Stopping consumer...")
            self._consuming = False
            if self.channel and self._consumer_tag:
                self.channel.basic_cancel(self._consumer_tag)
    
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
        self.stop_consuming()
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
