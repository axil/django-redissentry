===========
RedisSentry
===========

Installation
------------

settings.py::

    MIDDLEWARE_CLASSES += (
        'redissentry.middleware.RequestMiddleware',
    )

    INSTALLED_APPS += (
        'redissentry',
    )


Finetuning (Django)
------------------

REDIS_SENTRY_DB = n if you want to use Redis db number n instead of the default 0

