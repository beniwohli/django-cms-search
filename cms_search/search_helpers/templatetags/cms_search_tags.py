from classytags.arguments import Argument
from classytags.core import Options
from classytags.helpers import AsTag
import haystack
from django import template
from django.conf import settings
from django.utils.translation import get_language

register = template.Library()

class GetTransFieldTag(AsTag):
    """
    Templatetag to access translated attributes of a `haystack.models.SearchResult`.

    By default, it looks for a translated field at `field_name`_`language`. To
    customize this, subclass `GetTransFieldTag` and override `get_translated_value`.

    """
    EMPTY_VALUE = ''
    FALLBACK = True
    name = 'get_translated_value'
    options = Options(
        Argument('obj'),
        Argument('field_name'),
        'as',
        Argument('varname', resolve=False, required=False)
    )
    
    def get_value(self, context, obj, field_name):
        """
        gets the translated value of field name. If `FALLBACK`evaluates to `True` and the field
        has no translation for the current language, it tries to find a fallback value, using
        the languages defined in `settings.LANGUAGES`.

        """
        try:
            language = get_language()
            value = self.get_translated_value(obj, field_name, language)
            if value:
                return value
            if self.FALLBACK:
                for lang, lang_name in settings.LANGUAGES:
                    if lang == language:
                        # already tried this one...
                        continue
                    value = self.get_translated_value(obj, field_name, lang)
                    if value:
                        return value
            untranslated = getattr(obj, field_name)
            if self._is_truthy(untranslated):
                return untranslated
            else:
                return self.EMPTY_VALUE
        except Exception:
            if settings.TEMPLATE_DEBUG:
                raise
            return self.EMPTY_VALUE

    def get_translated_value(self, obj, field_name, language):
        safe_lang = language.replace('-', '_')
        value = getattr(obj, '%s_%s' % (field_name, safe_lang), '')
        if self._is_truthy(value):
            return value
        else:
            return self.EMPTY_VALUE

    def _is_truthy(self, value):
        if isinstance(value, haystack.fields.NOT_PROVIDED):
            return False
        elif isinstance(value, basestring) and value.startswith('<haystack.fields.NOT_PROVIDED instance at '): #UUUGLY!!
            return False
        return bool(value)


register.tag(GetTransFieldTag)