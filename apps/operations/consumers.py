import json
import logging
from datetime import datetime, timezone
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)

class HMOSGatewayConsumer(AsyncJsonWebsocketConsumer):
    """
    Unified Real-time Gateway WebSocket Consumer.
    Handles real-time events for front office, operations, KOT, housekeeping,
    and system-wide broadcast notifications.
    """

    DEFAULT_GROUPS = ['global', 'operations', 'notifications']

    async def connect(self):
        # Accept connection first
        await self.accept()

        # Join default broadcast groups
        self.subscribed_groups = set()
        for group in self.DEFAULT_GROUPS:
            await self.channel_layer.group_add(group, self.channel_name)
            self.subscribed_groups.add(group)

        # Send welcome payload
        await self.send_json({
            "channel": "system",
            "payload": {
                "status": "connected",
                "message": "HMOS Real-time Gateway Connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        })
        logger.info(f"WebSocket client connected: {self.channel_name}")

    async def disconnect(self, close_code):
        # Leave all groups
        if hasattr(self, 'subscribed_groups'):
            for group in self.subscribed_groups:
                await self.channel_layer.group_discard(group, self.channel_name)
        logger.info(f"WebSocket client disconnected: {self.channel_name} (code: {close_code})")

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming messages from client:
        Format: {"channel": "...", "data": ...} or {"action": "subscribe", "channel": "..."}
        """
        if not isinstance(content, dict):
            return

        action = content.get('action')
        target_channel = content.get('channel', 'global')
        data = content.get('data')

        # Handle subscription requests
        if action == 'subscribe' and target_channel:
            group_name = f"group_{target_channel}".replace('-', '_')
            await self.channel_layer.group_add(group_name, self.channel_name)
            self.subscribed_groups.add(group_name)
            await self.send_json({
                "channel": "system",
                "payload": {"status": "subscribed", "target": target_channel}
            })
            return

        # Handle ping/keepalive
        if content.get('type') == 'ping' or action == 'ping':
            await self.send_json({
                "channel": "system",
                "payload": {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
            })
            return

        # Broadcast message to channel group
        group_name = target_channel if target_channel in self.DEFAULT_GROUPS else f"group_{target_channel}".replace('-', '_')
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "broadcast.message",
                "channel": target_channel,
                "payload": data or content,
                "sender": self.channel_name
            }
        )

    async def broadcast_message(self, event):
        """
        Handler for messages dispatched to group via group_send
        """
        # Do not echo back to sender if flagged
        await self.send_json({
            "channel": event.get("channel", "global"),
            "payload": event.get("payload", {})
        })
