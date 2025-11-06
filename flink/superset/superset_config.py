"""
Apache Superset Configuration for Flink POC
"""
import os

# Superset specific config
ROW_LIMIT = 5000
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'your-secret-key-change-this')

# Flask App Builder configuration
# Your App secret key
SECRET_KEY = SECRET_KEY

# The SQLAlchemy connection string to your database backend
SQLALCHEMY_DATABASE_URI = 'sqlite:////app/superset_home/superset.db'

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = ''

# Security
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_TIME_LIMIT = None

# Enable scheduled queries
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'SCHEDULED_QUERIES': True,
}

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
}

# Set timeout for queries
SUPERSET_WEBSERVER_TIMEOUT = 300
