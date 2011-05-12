import inspect

from django.conf import settings
from haystack import indexes
from django.utils.translation import activate, get_language


class MultiLangPrepareDecorator(object):
    def __init__(self, language):
        self.language = language

    def __call__(self, func):
        def wrapped(*args):
            old_language = get_language()
            activate(self.language)
            try:
                return func(*args)
            finally:
                activate(old_language)
        return wrapped


class MultiLanguageIndexBase(indexes.DeclarativeMetaclass):

    @classmethod
    def _get_field_copy(cls, field, language):
        model_attr = field.model_attr
        if model_attr:
            model_attr += '_%s' % language.replace('-', '_')
        arg_names = inspect.getargspec(indexes.SearchField.__init__)[0][2:]
        kwargs = dict((arg_name, getattr(field, arg_name)) for arg_name in arg_names if hasattr(field, arg_name))
        kwargs['model_attr'] = model_attr
        copy = field.__class__(**kwargs)
        copy.null = True
        return copy

    def __new__(cls, name, bases, attrs):
        if 'HaystackTrans' in attrs:
            for field in getattr(attrs['HaystackTrans'], 'fields', []):
                if field not in attrs:
                    continue
                for lang_tuple in settings.LANGUAGES:
                    lang = lang_tuple[0]
                    safe_lang = lang.replace('-', '_')
                    attrs['%s_%s' % (field, safe_lang)] = cls._get_field_copy(attrs[field], lang)
                    if 'prepare_' + field in attrs:
                        attrs['prepare_%s_%s' % (field, safe_lang)] = MultiLangPrepareDecorator(lang)(attrs['prepare_' + field])
        return super(MultiLanguageIndexBase, cls).__new__(cls, name, bases, attrs)


class MultiLanguageIndex(indexes.SearchIndex):
    __metaclass__ = MultiLanguageIndexBase
