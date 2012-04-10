from logging import getLogger
from traceback import format_exc

from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import string_concat
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from redissentry import RedisSentry
# from redissentry import RedisSentryLite as RedisSentry      # uncomment to use the lite version

from .middleware import get_request
from .models import BlocksHistoryRecord, BLOCK_TYPES

RS_DB = getattr(settings, 'REDIS_SENTRY_DB', 0)                                                     # redis db #
RS_ERROR_MSG = getattr(settings, 'REDIS_SENTRY_ERROR_MSG', _('Incorrect username or password.'))    # shown when the block has just been applied (every 5th failed attempt by default)
RS_ERROR_SEP = getattr(settings, 'REDIS_SENTRY_ERROR_SEP', ' ')                                     # eg '<br/>'

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

def protect(auth):
    if hasattr(auth, '__protected__'):
        return auth
    
    def wrapper(username=None, password=None, error_msg=RS_ERROR_MSG, error_sep=RS_ERROR_SEP):
        try:
            request = get_request()
            if request:
                # try to get the remote address from thread locals
                ip = request.META.get('REMOTE_ADDR', '')
            else:
                ip = ''

            rs = RedisSentry(ip, username, 
                    user_exists_callback_test if getattr(settings, 'REDIS_SENTRY_TEST', False) else user_exists_callback,
                    store_history_record if getattr(settings, 'REDIS_SENTRY_SAVE_HISTORY', True) else None,
                    RS_DB)
        except: # fallback for redis initialization error
            getLogger('redissentry').error(format_exc())
            return auth(username=username, password=password)
        
        msg = rs.ask()
        if msg != '':
            raise forms.ValidationError(mark_safe(msg))
        
        user = auth(username=username, password=password)
        
        msg = rs.inform(bool(user))

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
