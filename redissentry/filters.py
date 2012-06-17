from traceback import format_exc
from datetime import datetime as dt, timedelta as td

from redissentrycore.filters  import Filter
from redissentrycore.utils import humanize, fallback

from .models import WhitelistRecord


class FilterWMainDb(Filter):
    db_record_ttl = 30*24*60      # a month
    log_message = 'auth rejected for whitelisted ip:username'

    def __init__(self, **kwargs):
        super(FilterWMainDb, self).__init__(**kwargs)
        self.counter = 'Wc:' + self.ip + ':' + self.username
        self.block   = 'Wb:' + self.ip + ':' + self.username

    def whitelist(self, user):
        try:
#            self.r.set(self.counter, 0)
#            self.r.expire(self.counter, self.counter_ttl * 60)
            self.r.delete(self.counter)
            self.r.delete(self.block)
            n = WhitelistRecord.objects.filter(ip=self.ip, user=user).update(
                    expire_date=dt.utcnow() + td(minutes=self.db_record_ttl))
            if n == 0:
                WhitelistRecord.objects.create(ip=self.ip, user=user, 
                    expire_date=dt.utcnow() + td(minutes=self.db_record_ttl))
            self.log('user whitelisted')
        except:
            self.logger.error(format_exc())
    
    def is_whitelisted(self):
        try:
#            return self.r.get(self.counter) is not None
            return self.r.exists(self.counter) or \
                   WhitelistRecord.objects.filter(ip=self.ip, user__username=self.username, 
                           expire_date__gt=dt.utcnow()).exists()
        except:
            self.logger.error(format_exc())

    def test(self):
        t, msg = super(FilterWMainDb, self).test()
        if t:
            zt, zmsg = self.rs().fzw.update()
        else:
            zt, zmsg = 0, ''
        return zt or t, zmsg or msg

    @fallback(0, '')
    def update(self):
        r = self.r
        n = r.incr(self.counter)
        log_msg = 'fa #%d from whitelisted ip:username' % n
        t = self.get_delay(n) * 60
        if t:
            if not r.exists(self.block):
                r.set(self.block, 1)
            r.expire(self.block, t)
            self.rs().store_history_record('ip:username', self.ip, self.username, n)
            log_msg += ', blocked for %d min' % (t/60)
            res = t, self.error_message % humanize(t)
        else:
            res = 0, ''
        r.expire(self.counter, self.get_counter_ttl(n) * 60 + t)
        self.log(log_msg + '; ttl = ' + str(td(minutes=self.get_counter_ttl(n))))
        return res
    








