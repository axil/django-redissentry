import logging
from datetime import datetime as dt, timedelta as td            ##
from traceback import format_exc
from random import uniform, random
from struct import pack
from math import log

import redis

COUNTER_TTL = { # in minutes
    'A': 60,
    'B': 60,
    'C': 5,
    'Ze': 5,
    'Zi': 24*60,
    'W': 30*24*60,
}

# quantity of allowed failed attempts in a series;
# = number of attempt in the series when some measure is taken

PERIOD = {
    'A': 5,
    'B': 3,
    'C': 50,
    'Ze': 10,
    'Zi': 5,
}

# get_delay functions: 
# after n attempts block for t minutes; 
# negative t hides remaining time: 'try later'

DELAY = {
    1: 5,
    2: 10,
    3: 30,
    4: 60,
#   5,6...: -5 hours..-23 hours
}

def exprand(a, b):
    return int(a + log(random()) * (b - a))

def get_delayAW(n):
    """
    for filters A,B,W
    >>> get_delayAW(0)
    0
    >>> get_delayAW(1)
    0
    >>> get_delayAW(5)
    5
    >>> get_delayAW(9)
    0
    >>> get_delayAW(10)
    10
    >>> get_delayAW(15)
    30
    """
    N = PERIOD['A']
    if n==0 or n % N != 0:
        return 0
    else:
        return DELAY.get(n//N, -uniform(5*60, 7*24*60))

def get_delayB(n):
    if n < PERIOD['B']:
        return 0
    else:
        return 60

DELAY_C = {
    1: 1,
    2: 2,
#   3,4,...: uniform(3..5)
}

def get_delayC(n):
    """
    >>> get_delayC(0)
    0
    >>> get_delayC(1)
    0
    >>> get_delayC(50)
    1
    >>> get_delayC(52)
    0
    >>> get_delayC(100)
    2
    >>> get_delayC(105)
    0
    """
    N = PERIOD['C']
    if n==0 or n % N != 0:
        return 0
    else:
        return DELAY_C.get(n//N, uniform(3, 5))
C_LOGGING_THRESHOLD = 40

def get_delayZ(n, is_explicit):
    if is_explicit:
        if n % PERIOD['Ze']:
            return 0
        elif n == PERIOD['Ze']:
            return 60
        else:
            return -exprand(3*60, 23*60)
    else:
        if n % PERIOD['Zi']:
            return 0
        else:
            return -exprand(3*60, 23*60)

MSG_A = 'Too many failed attempts. Try again %s'
MSG_B = 'Too many failed attempts. Try again %s'
MSG_C = 'You cannot login right now. Try again %s'

def humanize(t):
    """
    >>> print humanize(0)
    now
    >>> print humanize(1)
    in a minute
    >>> print humanize(60)
    in a minute
    >>> print humanize(61)
    in 2 minutes
    >>> print humanize(3600)
    in an hour
    >>> print humanize(3601)
    in 2 hours
    """
    m, s = divmod(t, 60)
    if s:
        m += 1                 # ceil minutes 
    h, m = divmod(m, 60)
    if m and h:
        h += 1                 # ceil hours
    d, h = divmod(h, 24)

    if h > 1:
        res = 'in %d hours' % h
    elif h == 1:
        res = 'in an hour'
    else:
        if m > 1:
            res = 'in %d minutes' % m
        elif m == 1:
            res = 'in a minute'
        else:
            res = 'now'
    return res

class RedisSentryBase(object):
    def __init__(self, ip, username, is_staff_callback = lambda x: False):
        self.ip = ip
        self.username = username
        self.is_staff_callback = is_staff_callback

        self.r = redis.Redis()
        self.logger = logging.getLogger('redissentry')
        self.counter_ttl = COUNTER_TTL
        self.is_staff = None

        self.Acounter = 'Ac:' + ip
        self.Ablock   = 'Ab:' + ip
        self.Bcounter = 'Bc:' + username
        self.Bblock   = 'Bb:' + username
        self.Ccounter = 'Cc'
        self.Cblock   = 'Cb'
        self.Wcounter = 'Wc:' + ip + ':' + username
        self.Wblock   = 'Wb:' + ip + ':' + username
        self.Zcounter = 'Zc:' + ip
#        self.Zblock   = 'Zb:' + ip     # Ablock is used

    def __del__(self):
        try:
            del self.r
            self.logger.handlers[0].close()
        except:
            pass

    # overload if necessary:
    def get_delayA(self, n):  return get_delayAW(n)
    def get_delayB(self, n):  return get_delayB(n)
    def get_delayC(self, n):  return get_delayC(n)
    def get_delayW(self, n):  return get_delayAW(n)
    def get_delayZ(self, n, is_explicit):  return get_delayZ(n, is_explicit)
    def humanize(self, n): return humanize(n)
    c_logging_threshold = C_LOGGING_THRESHOLD
    msg_a = MSG_A
    msg_b = MSG_B
    msg_c = MSG_C

    def testABC(self):
        try:
            r = (self.testA(), self.testB(), self.testC())
            m = max(r)
            return m[2], m[1]
        except:
            self.logger.error(format_exc())

    def updateABC(self):
        res = (self.updateA(), self.updateB(), self.updateC())
        return max(res)[1]

    def log(self, msg):
        self.logger.info('%-15s %-21s ' % (self.ip, self.username[:21]) + msg)
    
    def debug(self, msg):
        self.logger.debug('%-15s %-21s ' % (self.ip, self.username[:21]) + msg)

    def cached_is_staff(self, username):
        if self.is_staff is None:
            self.is_staff = self.is_staff_callback(username)
        return self.is_staff

    def testA(self):
        try:
            r = self.r
            t = r.ttl(self.Ablock)
            if t:
                b = int(r.get(self.Ablock))
                self.log('auth rejected from ip, %s sec left' % t + (' (hidden)' if not b else ''))
                return t, b, self.msg_a % (humanize(t) if b else 'later')
            else:
                return t, 1, ''
        except:
            self.logger.error(format_exc())

    def testB(self):
        try:
            r = self.r
            t = r.ttl(self.Bblock)
            if t:
                b = int(r.get(self.Bblock))
                self.log('auth rejected for username, %s sec left' % t + (' (hidden)' if not b else ''))
                return t, b, self.msg_b % (humanize(t) if b else 'later')
            else:
                return t, 1, ''
        except:
            self.logger.error(format_exc())

    def testC(self):
        try:
            r = self.r
            t = r.ttl(self.Cblock)
            if t:
                b = int(r.get(self.Cblock))
                self.log('auth rejected due to global block, %s sec left' % t + (' (hidden)' if not b else ''))
                return t, b, self.msg_c % (humanize(t) if b else 'later')
            else:
                return t, 1, ''
        except:
            self.logger.error(format_exc())
    
#   no testZ(self) because it shares block flag with filter A

    def updateA(self):
        res = 0, ''
        try:
            r = self.r
            n = r.incr(self.Acounter)
            r.expire(self.Acounter, self.counter_ttl['A'] * 60)
            log_msg = 'fa #%d from regular ip' % n
            t = self.get_delayA(n) * 60
            if t:
                r.set(self.Ablock, int(t>0))
                r.expire(self.Ablock, abs(t))
                log_msg += ', ip blocked for %d min' % (t/60)
                res = abs(t), 'Too many failed attempts. Try again %s' % (humanize(t) if t>0 else 'later')
            self.log(log_msg)
        except:
            self.logger.error(format_exc())
        return res

    def updateB(self):
        res = 0, ''
        try:
            r = self.r
            n = r.scard(self.Bcounter)
            if n or self.cached_is_staff(self.username):
                packed_ip = pack('4B', *map(int, self.ip.split('.')))
                added = r.sadd(self.Bcounter, packed_ip)
                r.expire(self.Bcounter, self.counter_ttl['B'] * 60)
                if added:
                    n += added
                    log_msg = 'fa from ip #%d with same username' % n
                    t = self.get_delayB(n) * 60
                    if t:
                        r.set(self.Bblock, int(t>0))
                        r.expire(self.Bblock, abs(t))
                        log_msg += ', username blocked for %d min ' % abs(t/60) + 'explicitly' if t>0 else 'implicitly'
                        res = abs(t), self.msg_b % (humanize(t) if t>0 else 'later')
                        r.delete(self.Bcounter)
                    if n > 1 or t:
                        self.log(log_msg)
            else:
                self.log('fa with non-staff username - not storing')
        except:
            self.logger.error(format_exc())
        return res

    def updateC(self):
        res = 0, ''
        try:
            r = self.r
            if self.cached_is_staff(self.username):                     # otherwise it could be triggered by a number of specially registered fake user accounts
                n = r.incr(self.Ccounter)
                r.expire(self.Ccounter, self.counter_ttl['C'] * 60)
                log_msg = 'fa #%d of a distributed attack' % n
                t = self.get_delayC(n) * 60
                if t:
                    r.set(self.Cblock, int(t>0))
                    r.expire(self.Cblock, abs(t))
                    log_msg += ', global block for %d min' % (t/60)
                    res = abs(t), self.msg_c % (humanize(t) if t>0 else 'later')
                if n > self.c_logging_threshold or t:
                    self.log(log_msg)
        except:
            self.logger.error(format_exc())
        return res

    def whitelist(self):
        try:
            self.r.set(self.Wcounter, 0)
            self.log('user whitelisted')
        except:
            self.logger.error(format_exc())
    
    def is_whitelisted(self):
        try:
            return self.r.get(self.Wcounter) is not None
        except:
            self.logger.error(format_exc())
    
    def testW(self):
        try:
            t = self.r.ttl(self.Wblock)
            if t:
                self.log('whitelisted auth rejected, %s sec left' % t)
                return 'Too many failed attempts. Try again %s' % (humanize(t) if t>0 else 'later'), t>0
            else:
                return '', 1
        except:
            self.logger.error(format_exc())

    def updateW(self):
        res = ''
        try:
            if self.is_staff_callback(self.username):   # minimize number of items with high ttl to be kept in memory 
                r = self.r
                n = r.incr(self.Wcounter)
                r.expire(self.Wcounter, self.counter_ttl['W'] * 60)
                msg = 'fa #%d from whitelisted ip:username' % n
                t = self.get_delayW(n) * 60
                if t:
                    r.set(self.Wblock, int(t>0))
                    r.expire(self.Wblock, abs(t))
                    msg += ', blocked for %d min' % (t/60)
                    res = self.msg_a % (humanize(t) if t>0 else 'later')
                self.log(msg)
        except:
            self.logger.error(format_exc())
        return res

    def updateZ(self, is_explicit):
        res = ''
        try:
            r = self.r
            n = r.incr(self.Zcounter)
            r.expire(self.Zcounter, self.counter_ttl['Ze' if is_explicit else 'Zi'] * 60)
            log_msg = 'fa #%d from blocked ip' % n
            t = self.get_delayZ(n, is_explicit) * 60
            if t > r.ttl(self.Ablock):
                r.set(self.Ablock, int(t>0))
                r.expire(self.Ablock, abs(t))
                log_msg += ', ip blocked for %d min ' % abs(t/60) + ('explicitly' if t>0 else 'implicitly')
                res = self.msg_a % (humanize(t) if t>0 else 'later')
            self.log(log_msg)
        except:
            self.logger.error(format_exc())
        return res

    
class RedisSentryBasic(RedisSentryBase):
    def ask(self):
        return self.testA()[-1]

    def inform(self, result):
        return self.updateA()[-1]

class RedisSentry(RedisSentryBase):
#   version without filterZ
#
#   def ask(self):
#        self.whitelisted = self.is_whitelisted()
#        if self.whitelisted:
#            msg = self.testW()[0]
#        else:
#            msg = self.testABC()[0]
#        return msg
    
    def ask(self):
        self.whitelisted = self.is_whitelisted()
        if self.whitelisted:
            msg, is_explicit = self.testW()
        else:
            msg, is_explicit = self.testABC()
        if msg:
            msg = self.updateZ(is_explicit) or msg
        return msg
    

    def inform(self, result):
        if result:
            self.whitelist()
            res = None
        else:
            if self.whitelisted:
                res = self.updateW()
            else:
                res = self.updateABC()
        return res


def usage_example1():
    from django import forms

    sentry = RedisSentry(ip, username)   ##
    msg = sentry.ask()
    if msg:
        raise forms.ValidationError(msg)
    res = auth()            ##
    sentry.inform(res)

def usage_example2(error_msg):
    from django import forms

    sentry = RedisSentry(ip, username)   ##
    msg = sentry.ask()
    if msg:
        raise forms.ValidationError(msg)
    res = auth()            ##
    msg = sentry.inform(res)
    if msg:
        raise forms.ValidationError(error_msg + ' ' + msg)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
