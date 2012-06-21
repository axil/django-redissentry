#!/usr/bin/env python

from distutils.core import setup

setup(name='django-redissentry',
      version='0.2.0',
      description='Django app based on RedisSentry (redissentry-core) protecting against password attacks',
      long_description=open('README.rst').read(),
      author='Lev Maximov',
      author_email='lev.maximov@gmail.com',
      url='http://github.com/axil/django-redissentry',
      packages=['redissentry', 'redissentry.migrations'],
      include_package_data=True,
      install_requires=['redissentry-core>=0.2.0'],
#      dependency_links=['https://github.com/axil/redissentry-core/tarball/master#egg=redissentry-core-0.1.0'],
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
