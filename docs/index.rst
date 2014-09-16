=================
django-cms-search
=================

This package provides multilingual search indexes for easy Haystack integration
with `django CMS <http://www.django-cms.org>`_.

Requirements
============

 * Django >= 1.3
 * django CMS >= 2.1.3
 * django-haystack >= 1.2.4, < 2.0 (support for 2.0 will be a priority once it is released)
 * django-classy-tags >= 0.3.2

Usage
=====

After installing django-cms-search through your package manager of choice, add
:mod:`cms_search` to your :setting:`INSTALLED_APPS`. 

.. warning::

    Since version 0.5, the ``HaystackSearchApphook`` is not registered automatically
    anymore. If you want do use the default app hook provided by django-cms-search,
    add this (e.g. in ``models.py``)::

        from cms_search.cms_app import HaystackSearchApphook
        apphook_pool.register(HaystackSearchApphook)

Configure Haystack, please refer to their
`documentation <http://django-haystack.readthedocs.org/en/v1.2.7/tutorial.html#configuration>`_ and follow all steps under "Configuration". Add a `search site <http://django-haystack.readthedocs.org/en/v1.2.7/tutorial.html#create-a-searchsite>`_ and `search template <http://django-haystack.readthedocs.org/en/v1.2.7/tutorial.html#search-template>`_. (This app handles the SearchIndex for you and the CMS itself handles the URLs so you can skip those steps.)

To add a search results page add a new page to the CMS. Give it a title. Set the status to: "published". Set the template to: "inherit the template of the nearest ancestor". Set the application (under advanced settings) to" "search apphook". Save.

Customizing the Index
---------------------

You can customize what parts of a :class:`~cms.models.CMSPlugin` end up in
the index with two class attributes on :class:`~cms.plugin_base.CMSPluginBase`
subclasses:

.. attribute:: search_fields

    a list of field names to index.

.. attribute:: search_fulltext

    if ``True``, the index renders the plugin and adds the result (sans HTML
    tags) to the index.

    .. note::

        Before version 0.6 of this library, this attributes had to be defined on
        :class:`~cms.models.CMSPlugin`. Starting with 0.6, it can also be defined
        on :class:`~cms.plugin_base.CMSPluginBase`, for cases where one 
        :class:`~cms.models.CMSPlugin` subclass is used by multiple 
        :class:`~cms.plugin_base.CMSPluginBase` subclasses with different search
        requirements.

Helpers
=======

.. module:: cms_search.search_helpers

django-cms-search provides a couple of useful helpers to deal with multilingual
content.


.. py:class:: cms_search.search_helpers.indexes.MultiLanguageIndex

    A :class:`~haystack:SearchIndex` that dynamically adds translated fields to
    the search index.  An example for when this is useful is the app hook
    infrastructure from django CMS. When a model's
    :meth:`~django.db.models.Model.get_absolute_url` uses a url pattern that
    is attached to an app hook, the URL varies depending on the language. A
    usage example:

    .. code-block:: python

        from haystack import indexes
        from cms_search.search_helpers.indexes import MultiLanguageIndex

        class NewsIndex(MultiLanguageIndex):
            text = indexes.CharField(document=True, use_template=True)
            title = indexes.CharField(model_attr='title')
            url = indexes.CharField(stored=True)

            def prepare_url(self, obj):
                return obj.get_absolute_url()

            class HaystackTrans:
                fields = ('url', 'title')

    .. note::

        * :class:`~cms_search.search_helpers.indexes.MultiLanguageIndex`
          dynamically creates translated fields. The name of the dynamic fields
          is a concatenation of the original field name, an underscore and the
          language code.
        * If you define a :meth:`prepare` method for a translated field, that
          method will be called multiple times, with changing active language.
        * In the above example, you might want to catch
          :class:`~django.core.urlresolvers.NoReverseMatch` exceptions if you
          don't have activated the app hook for all languages defined in
          :setting:`django:LANGUAGES`.
        * The :attr:`~haystack:SearchField.model_attr` attribute is handled
          somewhat specially. The index tries to find a field on the model
          called ``model_attr + '_' + language_code``. If it exists, it is used
          as the translated value. But it isn't possible to supply the name of
          a model method and let the index call it with varying activated
          languages. Use :meth:`prepare_myfieldname` for that case.

    .. note::

        django CMS monkeypatches :func:`django.core.urlresolvers.reverse` to
        enable language namespaces. To ensure that this monkeypatching happens
        before haystack autodiscovers your indexes, your ``search_sites.py``
        should look somewhat like this:

        .. code-block:: python

            from cms.models import monkeypatch_reverse
            import haystack

            monkeypatch_reverse()
            haystack.autodiscover()


.. py:class:: cms_search.search_helpers.fields.MultiLangTemplateField

    A :class:`haystack.indexes.CharField` subclass that renders the search
    template in all languages defined in :setting:`django:LANGUAGES` and
    concatenates the result.

    .. note::

        If you plan to render django CMS placeholders in the template,
        make sure to pass the ``needs_request`` argument to 
        :meth:`cms_search.search_helpers.fields.MultiLangTemplateField`.

.. templatetag:: get_translated_value

``{% get_translated_value %}`` template tag
-------------------------------------------

This template tag is most useful in combination with the
:class:`~cms_search.search_helpers.indexes.MultiLanguageIndex`. You can use it
while looping through search results, and it will automatically pick up the
translated field for the current language or fall back to another available
language (in the order defined in :setting:`django:LANGUAGES`). Example:

.. code-block:: html+django

    {% load cms_search_tags %}

    <ul class="search-results">
        {% for result in page.object_list %}
            <li><a href="{% get_translated_value result "url" %}">{% get_translated_value result "title" %}</a></li>
        {% endfor %}
    </ul>

.. note::

    If you plan to use this template tag, you have to add
    :mod:`cms_search.search_helpers` to your :setting:`django:INSTALLED_APPS`.


Settings
========
.. setting: CMS_SEARCH_INDEX_BASE_CLASS

CMS_SEARCH_INDEX_BASE_CLASS
---------------------------
Default: :class:`haystack.indexes.SearchIndex <haystack:SearchIndex>`

This setting can be used to add custom fields to the search index if the
included fields do not suffice. Make sure to provide the full path
to your :class:`haystack:SearchIndex` subclass.
