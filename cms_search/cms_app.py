from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

from cms.app_base import CMSApp

from haystack.views import search_view_factory

class HaystackSearchApphook(CMSApp):
    name = _("search apphook")
    urls = [patterns('',
        url('^$', search_view_factory(), name='haystack-search'),
    ),]

