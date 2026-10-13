
"""
Django settings for config project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# BASE_DIR: thư mục backend (chứa manage.py, config/, home/, shop/)
BASE_DIR = Path(__file__).resolve().parent.parent
# PROJECT_ROOT: thư mục gốc dự án (chứa frontend/, .env, ca.pem, db, media)
PROJECT_ROOT = BASE_DIR.parent

# Đọc file .env
load_dotenv(PROJECT_ROOT / ".env")

# Cloudinary
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")


# =========================
# SECURITY
# =========================

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost"
    ).split(",")
    if host.strip()
]

# Render (và các proxy HTTPS khác) gửi request tới app qua HTTP nội bộ,
# nên Django cần tin header X-Forwarded-Proto để nhận biết kết nối HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Danh sách origin được phép gửi form (CSRF), ví dụ:
# DJANGO_CSRF_TRUSTED_ORIGINS=https://shop-sbcb.onrender.com
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"


# =========================
# APPLICATIONS
# =========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'cloudinary',

    'home',
    'shop',
]


# =========================
# MIDDLEWARE
# =========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


# =========================
# TEMPLATES
# =========================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [PROJECT_ROOT / 'frontend' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.cart',
                'shop.context_processors.nav_categories',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# =========================
# DATABASE
# =========================
MYSQL_DATABASE = 'sbcb_shop'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', MYSQL_DATABASE),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
        'OPTIONS': {
            'ssl': {
                'ca': PROJECT_ROOT / 'ca.pem',
            },
        },
    },


    # SQLite dùng làm dữ liệu backup/local
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': PROJECT_ROOT / 'db.sqlite3',
    },
}

# =========================
# PASSWORD VALIDATION
# =========================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =========================
# LANGUAGE / TIME
# =========================

LANGUAGE_CODE = 'vi'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_TZ = True


# =========================
# STATIC FILES
# =========================
STATIC_URL = '/static/'
STATICFILES_DIRS = [PROJECT_ROOT / 'frontend' / 'static']
STATIC_ROOT = PROJECT_ROOT / 'staticfiles'


# =========================
# MEDIA FILES
# =========================

MEDIA_URL = '/media/'

MEDIA_ROOT = PROJECT_ROOT / 'media'


# =========================
# DEFAULT PRIMARY KEY
# =========================
LOGIN_URL = 'shop:login'
LOGIN_REDIRECT_URL = '/ho-so/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
