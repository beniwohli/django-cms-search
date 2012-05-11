from django.conf import settings
from haystack import indexes
from django.utils.translation import get_language, activate
from django.template import loader, Context

try:
    from django.test.client import RequestFactory
except ImportError:
    from cms_search.utils import RequestFactory

rf = RequestFactory()

class MultiLangTemplateField(indexes.CharField):

    def __init__(self, needs_request=False, **kwargs):
        kwargs['use_template'] = True
        self.needs_request = needs_request
        super(MultiLangTemplateField, self).__init__(**kwargs)

    def prepare_template(self, obj):
        content = []
        current_lang = get_language()
        try:
            for lang, lang_name in settings.LANGUAGES:
                activate(lang)
                content.append(self._prepare_template(obj, needs_request=self.needs_request))
        finally:
            activate(current_lang)
        return '\n'.join(content)

    def _prepare_template(self, obj, needs_request=False):
        """
        This is a copy of CharField.prepare_template, except that it adds a fake
        request to the context, which is mainly needed to render CMS placeholders
        """
        if self.instance_name is None and self.template_name is None:
            raise SearchFieldError("This field requires either its instance_name variable to be populated or an explicit template_name in order to load the correct template.")

        if self.template_name is not None:
            template_names = self.template_name

            if not isinstance(template_names, (list, tuple)):
                template_names = [template_names]
        else:
            template_names = ['search/indexes/%s/%s_%s.txt' % (obj._meta.app_label, obj._meta.module_name, self.instance_name)]

        t = loader.select_template(template_names)
        ctx = {'object': obj}
        if needs_request:
            request = rf.get("/")
            request.session = {}
            ctx['request'] = request
        return t.render(Context(ctx))
