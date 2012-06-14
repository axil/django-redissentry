===========
RedisSentry
===========

This is django specific app for RedisSentry. For generic package,
(which this app is dependent on) see redissentry-core.

Installation
------------

settings.py::

    MIDDLEWARE_CLASSES += (
        'redissentry.middleware.RequestMiddleware',
    )

    INSTALLED_APPS += (
        'redissentry',
    )


Finetuning
----------

settings.py::

    RS_REDIS_HOST = 'localhost'
    RS_REDIS_PORT = 6379
    RS_REDIS_PASSWORD = ''
    RS_REDIS_DB = 0

    RS_FA_PER_IP = 5         # block ip after every N failed attempts
    RS_FA_PER_USERNAME = 5   # block username after every N failed attempts

Also the class structure is designed in such a way as to facilitate further finetuning 
through inheritance.
