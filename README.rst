=================
django-cms-search
=================

This package provides multilingual search indexes for easy Haystack integration with django CMS.

Usage
=====

After installing django-cms-search through your package manager of choice, add ``cms_search`` to your
``INSTALLED_APPS``. That's it.

For setting up Haystack, please refer to their `documentation <http://docs.haystacksearch.org/dev/>`_.

For more docs, see the ``docs`` folder or the
`online documentation <http://django-cms-search.readthedocs.org/en/latest/>`_.


.. warning::

    Since version 0.5, the ``HaystackSearchApphook`` is not registered automatically
    anymore. If you want do use the default app hook provided by django-cms-search,
    add this (e.g. in ``models.py``)::

        from cms_search.cms_app import HaystackSearchApphook
        apphook_pool.register(HaystackSearchApphook)
