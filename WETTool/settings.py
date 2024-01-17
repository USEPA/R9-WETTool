"""
Django settings for WETTool project.

Generated by 'django-admin startproject' using Django 3.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

from django.utils.log import DEFAULT_LOGGING

from . import local_settings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getattr(local_settings, 'SECRET_KEY', 'super_secret')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getattr(local_settings, 'DEBUG', False)

ALLOWED_HOSTS = getattr(local_settings, 'ALLOWED_HOSTS', [])

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'admin_reorder',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_dramatiq',
    'QuestionLibrary',
    'agol_oauth2',
    'social_django',
    'debug_toolbar',
    'corsheaders',
    'fieldsets_with_inlines',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'admin_reorder.middleware.ModelAdminReorder'
]

ROOT_URLCONF = 'WETTool.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

WSGI_APPLICATION = 'WETTool.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = getattr(local_settings, 'DATABASES', {})

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
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

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

XLS_FORM_TEMPLATE = 'survey123_template.xlsx'

SOCIAL_AUTH_AGOL_KEY = getattr(local_settings, 'SOCIAL_AUTH_AGOL_KEY', '')
SOCIAL_AUTH_AGOL_SECRET = getattr(local_settings, 'SOCIAL_AUTH_AGOL_SECRET', '')
SOCIAL_AUTH_AGOL_DOMAIN = 'epa.maps.arcgis.com'

SOCIAL_AUTH_PIPELINE = [  # Note: Sequence of functions matters here.
    'social_core.pipeline.social_auth.social_details',  # 0
    'social_core.pipeline.social_auth.social_uid',  # 1
    'social_core.pipeline.social_auth.auth_allowed',  # 2
    'social_core.pipeline.social_auth.social_user',  # 3
    'social_core.pipeline.user.get_username',  # 4
    'agol_oauth2.pipeline.associate_by_username',
    'social_core.pipeline.social_auth.associate_user',  # 6
    'social_core.pipeline.social_auth.load_extra_data',  # 7
    'social_core.pipeline.user.user_details',
]

AUTHENTICATION_BACKENDS = getattr(local_settings, 'AUTHENTICATION_BACKENDS', [])

INTERNAL_IPS = getattr(local_settings, 'INTERNAL_IPS', [])

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

URL_PREFIX = getattr(local_settings, 'URL_PREFIX', '')

LOGIN_REDIRECT_URL = f'/{URL_PREFIX}'
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/


STATIC_URL = f'/{URL_PREFIX}static/'

STATIC_ROOT = 'static'

CORS_ORIGIN_ALLOW_ALL = True  # If this is used then `CORS_ORIGIN_WHITELIST` will not have any effect
CORS_ALLOW_CREDENTIALS = True

ADMIN_REORDER = (
    # Keep original label and models
    'sites',
    {'app': 'auth', 'models': (
        'auth.Group',
        {'model': 'auth.User', 'label': 'Staff'},
    )},

    {'app': 'social_django', 'label': 'ArcGIS User Settings', 'models': (
        'social_django.Group',
        {'model': 'social_django.UserSocialAuth', 'label': 'ArcGIS User Authorization'},
        {'model': 'social_django.Association', 'label': 'Associations'},
        {'model': 'social_django.Nonce', 'label': 'Nonces'},
    )},
    {'app': 'QuestionLibrary', 'models': (
        {'model': 'QuestionLibrary.Media', 'label': 'Media'},
        {'model': 'QuestionLibrary.Category', 'label': 'Category'},
        {'model': 'QuestionLibrary.FacilityType', 'label': 'Facility Type'},
        {'model': 'QuestionLibrary.MasterQuestion', 'label': 'Question List'},
        {'model': 'QuestionLibrary.QuestionSet', 'label': 'Question Sets'},
        {'model': 'QuestionLibrary.Survey', 'label': 'Assessments'},
        {'model': 'QuestionLibrary.Dashboard', 'label': 'Dashboards'},
        {'model': 'QuestionLibrary.LookupGroup', 'label': 'Response Types'},
        {'model': 'QuestionLibrary.FeatureServiceResponse', 'label': 'Feature Service/Survey123 Field Mappings'},
    )},
)

USE_X_FORWARDED_HOST = getattr(local_settings, 'USE_X_FORWARDED_HOST', False)
LOGGING = DEFAULT_LOGGING
LOGGING['handlers']['slack'] = {
    'level': 'ERROR',
    'filters': ['require_debug_false'],
    'class': 'slack_logging.SlackExceptionHandler',
    'bot_token': getattr(local_settings, 'SLACK_BOT_TOKEN', ''),
    'channel_id': getattr(local_settings, 'SLACK_CHANNEL', '')
}
LOGGING['handlers']['file'] = {'level': 'ERROR',
                               'filters': ['require_debug_false'],
                               'class': 'logging.FileHandler',
                               'filename': os.path.join(BASE_DIR, 'error.log')}

LOGGING['handlers']['drama_file'] = {'level': 'INFO',
                                     'filters': ['require_debug_false'],
                                     'class': 'logging.FileHandler',
                                     'filename': os.path.join(BASE_DIR, 'drama.log')}
LOGGING['loggers']['django'] = {'handlers': ['console', 'slack', 'file'], 'level': 'INFO'}
LOGGING['loggers']['dramatiq'] = {'handlers': ['console', 'slack', 'drama_file'], 'level': 'INFO'}

DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.rabbitmq.RabbitmqBroker",
    "OPTIONS": {
        "url": "amqp://localhost:5672",
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Pipelines",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ]
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

TASK_RUNNER_AGOL_USER = getattr(local_settings, 'TASK_RUNNER_AGOL_USER', None)

CSRF_TRUSTED_ORIGINS = getattr(local_settings, 'CSRF_TRUSTED_ORIGINS', None)
