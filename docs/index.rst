=================
django-cms-search
=================

This package provides multilingual search indexes for easy Haystack integration with django CMS.

Usage
=====

After installing django-cms-search through your package manager of choice, add ``cms_search`` to your
``INSTALLED_APPS``. That's it.

For setting up Haystack, please refer to their `documentation <http://docs.haystacksearch.org/dev/>`_.

Customizing the Index
---------------------

You can customize what parts of a ``CMSPlugin`` end up in the index with two class attributes on ``CMSPlugin``
subclasses:

.. py:attribute:: search_fields

    a list of field names to index.

.. py:attribute:: search_fulltext

    if ``True``, the index renders the plugin and adds the result (sans HTML tags) to the index.

Helpers
=======

django-cms-search provides a couple of useful helpers to deal with multilingual content.

``cms_search.helpers.indexes.MultiLanguageIndex``
-------------------------------------------------

A :py:class:`haystack.indexes.SearchIndex` that dynamically adds translated fields to the search index. An example for when this is useful is the
app hook infrastructure from django CMS. When a model's ``get_absolute_url`` uses a url pattern that is attached to an
app hook, the URL varies depending on the language. A usage example:

.. code-block:: python

    from haystack import indexes
    from cms_search.helpers.indexes import MultiLanguageIndex

    class NewsIndex(MultiLanguageIndex):
        text = indexes.CharField(document=True, use_template=True)
        title = indexes.CharField(model_attr='title')
        url = indexes.CharField(stored=True)

        def prepare_url(self, obj):
            return obj.get_absolute_url()

        class HaystackTrans:
            fields = ('url', 'title')

.. note::

    * ``MultiLanguageIndex`` dynamically creates translated fields. The name of the dynamic fields is a concatenation of the
      original field name, an underscore and the language code.
    * If you define a ``prepare`` method for a translated field, that method will be called multiple times, with changing
      active language.
    * In the above example, you might want to catch ``NoReverseMatch`` exceptions if you don't have activated the app hook
      for all languages defined in ``settings.LANGUAGES``.
    * The ``model_attr`` attribute is handled somewhat specially. The index tries to find a field on the model called
      ``model_attr + '_' + language_code``. If it exists, it is used as the translated value. But it isn't possible to supply
      the name of a model method and let the index call it with varying activated languages. Use ``prepare_myfieldname`` for
      that case.

``{% get_translated_value %}`` template tag
-------------------------------------------

This template tag is most useful in combination with the ``MultiLanguageIndex``. You can use it while looping through
search results, and it will automatically pick up the translated field for the current language or fall back to another
available language (in the order defined in ``settings.LANGUAGES``). Example:

.. code-block:: html+django

    {% load cms_search %}

    <ul class="search-results">
        {% for result in page.object_list %}
            <li><a href="{% get_translated_value result "url" %}">{% get_translated_value result "title" %}</a></li>
        {% endfor %}
    </ul>
