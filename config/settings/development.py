"""
Development settings for local development.
"""
from .base import *

DEBUG = True

# Allow all hosts in local development
ALLOWED_HOSTS = ['*']

# Ensure CORS allows all local ports in development
CORS_ALLOW_ALL_ORIGINS = True

# Channels fallback to in-memory for local testing if Redis is not running
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
