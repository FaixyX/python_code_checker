from os import getenv as env
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY SETTINGS
SECRET_KEY = env("SECRET_KEY")
SERVER_IP = env("SERVER_IP")
SERVER_URL = env("SERVER_URL")
DEBUG = bool(env("DEBUG", 1))
ALLOWED_HOSTS = env("ALLOWED_HOSTS", f"127.0.0.1,localhost,{SERVER_IP}").split(",")

# REST FRAMEWORK
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": env('PAGE_SIZE', 10),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication'
    )
}

# INSTALLED APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework.authtoken',
    'interface',
    'authemail',
]

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # must be before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS SETTINGS
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS",
    f"http://localhost:3000,http://127.0.0.1:3000, http://127.0.0.1:8000,{SERVER_URL}:8000").split(",")
CORS_ALLOW_ALL_ORIGINS = env("CORS_ALLOW_ALL_ORIGINS", "False").lower() == "true"
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'project.urls'

# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# DATABASE
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": env("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": env("DB_USER", None),
        "PASSWORD": env("DB_PASSWORD", None),
        "HOST": env("DB_HOST", None),
        "PORT": env("DB_PORT", None),
    }
}

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# I18N
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT CONFIG
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=120),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# CUSTOM USER MODEL
AUTH_USER_MODEL = 'interface.MyUser'

# EMAIL SETTINGS
EMAIL_FROM = env('Email')
EMAIL_BCC = env('Email')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_SSL = True
EMAIL_PORT = 465
EMAIL_HOST_USER = env('Email')
EMAIL_HOST_PASSWORD = env('Password')

# MISC
APPEND_SLASH = False
OPENAI_API_KEY = env('open_ai_key')

# GOOGLE OAUTH SETTINGS
GOOGLE_OAUTH2_REDIRECT_URI = env('LOGIN_REDIRECT_URL')
GOOGLE_OAUTH2_CLIENT_ID = env('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
GOOGLE_OAUTH2_CLIENT_SECRET = env('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
FRONTEND_REDIRECT_URL = env('FRONTEND_REDIRECT_URL')
