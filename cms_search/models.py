from cms.models import Page
from cms.models.managers import PageManager
from django.conf import settings
from django.utils.translation import ugettext_lazy, string_concat, activate, get_language


CMS_SEARCH_SITES = getattr(settings, 'CMS_SEARCH_SITES', [1])


def proxy_name(language_code, site_id):
    safe_code = language_code.replace('-', ' ').title().replace(' ', '_')
    return 'Page_%s_%s' % (safe_code, site_id)


def page_proxy_factory(language_code, language_name, site_id):
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
        verbose_name = string_concat(Page._meta.verbose_name, ' (', language_name, ') (site: ', site_id, ')')
        verbose_name_plural = string_concat(Page._meta.verbose_name_plural, ' (', language_name, ') (site: ', site_id, ')')

    attrs = {'__module__': Page.__module__,
             'Meta': Meta,
             'objects': PageManager(),
             'get_absolute_url': get_absolute_url}

    _PageProxy = type(proxy_name(language_code, site_id), (Page,), attrs)

    _PageProxy._meta.parent_attr = 'parent'
    _PageProxy._meta.left_attr = 'lft'
    _PageProxy._meta.right_attr = 'rght'
    _PageProxy._meta.tree_id_attr = 'tree_id'

    return _PageProxy

module_namespace = globals()

for site_id in CMS_SEARCH_SITES:
    for language_code, language_name in settings.LANGUAGES:
        if isinstance(language_name, basestring):
            language_name = ugettext_lazy(language_name)
        proxy_model = page_proxy_factory(language_code, language_name, site_id)
        module_namespace[proxy_model.__name__] = proxy_model