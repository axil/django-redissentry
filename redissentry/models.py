from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User

if getattr(settings, 'RS_PRETTY_ADMIN_LABEL', False):
    class RedisSentryLabel(str):
        # dirty hack, use at your own risk
        def __new__(cls, *args, **kwargs):
            return str.__new__(cls, 'redissentry')
        def title(self):
            return 'Redis Sentry'
        def __conform__(self, *args, **kwargs):
            return self
        def getquoted(self):
            return "'redissentry'"
    app_label = RedisSentryLabel()
else:
    app_label = 'redissentry'

#class Whitelist(models.Model):
#    class Meta:
#        app_label = app_label
#        verbose_name_plural = 'Whitelist'

#class Blacklist(models.Model):
#    class Meta:
#        abstract = True
#        app_label = app_label
#        verbose_name_plural = 'Blacklist'

class Dashboard(models.Model):
    class Meta:
        app_label = app_label
        verbose_name_plural = 'Dashboard'

BLOCK_TYPES = (
    ('A', 'ip'),
    ('B', 'username'),
    ('W', 'ip:username'),
)


if getattr(settings, 'RS_SAVE_HISTORY', True):
    class BlocksHistoryRecord(models.Model):
        # Note that failed_attempts and blocked_attempts are not total numbers 
        # of the corresponding attempts encountered, but numbers that triggered 
        # the most recent block in the series
        block_type = models.CharField(choices = BLOCK_TYPES, max_length=1, null=True)
        ip = models.CharField(_('IP address'), max_length=2048, null=True, blank=True)
        username = models.CharField(max_length=255, null=True, blank=True)
        failed_attempts = models.IntegerField(null=True)
        blocked_attempts = models.IntegerField(null=True)
        last_segment_duration = models.IntegerField(default=0)
        created = models.DateTimeField(auto_now_add=True, db_index=True)
        updated = models.DateTimeField(auto_now=True, db_index=True)
        
        class Meta:
            app_label = app_label
            ordering = '-created',

        def get_ip(self):
            if self.block_type in ('A', 'W'):
                return self.ip
            else:
                return '..., ' + self.ip if self.ip else '(None)'
        get_ip.short_description = _('IP address')
        
        def get_username(self):
            if self.block_type in ('B', 'W'):
                return self.username
            else:
                return '..., ' + self.username if self.username else '(None)'
        get_username.short_description = _('Username')

class WhitelistRecord(models.Model):
    # stores successful login attempts
    # expired items need to be flushed via cron-job
    user = models.ForeignKey(User)
    ip = models.IPAddressField()
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    expire_date = models.DateTimeField(_('Expire date (UTC)'), db_index=True)

    class Meta:
        app_label = app_label
        ordering = '-created',
