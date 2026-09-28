"""Template for the PythonAnywhere Web tab's WSGI configuration file.

Copy this file's contents into the WSGI file linked from the PythonAnywhere
Web tab, then replace the username in PROJECT_HOME. Do not put secrets here.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_HOME = Path('/home/YOUR_PYTHONANYWHERE_USERNAME/CEOBEF')
if not PROJECT_HOME.is_dir():
    raise RuntimeError(f'Update PROJECT_HOME in the PythonAnywhere WSGI file: {PROJECT_HOME}')

if str(PROJECT_HOME) not in sys.path:
    sys.path.insert(0, str(PROJECT_HOME))

load_dotenv(PROJECT_HOME / '.env')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('PYTHONANYWHERE', 'true')
os.environ.setdefault('DJANGO_SECURE_SSL_REDIRECT', 'true')
os.environ.setdefault('DJANGO_TRUST_PROXY_SSL', 'true')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
