#!/usr/bin/env python
from time import sleep
import warnings
warnings.filterwarnings('ignore')

from bs4 import BeautifulSoup as BS
from redis import Redis

from django.test.client import Client
from django.conf import settings


LOGIN_URL = '/accounts/login/'

settings.REDIS_SENTRY_TEST = True        # <anybody>@example.com is registered
settings.REDIS_SENTRY_DB = 0             # redis db #1 is used for testing to keep default #0 intact

r = Redis(db = settings.REDIS_SENTRY_DB)
r.flushdb()
c = Client()

def test(username, password='ddd', ip='127.0.0.1'):
    response = c.post(LOGIN_URL, {'username': username, 'password': password}, REMOTE_ADDR=ip)
    if response.status_code in (301, 302):
        print '(redirected)'
    elif response.status_code != 200:
        print '(%d status code)' % response.status_code
    else:
        try:
            soup = BS(response.content)
            z = soup.find('table', 'error').find('td')
            print ' '.join(z.strings)
        except:
            print '(no errors)'

def testA():
    for j in xrange(7):
        for i in xrange(6):
            test('aaa@bbb.cc')
        print '...'
        sleep(1)
        r.delete('Ab:127.0.0.1')

def testAZ():
    for i in xrange(32):
        test('aaa@bbb.cc')

def testB():
    for i in xrange(10):
        test('aaa@example.com', ip = '127.0.0.%d' % i)

def testB1():
    for i in xrange(3):
        test('aaa@example.com', ip = '127.0.0.1')
    for i in xrange(7):
        test('aaa@example.com', ip = '127.0.0.2')

def testBZ():
    testB1()
    for i in xrange(20):
        test('aaa@example.com', ip = '127.0.0.1')

def testW():
    test('existing@example.com')
    test('existing@example.com', 'qwerty')
    for i in xrange(7):
        test('aaa@bbb.cc')
    for i in xrange(7):
        test('existing@example.com')

def testWZ():
    testW()
    for i in xrange(50):
        test('existing@example.com')

if __name__ == '__main__':
    import timeit
#    print timeit.Timer('testA()', 'from __main__ import *').timeit(number=1)
#    print timeit.Timer('testAZ()', 'from __main__ import *').timeit(number=1)
    print timeit.Timer('testB()', 'from __main__ import *').timeit(number=1)
#    print timeit.Timer('testB1()', 'from __main__ import *').timeit(number=1)
#    print timeit.Timer('testBZ()', 'from __main__ import *').timeit(number=1)
#    print timeit.Timer('testW()', 'from __main__ import *').timeit(number=1)
#    print timeit.Timer('testWZ()', 'from __main__ import *').timeit(number=1)
