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

REDIS_SENTRY_DB = n if you want to use Redis db number n instead of the default 0


