==================
RedisSentry-Django
==================

Installation
------------

settings.py::

    MIDDLEWARE_CLASSES += (
        'redissentry.django.middleware.RequestMiddleware',
    )

    INSTALLED_APPS += (
        'redissentry.django',
    )


Finetuning (Django)
------------------

settings.py::

    RS_REDIS_HOST = 'localhost'
    RS_REDIS_PORT = 6379
    RS_REDIS_PASSWORD = ''
    RS_REDIS_DB = 0

    FA_PER_IP = 5         # block ip after every N failed attempts
    FA_PER_USERNAME = 5   # block username after every N failed attempts
