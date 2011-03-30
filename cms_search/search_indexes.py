from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.html import strip_tags

from haystack import indexes, site

from cms.models.pluginmodel import CMSPlugin

from cms_search import models as proxy_models

def page_index_factory(language_code, proxy_model):

    class _PageIndex(indexes.SearchIndex):
        language = language_code

        text = indexes.CharField(document=True, use_template=False)
        pub_date = indexes.DateTimeField(model_attr='publication_date')
        login_required = indexes.BooleanField(model_attr='login_required')
        url = indexes.CharField(stored=True, indexed=False, model_attr='get_absolute_url')
        title = indexes.CharField(stored=True, indexed=False, model_attr='get_title')

        def prepare(self, obj):
            self.prepared_data = super(_PageIndex, self).prepare(obj)
            plugins = CMSPlugin.objects.filter(language=language_code, placeholder__in=obj.placeholders.all())
            text = ''
            for plugin in plugins:
                instance, _ = plugin.get_plugin_instance()
                if hasattr(instance, 'search_fields'):
                    text += u''.join(force_unicode(strip_tags(getattr(instance, field, ''))) for field in instance.search_fields)
                if getattr(instance, 'search_fulltext', False):
                    text += strip_tags(instance.render_plugin())
            self.prepared_data['text'] = text
            return self.prepared_data

        def get_queryset(self):
            qs = proxy_model.objects.published().filter(title_set__language=language_code).distinct()
            if 'publisher' in settings.INSTALLED_APPS:
                qs = qs.filter(publisher_is_draft=True)
            return qs

    return _PageIndex

for language_code, language_name in settings.LANGUAGES:
    proxy_model = getattr(proxy_models, proxy_models.proxy_name(language_code))
    index = page_index_factory(language_code, proxy_model)
    if proxy_model:
        site.register(proxy_model, index)
    else:
        print "no page proxy model found for language %s" % language_code