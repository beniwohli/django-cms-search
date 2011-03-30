from django.conf.urls.defaults import patterns, url
from django.utils.translation import ugettext_lazy as _

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool

from haystack.views import search_view_factory

class HaystackSearchApphook(CMSApp):
    name = _("search apphook")
    urls = [patterns('',
        url('^$', search_view_factory(), name='haystack-search'),
    ),]

apphook_pool.register(HaystackSearchApphook)