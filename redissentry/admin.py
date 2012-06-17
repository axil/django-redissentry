from django.contrib import admin
from django.conf.urls.defaults import patterns
from django.conf import settings

from .models import Dashboard, Whitelist, BlocksHistoryRecord, WhitelistRecord
from .views import (
    show_dashboard, show_whitelist, 
    remove_from_whitelist, remove_from_blacklist, remove_from_counters,
)

class DashboardAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(DashboardAdmin, self).get_urls()
        my_urls = patterns('',
                (r'^$', self.admin_site.admin_view(show_dashboard)),
                (r'^remove/counter/(.)/$', self.admin_site.admin_view(remove_from_counters)),
                (r'^remove/block/(.)/$', self.admin_site.admin_view(remove_from_blacklist)),
        )
        return my_urls + urls

    def has_add_permission(self, request, obj=None):
        return False

#class WhitelistAdmin(admin.ModelAdmin):
#    def get_urls(self):
#        urls = super(WhitelistAdmin, self).get_urls()
#        my_urls = patterns('',
#                (r'^$', self.admin_site.admin_view(show_whitelist)),
#                (r'^remove/$', self.admin_site.admin_view(remove_from_whitelist)),
#        )
#        return my_urls + urls
#
#    def has_add_permission(self, request, obj=None):
#        return False
#
class WhitelistRecordAdmin(admin.ModelAdmin):
    list_display = 'ip', 'user', 'expire_date'
admin.site.register(WhitelistRecord, WhitelistRecordAdmin)

Dashboard._meta.abstract = False
admin.site.register(Dashboard, DashboardAdmin)
Dashboard._meta.abstract = True

#Whitelist._meta.abstract = False
#admin.site.register(Whitelist, WhitelistAdmin)
#Whitelist._meta.abstract = True

if getattr(settings, 'RS_SAVE_HISTORY', True):
    class BlocksHistoryRecordAdmin(admin.ModelAdmin):
        list_display = 'block_type', 'ip', 'get_username', 'failed_attempts', 'blocked_attempts', 'created'
        list_filter = 'block_type',
        search_fields = 'ip', 'username'
        date_hierarchy = 'created'
        
        def has_add_permission(self, request, obj=None):
            return False

    admin.site.register(BlocksHistoryRecord, BlocksHistoryRecordAdmin)

from .decorators import protect
try:
    admin.forms.authenticate = protect(admin.forms.authenticate) # django >= 1.3
except:
    admin.sites.authenticate = protect(admin.sites.authenticate) # django < 1.3
    
