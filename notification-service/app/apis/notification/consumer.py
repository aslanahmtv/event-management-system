"""RabbitMQ consumer for notification service"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.apis.config import settings
from .models import Notification, NotificationType
from .connection import connection_manager  # Changed import from websocket to connection

class RabbitMQConsumer:
    """Consumer for RabbitMQ messages"""
    
    def __init__(self, notification_repo):
        """Initialize the consumer with repository for saving notifications"""
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        self.notification_repo = notification_repo
        self.retry_count = 0
        self.should_reconnect = True
        self.logger = logging.getLogger("notification_consumer")
    
    async def connect(self):
        """Connect to RabbitMQ and set up exchange/queue"""
        try:
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(
                settings.BROKER_URL,
                reconnect_interval=settings.RETRY_DELAY
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.EXCHANGE_NAME,
                type=aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                settings.QUEUE_NAME,
                durable=True
            )
            
            # Bind queue to exchange with routing key
            await self.queue.bind(
                exchange=self.exchange,
                routing_key=settings.ROUTING_KEY
            )
            
            # Start consuming messages
            await self.queue.consume(self.process_message)
            
            self.logger.info("Connected to RabbitMQ")
            self.retry_count = 0
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            self.retry_count += 1
            
            if self.retry_count < settings.MAX_RETRIES and self.should_reconnect:
                reconnect_delay = settings.RETRY_DELAY * (2 ** (self.retry_count - 1))
                self.logger.info(f"Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)
                await self.connect()
    
    async def process_message(self, message: AbstractIncomingMessage):
        """Process a message from RabbitMQ"""
        async with message.process():
            try:
                # Parse message body
                body = json.loads(message.body.decode())
                
                # Extract event data
                event_data = body.get("event", {})
                event_id = event_data.get("id")
                
                if not event_id:
                    self.logger.error("Received message without event ID")
                    return
                
                # Create notification object
                notification = Notification(
                    type="notification",
                    notification_type=body.get("notification_type"),
                    event=event_data,
                    user=body.get("user", "")
                )
                
                # Broadcast to WebSocket clients
                await connection_manager.broadcast_notification(
                    notification,
                    self.notification_repo,
                    event_id
                )
                
                self.logger.info(f"Processed {notification.notification_type} notification for event {event_id}")
                
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
    
    async def stop(self):
        """Stop the consumer"""
        self.should_reconnect = False
        
        if self.connection:
            await self.connection.close()
            self.logger.info("Disconnected from RabbitMQ")


async def start_consumer(notification_repo):
    """Start the RabbitMQ consumer"""
    consumer = RabbitMQConsumer(notification_repo)
    await consumer.connect()
    return consumer