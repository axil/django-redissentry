#!/usr/bin/env python

from distutils.core import setup

setup(name='redis-sentry-django',
      version='0.1.0',
      description='Django app based on RedisSentry protecting against password bruteforce attacks',
      long_description=open('README.rst').read(),
      author='Lev Maximov',
      author_email='lev.maximov@gmail.com',
      url='http://github.com/axil/django-redissentry',
      packages=['redissentry', 'redissentry.migrations'],
      include_package_data=True,
      install_requires=['redis-sentry-core>=0.1.0'],
      dependency_links=['https://github.com/axil/redis-sentry-core/tarball/master#egg=redis-sentry-core-0.1.0'],
      classifiers = [
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Security',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: User Interfaces',
      ],
     )
