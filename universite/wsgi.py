"""
WSGI config for universite project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'universite.settings')

application = get_wsgi_application()
