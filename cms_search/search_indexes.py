from django.template import RequestContext
import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_unicode
from django.utils.translation import get_language, activate
from django.db.models import Q

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

from haystack import indexes, site

from cms.models.pluginmodel import CMSPlugin

from cms_search import models as proxy_models
from cms_search import settings as search_settings

def _get_index_base():
    index_string = search_settings.INDEX_BASE_CLASS
    module, class_name = index_string.rsplit('.', 1)
    mod = importlib.import_module(module)
    base_class = getattr(mod, class_name, None)
    if not base_class:
        raise ImproperlyConfigured('CMS_SEARCH_INDEX_BASE_CLASS: module %s has no class %s' % (module, class_name))
    if not issubclass(base_class, indexes.SearchIndex):
        raise ImproperlyConfigured('CMS_SEARCH_INDEX_BASE_CLASS: %s is not a subclass of haystack.indexes.SearchIndex' % search_settings.INDEX_BASE_CLASS)
    return base_class

rf = RequestFactory()

def page_index_factory(language_code, proxy_model):

    class _PageIndex(_get_index_base()):
        _language = language_code
        language = indexes.CharField()

        text = indexes.CharField(document=True, use_template=False)
        pub_date = indexes.DateTimeField(model_attr='publication_date', null=True)
        login_required = indexes.BooleanField(model_attr='login_required')
        url = indexes.CharField(stored=True, indexed=False, model_attr='get_absolute_url')
        title = indexes.CharField(stored=True, indexed=False, model_attr='get_title')
        site_id = indexes.IntegerField(stored=True, indexed=True, model_attr='site_id')

        def prepare(self, obj):
            current_languge = get_language()
            try:
                activate(self._language)
                request = rf.get("/")
                request.session = {}
                self.prepared_data = super(_PageIndex, self).prepare(obj)
                plugins = CMSPlugin.objects.filter(language=language_code, placeholder__in=obj.placeholders.all())
                text = u''
                for plugin in plugins:
                    instance, _ = plugin.get_plugin_instance()
                    if hasattr(instance, 'search_fields'):
                        text += u' '.join(force_unicode(_strip_tags(getattr(instance, field, ''))) for field in instance.search_fields)
                    if getattr(instance, 'search_fulltext', False):
                        text += _strip_tags(instance.render_plugin(context=RequestContext(request))) + u' '
                text += obj.get_meta_description() or u''
                text += u' '
                text += obj.get_meta_keywords() or u''
                self.prepared_data['text'] = text
                self.prepared_data['language'] = self._language
                return self.prepared_data
            finally:
                activate(current_languge)

        def index_queryset(self):
            # get the correct language and exclude pages that have a redirect
            qs = super(_PageIndex, self).index_queryset()
            qs = qs.published().filter(
                Q(title_set__language=language_code) & (Q(title_set__redirect__exact='') | Q(title_set__redirect__isnull=True)))
            if 'publisher' in settings.INSTALLED_APPS:
                qs = qs.filter(publisher_is_draft=True)
            qs = qs.distinct()
            return qs

    return _PageIndex

for language_code, language_name in settings.LANGUAGES:
    proxy_model = getattr(proxy_models, proxy_models.proxy_name(language_code))
    index = page_index_factory(language_code, proxy_model)
    if proxy_model:
        site.register(proxy_model, index)
    else:
        print "no page proxy model found for language %s" % language_code