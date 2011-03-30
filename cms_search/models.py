from cms.models import Page
from cms.models.managers import PageManager
from django.conf import settings
from django.utils.translation import ugettext_lazy, string_concat, activate, get_language

def proxy_name(language_code):
    safe_code = language_code.replace('-', ' ').title().replace(' ', '_')
    return 'Page_%s' % safe_code


def page_proxy_factory(language_code, language_name):
    def get_absolute_url(self):
        if 'cms.middleware.multilingual.MultilingualURLMiddleware' in settings.MIDDLEWARE_CLASSES:
            old_language = get_language()
            try:
                activate(language_code)
                return '/%s%s' % (language_code, Page.get_absolute_url(self))
            finally:
                activate(old_language)
        else:
            return Page.get_absolute_url(self)

    class Meta:
        proxy = True
        app_label = 'cms_search'
        if len(settings.LANGUAGES) > 1:
            verbose_name = string_concat(Page._meta.verbose_name, ' (', language_name, ')')
            verbose_name_plural = string_concat(Page._meta.verbose_name_plural, ' (', language_name, ')')
        else:
            verbose_name = Page._meta.verbose_name
            verbose_name_plural = Page._meta.verbose_name_plural

    attrs = {'__module__': Page.__module__,
             'Meta': Meta,
             'objects': PageManager(),
             'get_absolute_url': get_absolute_url}

    _PageProxy = type(proxy_name(language_code), (Page,), attrs)

    _PageProxy._meta.parent_attr = 'parent'
    _PageProxy._meta.left_attr = 'lft'
    _PageProxy._meta.right_attr = 'rght'
    _PageProxy._meta.tree_id_attr = 'tree_id'

    return _PageProxy

module_namespace = globals()

for language_code, language_name in settings.LANGUAGES:
    if isinstance(language_name, basestring):
        language_name = ugettext_lazy(language_name)
    proxy_model = page_proxy_factory(language_code, language_name)
    module_namespace[proxy_model.__name__] = proxy_model