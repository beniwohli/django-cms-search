from django.conf import settings

INDEX_BASE_CLASS = getattr(settings, 'CMS_SEARCH_INDEX_BASE_CLASS', 'haystack.indexes.SearchIndex')