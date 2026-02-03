from pathlib import Path
import os
import environ

# ------------------------------
# Base Paths
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------
# Initialize environment
# ------------------------------
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ------------------------------
# Security
# ------------------------------
SECRET_KEY = env('SECRET_KEY', default='django-insecure-default')
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'localhost',
    'v2.rekjrc.com',
    'rekjrc.com',
    'www.rekjrc.com',
])

INTERNAL_IPS = [
    "127.0.0.1",
]

# ------------------------------
# Stripe (optional)
# ------------------------------
STRIPE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')

# ------------------------------
# Installed Apps
# ------------------------------
INSTALLED_APPS = [
    # Django defaults
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'django_user_agents',
    'django_extensions',
    'phonenumber_field',
    'widget_tweaks',
    "rest_framework",

    # Ownable apps
    "builds",
    "clubs",
    "drivers",
    "events",
    "locations",
    "posts",
    "races",
    "stores",
    "teams",
    "tracks",

    # Event apps
    "crawler",
    "dragrace",
    "judged",
    "longjump",
    "stopwatch",
    "topspeed",
    "laprace",

    # Site apps
    "accounts",
    "chat_app",
    "crud",
    "sponsors",
    "stripe_app",
    "pages",
    "urls_app",
]

# ------------------------------
# Middleware
# ------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
]

# ------------------------------
# CORS
# ------------------------------
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware"] + MIDDLEWARE
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:3000",
    "https://rekjrc.com",
    "https://www.rekjrc.com",
]

# ------------------------------
# URL Config
# ------------------------------
ROOT_URLCONF = "rekjrc.urls"

# ------------------------------
# Templates
# ------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                #"rekjrc.context.device_type",
                #"sponsors.context_processors.sponsors_context",
            ],
        },
    },
]

# ------------------------------
# WSGI
# ------------------------------
WSGI_APPLICATION = "rekjrc.wsgi.application"

# ------------------------------
# Database (Postgres)
# ------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'TEST': {'NAME':env('DB_NAME_TEST')},
    }
}

# ------------------------------
# Password Validation
# ------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------
# Internationalization
# ------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------------
# Static & Media files
# ------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------
# Default Primary Key Type
# ------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------
# Custom User Model
# ------------------------------
AUTH_USER_MODEL = "auth.User"

# ------------------------------
# Login/Logout redirect
# ------------------------------
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ------------------------------
# CSRF Trusted Origins (Django 6)
# ------------------------------
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    "https://www.rekjrc.com",
    "https://rekjrc.com",
    "http://10.1.1.63",
    "http://127.0.0.1",
    "http://localhost",
])
