"""
WSGI config for airport_service project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

<<<<<<< HEAD
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airport_service.settings")
=======
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airport_service.settings')
>>>>>>> 5f99da08ee1571631d25ad7881494c2e70f05258

application = get_wsgi_application()
