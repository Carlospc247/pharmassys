import os
from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url
from storages.backends.s3boto3 import S3Boto3Storage
from celery.schedules import crontab
import environ




BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================
# Core
# =========================================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=lambda v: v.lower() in ('true', '1', 't'))
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# =========================================
# Application definition
# =========================================
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    
    # Terceiros
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_tailwind',
    'widget_tweaks',
    'django_filters',
    'django_extensions',
    
    # Seus apps
    'apps.core',
    'apps.produtos',
    'apps.licenca',
    'apps.fornecedores',
    'apps.estoque',
    'apps.clientes',
    'apps.analytics',
    'apps.vendas',
    'apps.funcionarios',
    'apps.servicos',
    'apps.comandas',
    'apps.financeiro',
    'apps.relatorios',
    'apps.configuracoes',
    'apps.fiscal',
    'apps.saft',
    'apps.compras',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'apps.core.middleware.AccountsProfileRedirectMiddleware',
]

ROOT_URLCONF = 'pharmassys.urls'
WSGI_APPLICATION = 'pharmassys.wsgi.application'


CELERY_BEAT_SCHEDULE = {
    'backup_diario': {
        'task': 'apps.configuracoes.tasks.backup_automatico_diario',
        'schedule': crontab(hour=2, minute=0),  # todos os dias às 2h
    },
    'check-critical-margin-daily': {
         'task': 'apps.vendas.tasks.verificar_margem_critica',
         'schedule': timedelta(days=1), # Executa a cada 24h
     },
     'check-critical-stock-hourly': {
         'task': 'apps.vendas.tasks.verificar_stock_critico',
         'schedule': timedelta(hours=1), # Executa a cada 1h
     },
}


# Exemplo de configuração de Celery Beat (configuração no settings.py)
CELERY_BEAT_SCHEDULE = {
     'check-critical-margin-daily': {
         'task': 'apps.vendas.tasks.verificar_margem_critica',
         'schedule': timedelta(days=1), # Executa a cada 24h
     },
     'check-critical-stock-hourly': {
         'task': 'apps.vendas.tasks.verificar_stock_critico',
         'schedule': timedelta(hours=1), # Executa a cada 1h
     },
}


# settings.py (CONFIGURAÇÃO OTIMIZADA DE CACHE E CELERY)



REDIS_HOST = env('REDIS_HOST', default='127.0.0.1') 
REDIS_PORT = env.int('REDIS_PORT', default=6379)

# URL Base para Construção: redis://HOST:PORT
REDIS_URL_BASE = f"redis://{REDIS_HOST}:{REDIS_PORT}"

# =================================================================
# CACHES (Django Cache)
# =================================================================

CACHES = {
    # 1. Cache Padrão: DB 1
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL_BASE}/1", # DB 1 para sessões/cache geral
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100}, # Otimização de conexão
        }
    },
    # 2. Cache de Business Intelligence (B.I.): DB 2
    "B.I.": { 
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL_BASE}/2", # DB 2 para isolar os dados de Rentabilidade
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# =================================================================
# CELERY (Tarefas Assíncronas)
# =================================================================

# 3. Celery Broker e Backend: DB 0
# Lê a variável CELERY_BROKER_URL, mas se não estiver definida, usa a URL Base + DB 0
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=f'{REDIS_URL_BASE}/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=f'{REDIS_URL_BASE}/0')



# =========================================
# Database
# =========================================
if config('DATABASE_URL', default=None):
    DATABASES = {'default': dj_database_url.parse(config('DATABASE_URL'))}
else:
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', cast=int),
        }
    }

# =========================================
# Templates
# =========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.i18n',
                'apps.core.context_processors.dashboard_data',
            ],
        },
    },
]

# =========================================
# Password validation
# =========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =========================================
# Internationalization
# =========================================
LANGUAGE_CODE = 'pt'
TIME_ZONE = 'Africa/Luanda'
USE_I18N = True
USE_TZ = True

# =========================================
# Static & Media via AWS S3
# =========================================
if not DEBUG:
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# =========================================
# Security
# =========================================
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# 🔥 CORRIGIDO: CSRF TRUSDED ORIGINS
CSRF_TRUSTED_ORIGINS = [
    "https://vistogest.pro",
    "https://www.vistogest.pro",
    "https://vistogest-env.eba-si92zp36.us-east-1.elasticbeanstalk.com",
]

# =========================================
# Email (Hostinger)
# =========================================
EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# =========================================
# Django Allauth
# =========================================
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# =========================================
# JWT / REST Framework
# =========================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}

# =========================================
# Default primary key
# =========================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.Usuario'
