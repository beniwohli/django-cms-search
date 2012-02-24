from django.template import RequestContext
import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_unicode
from django.utils.translation import get_language, activate

try:
    from django.test.client import RequestFactory
except ImportError:
    from cms_search.utils import RequestFactory

def _strip_tags(value):
    """
    Returns the given HTML with all tags stripped.

    This is a copy of django.utils.html.strip_tags, except that it adds some
    whitespace in between replaced tags to make sure words are not erroneously
    concatenated.
    """
    return re.sub(r'<[^>]*?>', ' ', force_unicode(value))

try:
    import importlib
except ImportError:
    from django.utils import importlib

from haystack import indexes, connections

from cms.models.pluginmodel import CMSPlugin

from cms_search import models as proxy_models
from cms_search import settings as search_settings

rf = RequestFactory()

def page_index_factory(language_code, proxy_model):

    class _PageIndex(indexes.SearchIndex, indexes.Indexable):
        language = language_code

        text = indexes.CharField(document=True, use_template=False)
        pub_date = indexes.DateTimeField(model_attr='publication_date', null=True)
        login_required = indexes.BooleanField(model_attr='login_required')
        url = indexes.CharField(stored=True, indexed=False, model_attr='get_absolute_url')
        title = indexes.CharField(stored=True, indexed=False, model_attr='get_title')
        site_id = indexes.IntegerField(stored=True, indexed=True, model_attr='site_id')

        def prepare(self, obj):
            current_languge = get_language()
            try:
                activate(self.language)
                request = rf.get("/")
                request.session = {}
                self.prepared_data = super(_PageIndex, self).prepare(obj)
                plugins = CMSPlugin.objects.filter(language=language_code, placeholder__in=obj.placeholders.all())
                text = ''
                for plugin in plugins:
                    instance, _ = plugin.get_plugin_instance()
                    if hasattr(instance, 'search_fields'):
                        text += u''.join(force_unicode(_strip_tags(getattr(instance, field, ''))) for field in instance.search_fields)
                    if getattr(instance, 'search_fulltext', False):
                        text += _strip_tags(instance.render_plugin(context=RequestContext(request)))
                self.prepared_data['text'] = text
                return self.prepared_data
            finally:
                activate(current_languge)

        def get_model(self):
            return proxy_model

        def index_queryset(self):
            qs = proxy_model.objects.published().filter(title_set__language=language_code).distinct()
            if 'publisher' in settings.INSTALLED_APPS:
                qs = qs.filter(publisher_is_draft=True)
            return qs

    return _PageIndex


# we don't want the globals() style which was used in models.py ...
def push_indices():
    magic_indices = []
    for language_code, language_name in settings.LANGUAGES:
        proxy_model = getattr(proxy_models, proxy_models.proxy_name(language_code))
        magic_indices.append( page_index_factory(language_code, proxy_model))
        
    unified_index = connections['default'].get_unified_index()
    prev_indices = [index for key, index in unified_index.indexes.iteritems()]
    all_indices = [ind() for ind in magic_indices] + prev_indices
    unified_index.build(indexes=all_indices)
push_indices()