from logging import getLogger
from traceback import format_exc

from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import string_concat
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from redissentrycore import RedisSentry
from redissentrycore.utils import fallback
# from redissentrycore import RedisSentryLite as RedisSentry      # uncomment to use the lite version

from .middleware import get_request
from .models import BlocksHistoryRecord, BLOCK_TYPES
from .filters import FilterWMainDb

FA_PER_IP       = getattr(settings, 'RS_FA_PER_IP', 5)                                    # block ip after every N failed attempts
FA_PER_USERNAME = getattr(settings, 'RS_FA_PER_USERNAME', 5)                              # block username after every N failed attempts
REDIS_HOST      = getattr(settings,'RS_REDIS_HOST', 'localhost')
REDIS_PORT      = getattr(settings,'RS_REDIS_PORT', 6379)
REDIS_PASSWORD  = getattr(settings,'RS_REDIS_PASSWORD', '')
REDIS_DB        = lambda:getattr(settings, 'RS_REDIS_DB', 0)                              # redis db number; lambda is necessary for the tests

ERROR_MSG       = getattr(settings, 'RS_ERROR_MSG', _('Incorrect username or password.')) # shown when the block has just been applied (every 5th failed attempt by default)
ERROR_SEP       = getattr(settings, 'RS_ERROR_SEP', ' ')                                  # eg '<br/>'
TEST_MODE       = lambda:getattr(settings, 'RS_TEST_MODE', False)                         # used in testing suite
SAVE_HISTORY    = getattr(settings, 'RS_SAVE_HISTORY', True)                              # store events in a table from the main db

def user_exists_callback(username):
    return User.objects.filter(username=username).exists()

def user_exists_callback_test(username):
    return username.endswith('@example.com')

REV_BLOCK_TYPES = dict((v,k) for k,v in BLOCK_TYPES)

def store_history_record(block_type, ip, username, failed_attempts=None, blocked_attempts=None):
    def update_record(r):
        if failed_attempts:
            if r.failed_attempts < failed_attempts:
                r.failed_attempts = failed_attempts
            else:
                return None
        if blocked_attempts:
            if r.blocked_attempts < blocked_attempts:
                r.blocked_attempts = blocked_attempts
            else:
                return None
        r.save()
        return r

    try:
        kwargs = {}
        if 'ip' in block_type:
            kwargs['ip'] = ip
        if 'username' in block_type:
            kwargs['username'] = username
        r = None
        try:
            r = BlocksHistoryRecord.objects.filter(block_type=REV_BLOCK_TYPES[block_type], **kwargs).order_by('-created')[0]
            r = update_record(r)
        except:
            pass
        if r is None:
            kwargs['failed_attempts'] = failed_attempts
            kwargs['blocked_attempts'] = blocked_attempts
            r = BlocksHistoryRecord.objects.create(block_type=REV_BLOCK_TYPES[block_type], ip=ip, username=username,
                    failed_attempts=failed_attempts, blocked_attempts=blocked_attempts)
    except:
        pass

class RedisSentryWMD(RedisSentry):
    # uses main db for storing the whitelist
    FW = FilterWMainDb

    def whitelist(self, user):
        self.fw.whitelist(user)

    @fallback('')
    def inform(self, user):
        if user is not None:
            self.whitelist(user)
            res = 0, ''
        else:
            if self.whitelisted:
                res = self.fw.update()
            else:
                res = max(self.fa.update(), self.fb.update())
        return res[1]
            

def protect(auth):
    if hasattr(auth, '__protected__'):
        return auth
    
    def wrapper(username=None, password=None, error_msg=ERROR_MSG, error_sep=ERROR_SEP):
        try:
            request = get_request()
            if request:
                # try to get the remote address from thread locals
                ip = request.META.get('REMOTE_ADDR', '')
            else:
                ip = ''

            rs = RedisSentryWMD(ip, username, 
                    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB(),
                    store_history_record if SAVE_HISTORY else None,
                    user_exists_callback_test if TEST_MODE else user_exists_callback)
            rs.fa.period = FA_PER_IP
            rs.fb.period = FA_PER_USERNAME
        except: # fallback for redis initialization error
            getLogger('redissentry').error(format_exc())
            return auth(username=username, password=password)
        
        msg = rs.ask()
        if msg != '':
            raise forms.ValidationError(mark_safe(msg))
        
        user = auth(username=username, password=password)
        
        msg = rs.inform(user)

        if user is None and error_msg is not None and msg:
            raise forms.ValidationError(mark_safe(string_concat(error_msg, error_sep, msg)))
        return user
    
    wrapper.__protected__ = True
    return wrapper

def log_email(func):
    if hasattr(func, '__email_logged__'):
        return func

    def wrapper(request, *args, **kwargs):
        email = request.POST.get('email', '')
        if email:
            from logging import getLogger
            getLogger('redissentry').info('%-15s %-24s %s' % (request.META.get('REMOTE_ADDR', ''), email, 'password reset initiated'))
        return func(request, *args, **kwargs)

    wrapper.__email_logged__ = True
    return wrapper
