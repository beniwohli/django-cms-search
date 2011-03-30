from django.conf import settings
from haystack import indexes
from django.utils.translation import get_language, activate

class MultiLangTemplateField(indexes.CharField):

    def __init__(self, **kwargs):
        kwargs['use_template'] = True
        super(MultiLangTemplateField, self).__init__(**kwargs)

    def prepare_template(self, obj):
        content = []
        current_lang = get_language()
        try:
            for lang, lang_name in settings.LANGUAGES:
                activate(lang)
                content.append(super(MultiLangTemplateField, self).prepare_template(obj))
        finally:
            activate(current_lang)

        return '\n'.join(content)
  