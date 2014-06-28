import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.sites.models import Site
from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.template import RequestContext
from django.test.client import RequestFactory
from django.utils.encoding import force_unicode
from django.utils.translation import get_language, activate


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

class PageIndex(indexes.SearchIndex):

    text = indexes.CharField(document=True, use_template=False)
    language = indexes.CharField()
    pub_date = indexes.DateTimeField(model_attr='publication_date', null=True)
    login_required = indexes.BooleanField(model_attr='login_required')
    url = indexes.CharField(stored=True, indexed=False, model_attr='get_absolute_url')
    title = indexes.CharField(stored=True, indexed=False, model_attr='get_title')
    site_id = indexes.IntegerField(stored=True, indexed=True, model_attr='site_id')

def _get_index_base():
    index_string = search_settings.INDEX_BASE_CLASS
    module, class_name = index_string.rsplit('.', 1)
    mod = importlib.import_module(module)
    base_class = getattr(mod, class_name, None)
    if not base_class:
        raise ImproperlyConfigured('CMS_SEARCH_INDEX_BASE_CLASS: module %s has no class %s' % (module, class_name))
    if not issubclass(base_class, indexes.SearchIndex):
        raise ImproperlyConfigured('CMS_SEARCH_INDEX_BASE_CLASS: %s is not a subclass of haystack.indexes.SearchIndex' % search_settings.INDEX_BASE_CLASS)
    required_fields = ['text', 'language']
    if not all(field in base_class.fields for field in required_fields):
        raise ImproperlyConfigured('CMS_SEARCH_INDEX_BASE_CLASS: %s must contain at least these fields: %s' % (search_settings.INDEX_BASE_CLASS, required_fields))
    return base_class

rf = RequestFactory()

def page_index_factory(language_code):

    class _PageIndex(_get_index_base()):
        _language = language_code


        def prepare(self, obj):
            current_languge = get_language()
            try:
                if current_languge != self._language:
                    activate(self._language)
                request = rf.get("/")
                request.session = {}
                request.LANGUAGE_CODE = self._language
                self.prepared_data = super(_PageIndex, self).prepare(obj)
                plugins = CMSPlugin.objects.filter(language=language_code, placeholder__in=obj.placeholders.all())
                text = u''
                for base_plugin in plugins:
                    instance, plugin_type = base_plugin.get_plugin_instance()
                    if instance is None:
                        # this is an empty plugin
                        continue
                    if hasattr(instance, 'search_fields'):
                        text += u' '.join(force_unicode(_strip_tags(getattr(instance, field, ''))) for field in instance.search_fields)
                    if getattr(instance, 'search_fulltext', False) or getattr(plugin_type, 'search_fulltext', False):
                        text += _strip_tags(instance.render_plugin(context=RequestContext(request))) + u' '
                text += obj.get_meta_description() or u''
                text += u' '
                text += obj.get_meta_keywords() or u''
                self.prepared_data['text'] = text
                self.prepared_data['language'] = self._language
                return self.prepared_data
            finally:
                if get_language() != current_languge:
                    activate(current_languge)

        def index_queryset(self):
            # get the correct language and exclude pages that have a redirect
            base_qs = super(_PageIndex, self).index_queryset()
            result_qs = EmptyQuerySet()
            for site_obj in Site.objects.all():
                qs = base_qs.published(site=site_obj.id).filter(
                    Q(title_set__language=language_code) & (Q(title_set__redirect__exact='') | Q(title_set__redirect__isnull=True)))
                if 'publisher' in settings.INSTALLED_APPS:
                    qs = qs.filter(publisher_is_draft=True)
                qs = qs.distinct()
                result_qs |= qs
            return result_qs

    return _PageIndex

for language_code, language_name in settings.LANGUAGES:
    proxy_model = getattr(proxy_models, proxy_models.proxy_name(language_code))
    index = page_index_factory(language_code)
    if proxy_model:
        site.register(proxy_model, index)
    else:
        print "no page proxy model found for language %s" % language_code
