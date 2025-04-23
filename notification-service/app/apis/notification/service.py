"""Module with the Notification service to serve"""
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from redbird.templates import TemplateRepo

from .models import NotificationDB, WebSocketConnection


class NotificationService:
    """Service to interact with notifications in the database

    Args:
        notification_repo (TemplateRepo): Repository for the DB connection
    """

    def __init__(self, notification_repo: TemplateRepo) -> None:
        self.notification_repo = notification_repo

    async def get_user_notifications(
        self, user_id: str, page: int = 1, page_size: int = 10
    ) -> List[NotificationDB]:
        """Get paginated notifications for a specific user"""
        # Get all notifications and filter in-memory
        all_notifications = self.notification_repo.filter_by().all()
        
        # Filter for the user's notifications
        user_notifications = [n for n in all_notifications if user_id in n.delivered_to]
        
        # Sort by timestamp descending
        sorted_notifications = sorted(
            user_notifications,
            key=lambda n: n.timestamp,
            reverse=True
        )
        
        # Apply pagination
        offset = (page - 1) * page_size
        return sorted_notifications[offset:offset+page_size]

    async def get_notification_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        # Get all notifications
        all_notifications = self.notification_repo.filter_by().all()
        
        # Filter for unread notifications for this user
        unread_count = sum(1 for n in all_notifications if 
                            user_id in n.delivered_to and 
                            (not hasattr(n, 'read_by') or user_id not in n.read_by))
        
        return unread_count

    async def get_notification(
        self, notification_id: str, user_id: str
    ) -> Optional[NotificationDB]:
        """
        Get a specific notification by ID (only if the user has access)
        
        Args:
            notification_id: The notification ID
            user_id: The user ID making the request
            
        Returns:
            The notification if found and accessible, None otherwise
        """
        # Get the notification
        notification = self.notification_repo.filter_by(notification_id=notification_id).first()
        
        # Check if notification exists and user has access
        if notification and user_id in notification.delivered_to:
            return notification
            
        return None

    async def mark_notification_read(
        self, notification_id: str, user_id: str
    ) -> bool:
        """
        Mark a notification as read for a specific user
        
        Args:
            notification_id: The notification ID
            user_id: The user ID
            
        Returns:
            True if successful, False otherwise
        """
        # Get the notification
        notification = self.notification_repo.filter_by(notification_id=notification_id).first()
        
        # Check if notification exists and user has access
        if not notification or user_id not in notification.delivered_to:
            return False
            
        # Initialize read_by list if it doesn't exist
        if not hasattr(notification, 'read_by'):
            notification.read_by = []
            
        # Add user to read_by list if not already there
        if user_id not in notification.read_by:
            notification.read_by.append(user_id)
            
            # Update the notification
            self.notification_repo.filter_by(notification_id=notification_id).update(
                read_by=notification.read_by
            )
            
        return True

    async def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all notifications as read for a specific user"""
        # Get all notifications
        all_notifications = self.notification_repo.filter_by().all()
        
        # Filter for unread notifications for this user
        unread_notifications = [n for n in all_notifications if 
                            user_id in n.delivered_to and 
                            (not hasattr(n, 'read_by') or user_id not in n.read_by)]
        
        count = 0
        for notification in unread_notifications:
            # Initialize read_by list if needed
            if not hasattr(notification, 'read_by'):
                notification.read_by = []
                
            # Add user to read_by
            if user_id not in notification.read_by:
                notification.read_by.append(user_id)
                
                # Update notification
                self.notification_repo.filter_by(notification_id=notification.notification_id).update(
                    read_by=notification.read_by
                )
                count += 1
        
        return count

    async def save_notification(self, notification: NotificationDB) -> NotificationDB:
        """
        Save a new notification to the database
        
        Args:
            notification: The notification to save
            
        Returns:
            The saved notification with ID
        """
        # Save to database
        self.notification_repo.add(notification)
        return notification
        
    async def update_notification_delivery(
        self, notification_id: str, user_id: str
    ) -> bool:
        """
        Add a user to the delivered_to list for a notification
        
        Args:
            notification_id: The notification ID
            user_id: The user ID that received the notification
            
        Returns:
            True if successful, False otherwise
        """
        # Get the notification
        notification = self.notification_repo.filter_by(notification_id=notification_id).first()
        
        if not notification:
            return False
            
        # Add user to delivered_to if not already there
        if user_id not in notification.delivered_to:
            notification.delivered_to.append(user_id)
            
            # Update the notification
            self.notification_repo.filter_by(notification_id=notification_id).update(
                delivered_to=notification.delivered_to
            )
            
        return True