from django.urls import re_path
from .consumers import HMOSGatewayConsumer

websocket_urlpatterns = [
    # Support both /ws and /ws/
    re_path(r'^ws/?$', HMOSGatewayConsumer.as_asgi()),
    # Support parameterized routes like /ws/operations/, /ws/kot/, /ws/notifications/
    re_path(r'^ws/(?P<channel_name>[\w\-]+)/?$', HMOSGatewayConsumer.as_asgi()),
]
