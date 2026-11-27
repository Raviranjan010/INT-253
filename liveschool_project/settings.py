"""
Django settings for liveschool_project project.
Live School for World-Class Free Education (INT-253)
"""

import os
import re
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local environment variables (.env file takes precedence locally; cloud deployments inject environment variables)
load_dotenv(BASE_DIR / '.env', override=False)

# DEBUG Configuration (defaults to True in local development, override with DEBUG=False in production)
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't', 'yes')

# SECRET_KEY Handling: Enforce secure key in production; fallback allowed only in DEBUG mode
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-key-liveschool-int253-local-development-only'
    else:
        raise ValueError("Critical Security Error: The SECRET_KEY environment variable must be set when DEBUG is False!")

if not DEBUG and (len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith('django-insecure-')):
    raise ImproperlyConfigured('Set SECRET_KEY to a generated secret of at least 50 characters.')

CERTIFICATE_SIGNING_KEY = os.getenv('CERTIFICATE_SIGNING_KEY') or (SECRET_KEY if DEBUG else '')
CERTIFICATE_LEGACY_SIGNING_KEY = os.getenv('CERTIFICATE_LEGACY_SIGNING_KEY') or (SECRET_KEY if DEBUG else '')
if not DEBUG and (len(CERTIFICATE_SIGNING_KEY) < 50 or CERTIFICATE_SIGNING_KEY == SECRET_KEY):
    raise ImproperlyConfigured('Set a separate CERTIFICATE_SIGNING_KEY of at least 50 characters.')

# ALLOWED_HOSTS: Environment-driven host list (no wildcards by default)
allowed_hosts_env = os.getenv('ALLOWED_HOSTS')
if allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
if not DEBUG and (not allowed_hosts_env or not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS):
    raise ImproperlyConfigured('Set ALLOWED_HOSTS to the explicit production hostnames.')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom Live School Apps
    'accounts.apps.AccountsConfig',
    'core.apps.CoreConfig',
    'courses.apps.CoursesConfig',
    'live_classes.apps.LiveClassesConfig',
    'quizzes.apps.QuizzesConfig',
    'community.apps.CommunityConfig',
    'certificates.apps.CertificatesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'liveschool_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'liveschool_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.getenv('SQLITE_PATH') or BASE_DIR / 'db.sqlite3',
    }
}

# Use a managed PostgreSQL service in production when DATABASE_URL is set.
# SQLite remains the zero-configuration local development default.
DATABASE_URL = os.getenv('DATABASE_URL')
if not DEBUG and not DATABASE_URL:
    raise ImproperlyConfigured('Production requires a PostgreSQL DATABASE_URL.')
if DATABASE_URL:
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=os.getenv(
            'DATABASE_SSL_REQUIRE', 'False' if DEBUG else 'True'
        ).lower() in ('true', '1', 't', 'yes'),
    )
    if not DEBUG and DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
        raise ImproperlyConfigured('Production DATABASE_URL must point to PostgreSQL.')

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'
AUTHENTICATION_BACKENDS = ['accounts.backends.EmailOrUsernameBackend']

RESEND_API_KEY = os.getenv('RESEND_API_KEY')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
CONTACT_NOTIFICATION_EMAIL = os.getenv('CONTACT_NOTIFICATION_EMAIL', '')
EMAIL_BACKEND = (
    'django.core.mail.backends.console.EmailBackend' if DEBUG else
    'core.email.ResendBackend' if RESEND_API_KEY else
    'django.core.mail.backends.dummy.EmailBackend'
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Modern Django STORAGES Configuration with Whitenoise compression
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedStaticFilesStorage" if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

if not DEBUG or os.getenv('MEDIA_BUCKET'):
    storage_fields = {
        'bucket_name': 'MEDIA_BUCKET',
        'access_key': 'MEDIA_ACCESS_KEY_ID',
        'secret_key': 'MEDIA_SECRET_ACCESS_KEY',
    }
    storage_options = {option: os.getenv(variable) for option, variable in storage_fields.items()}
    missing = [variable for option, variable in storage_fields.items() if not storage_options[option]]
    if missing:
        raise ImproperlyConfigured('Object storage requires ' + ', '.join(missing))
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            **storage_options,
            'endpoint_url': os.getenv('MEDIA_ENDPOINT_URL') or None,
            'region_name': os.getenv('MEDIA_REGION', 'us-east-1'),
            'file_overwrite': False,
            'querystring_auth': True,
            'addressing_style': 'path',
        },
    }
    STORAGES['staticfiles']['BACKEND'] = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
elif os.getenv('STATIC_MANIFEST') == '1':
    STORAGES['staticfiles']['BACKEND'] = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'accounts:dashboard_redirect'
LOGOUT_REDIRECT_URL = 'core:home'
LOGIN_URL = 'accounts:login'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Jitsi Meet Domain for WebRTC Live Classroom
JITSI_DOMAIN = os.getenv('JITSI_DOMAIN', '')
JAAS_APP_ID = os.getenv('JAAS_APP_ID', '')
JAAS_KID = os.getenv('JAAS_KID', '')
JAAS_PRIVATE_KEY = os.getenv('JAAS_PRIVATE_KEY', '').replace('\\n', '\n')
if any((JAAS_APP_ID, JAAS_KID, JAAS_PRIVATE_KEY)) and not (
    re.fullmatch(r'vpaas-magic-cookie-[a-zA-Z0-9_-]+', JAAS_APP_ID)
    and JAAS_KID.startswith(JAAS_APP_ID + '/') and JAAS_PRIVATE_KEY
):
    raise ImproperlyConfigured('Set a matching JAAS_APP_ID, JAAS_KID, and JAAS_PRIVATE_KEY.')
CACHE_GLOBAL_STATS = not DEBUG
if JITSI_DOMAIN and not all(part and part.replace('-', '').isalnum() for part in JITSI_DOMAIN.split('.')):
    raise ImproperlyConfigured('JITSI_DOMAIN must be a hostname.')

# Production Security Hardening
if not DEBUG:
    conferencing = [f'https://{JITSI_DOMAIN}'] if JITSI_DOMAIN and JITSI_DOMAIN != 'meet.jit.si' else []
    if JAAS_APP_ID:
        conferencing.append('https://8x8.vc')
    SECURE_CSP_REPORT_ONLY = {
        'default-src': ["'self'"],
        'base-uri': ["'self'"],
        'object-src': ["'none'"],
        'frame-ancestors': ["'none'"],
        'script-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', *conferencing],
        'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
        'font-src': ["'self'", 'https://fonts.gstatic.com', 'https://cdn.jsdelivr.net'],
        'img-src': ["'self'", 'https:', 'data:'],
        'frame-src': ['https://www.youtube-nocookie.com', 'https://player.vimeo.com', *conferencing],
    }
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 't', 'yes')
    hsts_seconds = os.getenv('SECURE_HSTS_SECONDS', '31536000')
    if hsts_seconds:
        SECURE_HSTS_SECONDS = int(hsts_seconds)
        SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv(
            'SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False'
        ).lower() in ('true', '1', 't', 'yes')
        SECURE_HSTS_PRELOAD = os.getenv(
            'SECURE_HSTS_PRELOAD', 'False'
        ).lower() in ('true', '1', 't', 'yes')
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
