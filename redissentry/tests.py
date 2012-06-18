#!/usr/bin/env python
import warnings
warnings.filterwarnings('ignore')
from django.utils import unittest
#import os

try:
    from bs4 import BeautifulSoup as BS             # BeautifulSoup 4
except:
    from BeautifulSoup import BeautifulSoup as BS   # BeautifulSoup 3
from redis import Redis

from django.test.client import Client
from django.conf import settings


#LOGIN_URL = '/accounts/login/'
LOGIN_URL = '/'
LOGOUT_URL = '/logout/'

settings.RS_TEST_MODE = True         # <anybody>@example.com is registered
settings.RS_REDIS_DB = 1             # redis db #1 is used for testing to keep the default db #0 intact
settings.SAVE_HISTORY = False

r = Redis(db = settings.RS_REDIS_DB)
c = Client()

userCreated = False

class LoggedInException(Exception):
    pass

def login(username, password='ddd', ip='127.0.0.1'):
    response = c.post(LOGIN_URL, {'username': username, 'password': password}, REMOTE_ADDR=ip)
    res = None
    if response.status_code in (301, 302):
        print '(redirected)'
        raise LoggedInException()
    elif response.status_code != 200:
        print '(%d status code)' % response.status_code
    else:
        try:
            soup = BS(response.content)
            #z = soup.find('table', 'error').find('td')
            items = soup.find(attrs='errorlist').find('li')
            res = ' '.join(item.string for item in items)
            print res
        except:
            print '(no errors)'
    return res

def clean_whitelist():
    from redissentry.models import WhitelistRecord
    WhitelistRecord.objects.all().delete()

class TestBase(object):
    def setUp(self):
        r.flushdb()

    def assertAllowed(self, *args, **kwargs):
        res = login(*args, **kwargs)
        self.assertIsNotNone(res)
        self.assertTrue('Try again' not in res or 'Incorrect username or password' in res)
    
    def assertRejected(self, *args, **kwargs):
        res = login(*args, **kwargs)
        self.assertIsNotNone(res)
        self.assertTrue('Try again' in res)
    
    def assertAuthenticated(self, *args, **kwargs):
        self.assertRaises(LoggedInException, login, *args, **kwargs)
        c.get(LOGOUT_URL)

class Test(TestBase, unittest.TestCase):
    def testA(self):
        for i in xrange(5):
            self.assertAllowed('aaa@bbb.cc')
        for i in xrange(3):
            self.assertRejected('aaa@bbb.cc')
    
    def testA1(self):
        for i in xrange(0, 5):
            self.assertAllowed('aaa%s@bbb.cc' % i)
        for i in xrange(5, 8):
            self.assertRejected('aaa%s@bbb.cc' % i)
    
    def testAZ(self):
        for j in xrange(7):
            for i in xrange(5):
                self.assertAllowed('aaa@bbb.cc')
            self.assertRejected('aaa@bbb.cc')
            print '(time passes...)'
            r.delete('Ab:127.0.0.1')
    
    def testB(self):
        for i in xrange(1, 6):
            self.assertAllowed('aaa@example.com', ip = '127.0.0.%d' % i)
        for i in xrange(6, 9):
            self.assertRejected('aaa@example.com', ip = '127.0.0.%d' % i)

    def testB1(self):
        for i in xrange(1, 9):
            self.assertAllowed('aaa@example.org', ip = '127.0.0.%d' % i)

    def testB2(self):
        for i in xrange(3):
            self.assertAllowed('aaa@example.com', ip = '127.0.0.1')
        for i in xrange(2):
            self.assertAllowed('aaa@example.com', ip = '127.0.0.2')
        for i in xrange(2):
            self.assertRejected('aaa@example.com', ip = '127.0.0.2')
        for i in xrange(2):
            self.assertRejected('aaa@example.com', ip = '127.0.0.1')

    def testBZ(self):
        for j in xrange(7):
            for i in xrange(5):
                self.assertAllowed('aaa@example.com', ip='127.0.0.%d' % (j*6+i))
            self.assertRejected('aaa@example.com', ip='127.0.0.%d' % (j*6+5))
            print '(time passes...)'
            r.delete('Bb:aaa@example.com')

class WhitelistTest(TestBase, unittest.TestCase):

    def setUp(self):
        global userCreated
        super(WhitelistTest, self).setUp()
        if not userCreated:
            from django.contrib.auth.models import User
            self.assertEqual(User.objects.count(), 0)   # this code should be run against a blank test database!
            user = User(username='existing@example.com', is_active=True)
            user.set_password('qwerty')
            user.save()
            userCreated = True

    def testW(self):
        self.assertAuthenticated('existing@example.com', 'qwerty')
        for i in xrange(5):
            self.assertAllowed('aaa@bbb.cc')
        self.assertRejected('aaa@bbb.cc')
        self.assertAllowed('existing@example.com')
        clean_whitelist()
    
    def testW1(self):
        for i in xrange(4):
            self.assertAllowed('existing@example.com')
        self.assertAuthenticated('existing@example.com', 'qwerty')
        self.assertAllowed('aaa@bbb.cc')
        self.assertRejected('aaa@bbb.cc')
        clean_whitelist()
    
    def testW2(self):
        self.assertAuthenticated('existing@example.com', 'qwerty')
        for i in xrange(5):
            self.assertAllowed('existing@example.com')
        self.assertRejected('existing@example.com')
        clean_whitelist()

    def testW3(self):
        self.assertAuthenticated('existing@example.com', 'qwerty')
        for i in xrange(4):
            self.assertAllowed('aaa@bbb.com')
        for i in xrange(7):
            self.assertAuthenticated('existing@example.com', 'qwerty', ip='127.0.0.%d' % (2+i))
        self.assertAllowed('existing@example.com')
        self.assertRejected('existing@example.com')
        clean_whitelist()

if __name__ == '__main__':
    if getattr(settings, 'RS_TEST_WHITELIST_AS_WELL', False):
        unittest.main(verbosity=2)
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(Test)
        unittest.TextTestRunner(verbosity=2).run(suite)
        print '\nWarning: to speed things up whitelist testing was skipped (so that only test redis db is used). '\
              'Run \'./manage.py test redissentry\' to go through all tests (test main database will be used as well).'
