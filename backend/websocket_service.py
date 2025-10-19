"""
Real-time WebSocket Service for Admin Verification and Notifications
Handles real-time communication for admin requests, approvals, and system notifications
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time communication with memory leak prevention"""
    
    def __init__(self):
        # Active connections by user ID
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Admin connections (system admins and campus admins)
        self.admin_connections: Dict[str, Set[WebSocket]] = {}
        # System admin connections (for admin request notifications)
        self.system_admin_connections: Set[WebSocket] = set()
        # Track connection timestamps for cleanup
        self.connection_timestamps: Dict[WebSocket, datetime] = {}
        # Heartbeat interval in seconds
        self.heartbeat_interval = 30
        # Connection timeout in seconds (5 minutes of inactivity)
        self.connection_timeout = 300
        # Background cleanup task
        self._cleanup_task = None
        
    async def connect_user(self, websocket: WebSocket, user_id: str):
        """Connect a regular user for notifications"""
        await websocket.accept()
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        
        self.user_connections[user_id].add(websocket)
        self.connection_timestamps[websocket] = datetime.now(timezone.utc)
        logger.info(f"User {user_id} connected via WebSocket")
        
        # Start cleanup task if not running
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        # Send initial connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to real-time notifications",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)

    async def connect_admin(self, websocket: WebSocket, user_id: str, admin_type: str = "campus_admin"):
        """Connect an admin user (campus admin or system admin)"""
        await websocket.accept()
        
        if user_id not in self.admin_connections:
            self.admin_connections[user_id] = set()
        
        self.admin_connections[user_id].add(websocket)
        self.connection_timestamps[websocket] = datetime.now(timezone.utc)
        
        # Add to system admin connections if applicable
        if admin_type == "system_admin":
            self.system_admin_connections.add(websocket)
        
        logger.info(f"Admin {user_id} ({admin_type}) connected via WebSocket")
        
        # Start cleanup task if not running
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        # Send initial connection confirmation with admin privileges
        await self.send_personal_message({
            "type": "admin_connection_established",
            "admin_type": admin_type,
            "message": f"Connected to admin real-time system ({admin_type})",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)

    async def disconnect_user(self, websocket: WebSocket, user_id: str):
        """Disconnect a user and clean up resources"""
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Also remove from admin connections if applicable
        if user_id in self.admin_connections:
            self.admin_connections[user_id].discard(websocket)
            if not self.admin_connections[user_id]:
                del self.admin_connections[user_id]
        
        # Remove from system admin connections
        self.system_admin_connections.discard(websocket)
        
        # Remove from timestamp tracking
        self.connection_timestamps.pop(websocket, None)
        
        # Close WebSocket connection properly
        try:
            await websocket.close()
        except Exception as e:
            logger.debug(f"Error closing WebSocket (may already be closed): {str(e)}")
        
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def _periodic_cleanup(self):
        """Periodically clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Run cleanup every minute
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}")
    
    async def _cleanup_stale_connections(self):
        """Remove stale connections that haven't responded to heartbeat"""
        now = datetime.now(timezone.utc)
        stale_connections = []
        
        # Find stale connections
        for websocket, timestamp in self.connection_timestamps.items():
            if (now - timestamp).total_seconds() > self.connection_timeout:
                stale_connections.append(websocket)
        
        # Clean up stale connections
        for websocket in stale_connections:
            logger.info(f"Cleaning up stale connection (inactive for {self.connection_timeout}s)")
            
            # Remove from all connection sets
            for user_id, connections in list(self.user_connections.items()):
                if websocket in connections:
                    connections.discard(websocket)
                    if not connections:
                        del self.user_connections[user_id]
            
            for admin_id, connections in list(self.admin_connections.items()):
                if websocket in connections:
                    connections.discard(websocket)
                    if not connections:
                        del self.admin_connections[user_id]
            
            self.system_admin_connections.discard(websocket)
            self.connection_timestamps.pop(websocket, None)
            
            # Try to close the connection
            try:
                await websocket.close()
            except:
                pass
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")
    
    async def update_connection_timestamp(self, websocket: WebSocket):
        """Update the last activity timestamp for a connection"""
        self.connection_timestamps[websocket] = datetime.now(timezone.utc)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
            # Update timestamp on successful message send
            await self.update_connection_timestamp(websocket)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")

    async def send_user_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send notification to specific user's all connections"""
        if user_id in self.user_connections:
            disconnected_sockets = set()
            
            for websocket in self.user_connections[user_id].copy():
                try:
                    await websocket.send_text(json.dumps(notification))
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {str(e)}")
                    disconnected_sockets.add(websocket)
            
            # Clean up disconnected sockets
            for socket in disconnected_sockets:
                self.user_connections[user_id].discard(socket)

    async def send_admin_notification(self, notification: Dict[str, Any], admin_type: str = "all"):
        """Send notification to admin users"""
        target_connections = set()
        
        if admin_type == "system_admin":
            target_connections = self.system_admin_connections.copy()
        elif admin_type == "campus_admin":
            # Send to all campus admins
            for admin_id, connections in self.admin_connections.items():
                # Filter out system admins from campus admin notifications
                target_connections.update(connections)
        else:  # admin_type == "all"
            # Send to all admins
            for admin_id, connections in self.admin_connections.items():
                target_connections.update(connections)
            target_connections.update(self.system_admin_connections)
        
        disconnected_sockets = set()
        
        for websocket in target_connections:
            try:
                await websocket.send_text(json.dumps(notification))
            except Exception as e:
                logger.error(f"Error sending admin notification: {str(e)}")
                disconnected_sockets.add(websocket)
        
        # Clean up disconnected sockets
        for socket in disconnected_sockets:
            self.system_admin_connections.discard(socket)

    async def broadcast_system_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected users"""
        all_connections = set()
        
        # Collect all user connections
        for user_id, connections in self.user_connections.items():
            all_connections.update(connections)
        
        # Collect all admin connections
        for admin_id, connections in self.admin_connections.items():
            all_connections.update(connections)
        
        all_connections.update(self.system_admin_connections)
        
        disconnected_sockets = set()
        
        for websocket in all_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting: {str(e)}")
                disconnected_sockets.add(websocket)

    def get_connected_users_count(self) -> int:
        """Get total number of connected users"""
        return len(self.user_connections)

    def get_connected_admins_count(self) -> int:
        """Get total number of connected admins"""
        return len(self.admin_connections) + len(self.system_admin_connections)


class RealTimeNotificationService:
    """Service for handling real-time notifications"""
    
    def __init__(self, db: AsyncIOMotorDatabase, connection_manager: ConnectionManager):
        self.db = db
        self.connection_manager = connection_manager

    async def notify_admin_request_submitted(self, request_data: Dict[str, Any]):
        """Notify system admins about new admin request"""
        notification = {
            "type": "admin_request_submitted",
            "title": "New Admin Request",
            "message": f"New admin request from {request_data.get('full_name', 'Unknown')} at {request_data.get('college_name', 'Unknown College')}",
            "data": {
                "request_id": request_data.get('id'),
                "college_name": request_data.get('college_name'),
                "admin_type": request_data.get('requested_admin_type'),
                "verification_method": request_data.get('verification_method')
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": "high"
        }
        
        await self.connection_manager.send_admin_notification(notification, "system_admin")
        logger.info(f"Sent admin request notification for request {request_data.get('id')}")

    async def notify_admin_request_status_update(self, user_id: str, request_data: Dict[str, Any]):
        """Notify user about admin request status update"""
        status = request_data.get('status', 'unknown')
        
        # Determine message based on status
        status_messages = {
            "under_review": "Your admin request is now under review by system administrators",
            "approved": "🎉 Congratulations! Your admin request has been approved",
            "rejected": "Your admin request has been rejected. Please check the details for more information"
        }
        
        notification = {
            "type": "admin_request_status_update",
            "title": f"Admin Request {status.title()}",
            "message": status_messages.get(status, f"Admin request status updated to {status}"),
            "data": {
                "request_id": request_data.get('id'),
                "status": status,
                "review_notes": request_data.get('review_notes'),
                "rejection_reason": request_data.get('rejection_reason'),
                "admin_privileges": request_data.get('admin_privileges', {})
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": "high" if status in ["approved", "rejected"] else "medium"
        }
        
        await self.connection_manager.send_user_notification(user_id, notification)
        logger.info(f"Sent status update notification to user {user_id} for request {request_data.get('id')}")

    async def notify_document_uploaded(self, user_id: str, document_data: Dict[str, Any]):
        """Notify about successful document upload"""
        notification = {
            "type": "document_uploaded",
            "title": "Document Uploaded Successfully",
            "message": f"Your {document_data.get('document_type', 'document').replace('_', ' ')} has been uploaded and is being processed",
            "data": {
                "document_type": document_data.get('document_type'),
                "filename": document_data.get('filename'),
                "upload_timestamp": document_data.get('uploaded_at')
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": "medium"
        }
        
        await self.connection_manager.send_user_notification(user_id, notification)

    async def notify_email_verification_status(self, user_id: str, verification_data: Dict[str, Any]):
        """Notify about email verification status"""
        is_verified = verification_data.get('verified', False)
        
        notification = {
            "type": "email_verification_update",
            "title": "Email Verification Update",
            "message": "✅ Email verified successfully" if is_verified else "Email verification failed. Please try again or use alternative verification methods",
            "data": {
                "email_domain": verification_data.get('domain'),
                "verified": is_verified,
                "verification_method": verification_data.get('verification_method'),
                "auto_approved": verification_data.get('auto_approved', False)
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": "high" if is_verified else "medium"
        }
        
        await self.connection_manager.send_user_notification(user_id, notification)

    async def notify_admin_privileges_granted(self, user_id: str, admin_data: Dict[str, Any]):
        """Notify user about admin privileges being granted"""
        notification = {
            "type": "admin_privileges_granted",
            "title": "🎉 Admin Privileges Activated!",
            "message": f"Your {admin_data.get('admin_type', 'admin').replace('_', ' ')} privileges are now active. Welcome to the admin panel!",
            "data": {
                "admin_type": admin_data.get('admin_type'),
                "permissions": admin_data.get('permissions', []),
                "can_create_inter_college": admin_data.get('can_create_inter_college', False),
                "max_competitions_per_month": admin_data.get('max_competitions_per_month', 0),
                "expires_at": admin_data.get('expires_at')
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": "high"
        }
        
        await self.connection_manager.send_user_notification(user_id, notification)

    async def notify_system_maintenance(self, message: str, duration_minutes: int = None):
        """Notify all users about system maintenance"""
        notification = {
            "type": "system_maintenance",
            "title": "🔧 System Maintenance Notice",
            "message": message,
            "data": {
                "duration_minutes": duration_minutes,
                "maintenance_start": datetime.now(timezone.utc).isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": "high"
        }
        
        await self.connection_manager.broadcast_system_message(notification)

    async def create_and_notify_in_app_notification(self, user_id: str, notification_data: Dict[str, Any]):
        """Create in-app notification and send real-time notification"""
        try:
            # Create in-app notification in database
            notification_doc = {
                "user_id": user_id,
                "notification_type": notification_data.get("type", "general"),
                "title": notification_data.get("title", ""),
                "message": notification_data.get("message", ""),
                "action_url": notification_data.get("action_url"),
                "is_read": False,
                "created_at": datetime.now(timezone.utc),
                "related_id": notification_data.get("related_id"),
                "data": notification_data.get("data", {})
            }
            
            # Insert into database
            result = await self.db.in_app_notifications.insert_one(notification_doc)
            notification_doc["id"] = str(result.inserted_id)
            
            # Send real-time notification
            real_time_notification = {
                "type": notification_data.get("type", "general"),
                "title": notification_data.get("title", ""),
                "message": notification_data.get("message", ""),
                "data": notification_data.get("data", {}),
                "notification_id": notification_doc["id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "priority": notification_data.get("priority", "medium")
            }
            
            await self.connection_manager.send_user_notification(user_id, real_time_notification)
            
            return notification_doc
            
        except Exception as e:
            logger.error(f"Error creating and sending notification: {str(e)}")
            return None


# Global connection manager instance
connection_manager = ConnectionManager()

# Function to get notification service
async def get_notification_service(db: AsyncIOMotorDatabase = None) -> RealTimeNotificationService:
    """Get notification service instance"""
    if db is None:
        from database import get_database
        db = await get_database()
    
    return RealTimeNotificationService(db, connection_manager)
