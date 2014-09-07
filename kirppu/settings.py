# Django settings for kirppu project.
import os.path
from django.utils.translation import ugettext_lazy as _

BASE = os.path.dirname(os.path.abspath(__file__))
_path = lambda path: os.path.normpath(os.path.join(BASE, '..', path))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': _path('db.sqlite'),                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Helsinki'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fi'

LANGUAGES = (
    ('fi', _("Finnish")),
    ('en', _("English")),
)

LOCALE_PATHS = (
    _path("locale"),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = _path('static/')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '=#j)-ml7x@a2iw9=#l7%i89l%cry6kch6x49=0%vcasq!!@97-'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    #'kompassi_crowd.middleware.KompassiCrowdAuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    #'kompassi_crowd.backends.KompassiCrowdAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'kirppu.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'kirppu.wsgi.application'

import os
TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), '..', 'templates').replace('\\','/'),)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'kirppu.kirppuauth',
    'kirppu.app',
    'pipeline',
)

AUTH_USER_MODEL = 'kirppuauth.User'


PIPELINE_CSS = {
    'general': {
        "source_filenames": (
            "css/general.css",
            "css/bootstrap.css",
            "css/bootstrap-theme.css",
        ),
        "output_filename": "styles.css",
    },
    'vendor': {
        "source_filenames": (
            "css/app.css",
        ),
        "output_filename": "vendor.css",
    },
    'price_tags': {
        "source_filenames": (
            "css/price_tags.css",
        ),
        "output_filename": "price_tags.css",
    },
    'checkout': {
        "source_filenames": (
            "css/checkout.css",
        ),
        "output_filename": "checkout.css",
    }
}
PIPELINE_JS = {
    'general': {
        "source_filenames": (
            "js/jquery-1.10.2.js",
            "js/bootstrap.js",
            "js/csrf.coffee",
        ),
        "output_filename": "general.js",
    },
    'price_tags': {
        "source_filenames": (
            "js/number_test.coffee",
            "js/price_tags.coffee",
        ),
        "output_filename": "price_tags.js",
    },
    'checkout': {
        "source_filenames": (
            "js/checkout/util.coffee",
            "js/checkout/checkout.coffee",
            "js/checkout/datetime_formatter.coffee",
            "js/checkout/dialog.coffee",

            "js/checkout/resulttable.coffee",
            "js/checkout/itemreceipttable.coffee",
            "js/checkout/itemreporttable.coffee",
            "js/checkout/vendorlist.coffee",
            "js/checkout/vendorinfo.coffee",
            "js/checkout/receiptsum.coffee",
            "js/checkout/printreceipttable.coffee",

            "js/checkout/modeswitcher.coffee",
            "js/checkout/checkoutmode.coffee",
            "js/checkout/itemcheckoutmode.coffee",

            "js/checkout/countervalidationmode.coffee",
            "js/checkout/clerkloginmode.coffee",
            "js/checkout/itemcheckinmode.coffee",
            "js/checkout/vendorcheckoutmode.coffee",
            "js/checkout/countermode.coffee",
            "js/checkout/receiptprintmode.coffee",
            "js/checkout/vendorcompensation.coffee",
            "js/checkout/vendorreport.coffee",
            "js/checkout/vendorfindmode.coffee",
            "js/checkout/statusmode.coffee",

            "js/jquery.flot.js",
            "js/jquery.flot.time.js",

            "js/number_test.coffee",
            "js/jquery.cookie-1.4.1-0.js",
        ),
        "output_filename": "cout.js",
    },
    'jeditable': {
        "source_filenames": (
            "js/jquery.jeditable.js",
        ),
        "output_filename": "jeditable.js"
    },
}

PIPELINE_COMPILERS = (
    'pipeline.compilers.stylus.StylusCompiler',
    'pipeline.compilers.coffee.CoffeeScriptCompiler',
)
PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': True
        },
        'kompassi_crowd': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': True
        },
    },
}

# Mapping from Kompassi user fields to Kirppu user fields.
KOMPASSI_USER_MAP = [
#   (u'birth_date'  ,               ),
#   (u'display_name',               ),
    (u'email'       , 'email'       ),
    (u'first_name'  , 'first_name'  ),
#   (u'full_name'   ,               ),
#   (u'groups'      ,               ),
#   (u'nick'        ,               ),
    (u'phone'       , 'phone'       ),
    (u'surname'     , 'last_name'   ),
    (u'username'    , 'username'    ),
]

KOMPASSI_CROWD_URL = 'https://crowd.tracon.fi/crowd'
KOMPASSI_CROWD_APPLICATION_NAME = 'kirppu'
KOMPASSI_CROWD_APPLICATION_PASSWORD = 'fill me in'
KOMPASSI_CROWD_SESSION_URL = '{KOMPASSI_CROWD_URL}/rest/usermanagement/1/session'.format(**locals())
KOMPASSI_CROWD_COOKIE_NAME = 'crowd.token_key'
KOMPASSI_CROWD_VALIDATION_FACTORS = {
    'remote_address': lambda request: '127.0.0.1',
    'X-Forwarded-For': lambda request: request.META['HTTP_X_FORWARDED_FOR'],
}
KOMPASSI_API_URL = 'https://kompassidev.tracon.fi/api/v1'
KOMPASSI_API_APPLICATION_NAME = KOMPASSI_CROWD_APPLICATION_NAME
KOMPASSI_API_APPLICATION_PASSWORD = KOMPASSI_CROWD_APPLICATION_PASSWORD

LOGIN_URL = 'https://kompassidev.tracon.fi/crowd'
LOGOUT_URL = 'https://kompassidev.tracon.fi/logout'
PROFILE_URL = 'https://kompassidev.tracon.fi/profile'

KIRPPU_CHECKOUT_ACTIVE = False

KIRPPU_COPY_ITEM_WHEN_UNPRINTED = False
KIRPPU_MAX_ITEMS_PER_VENDOR = 1000

# Datetime of the instant of which Item registration is open until, in "YYYY-MM-DD HH:MM:SS" format.
# The specified date is expected to be in TIME_ZONE timezone.
KIRPPU_REGISTER_ACTIVE_UNTIL = "2024-12-31 23:59:59"

# Load local settings that are not stored in repository. This must be last at end of settings.
try:
    from local_settings import *
except ImportError:
    pass
