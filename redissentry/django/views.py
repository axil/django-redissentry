import logging
from datetime import timedelta as td
from urllib import unquote
from struct import unpack

from redis import Redis

from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse

REDISSENTRY_DB = getattr(settings,'REDISSENTRY_DB', 0)
LAST_LOG_LINES = getattr(settings, 'LAST_LOG_LINES', 100)

def get_ttl(r, k):
    return str(td(seconds=r.ttl(k)))
    
def get_redis():
    return Redis(db = REDISSENTRY_DB)

def show_whitelist(request):
    r = get_redis()
    whitelist = [k.split(':')[1:] + [r.get(k)] + [get_ttl(r, k)] for k in r.keys('Wc:*')]
    return direct_to_template(request, 'redissentry/whitelist.html', {
        'title': 'Redis Sentry Whitelist',
        'whitelist': whitelist,
    })

def show_blacklist(request):
    r = get_redis()
    blacklistA = [(k.split(':')[1], get_ttl(r, k)) for k in r.keys('Ab:*')]
    blacklistB = [(k.split(':')[1], get_ttl(r, k)) for k in r.keys('Bb:*')]
    blacklistW = [k.split(':')[1:] + [get_ttl(r,k)] for k in r.keys('Wb:*')]
    return direct_to_template(request, 'redissentry/blacklist.html', {
        'title': 'Redis Sentry Blacklist',
        'blacklistA': blacklistA,
        'blacklistB': blacklistB,
        'blacklistW': blacklistW,
    })

def show_dashboard(request):
    r = get_redis()
    countersA  = [(k.split(':')[1], r.get(k), get_ttl(r, k)) for k in r.keys('Ac:*')]
    countersB  = [(
        k.split(':')[1], 
        [('.'.join(map(str, unpack('4B', ip))), int(n)) for ip, n in r.zrange(k, 0, -1, withscores=True)], 
        get_ttl(r, k)) 
            for k in r.keys('Bc:*')
    ]
    countersW = filter(lambda x: x[2]!='0', [k.split(':')[1:] + [r.get(k), get_ttl(r,k)] for k in r.keys('Wc:*')])
    
    blacklistA = [(ip, abs(v)-1, ttl if v>0 else '(%s)' % ttl) for ip, v, ttl in [(k.split(':')[1], int(r.get(k)), get_ttl(r, k)) for k in r.keys('Ab:*')]]
    blacklistB = [(un, abs(v)-1, ttl if v>0 else '(%s)' % ttl) for un, v, ttl in [(k.split(':')[1], int(r.get(k)), get_ttl(r, k)) for k in r.keys('Bb:*')]]
    blacklistW = [(ip, un, abs(v)-1, ttl if v>0 else '(%s)' % ttl) for ip, un, v, ttl in [k.split(':')[1:] + [int(r.get(k)), get_ttl(r,k)] for k in r.keys('Wb:*')]]
    
    log = ''
    try:
        filename = logging.getLogger('redissentry').handlers[0].baseFilename
        log = open(filename).readlines()[-LAST_LOG_LINES:]
        n = len(log)
        if n < LAST_LOG_LINES:
            log = open(filename + '.1').readlines()[-LAST_LOG_LINES+n:] + log
    except:
        pass

    return direct_to_template(request, 'redissentry/dashboard.html', {
        'title': 'Redis Sentry Dashboard',
        'countersA': countersA,
        'countersB': countersB,
        'countersW': countersW,
        'blacklistA': blacklistA,
        'blacklistB': blacklistB,
        'blacklistW': blacklistW,
        'log': ''.join(log),
    })

def remove_from_whitelist(request):
    get_redis().delete(':'.join(('Wc', request.GET.get('ip', ''), request.GET.get('username'))))
    return HttpResponseRedirect(reverse('admin:redissentry_whitelist_changelist'))

def remove_from_blacklist(request, filter_name):
    k = ''
    ip = request.GET.get('ip', '')
    if ip:
        k += ':' + ip
    username = unquote(request.GET.get('username', ''))
    if username:
        k += ':' + username
    if k:
        get_redis().delete((filter_name.upper() + 'b' + k))
    return HttpResponseRedirect(reverse('admin:redissentry_dashboard_changelist'))

def remove_from_counters(request, filter_name):
    k = ''
    ip = request.GET.get('ip', '')
    if ip:
        k += ':' + ip
    username = unquote(request.GET.get('username', ''))
    if username:
        k += ':' + username
    if k:
        get_redis().delete((filter_name.upper() + 'c' + k))
    return HttpResponseRedirect(reverse('admin:redissentry_dashboard_changelist'))

