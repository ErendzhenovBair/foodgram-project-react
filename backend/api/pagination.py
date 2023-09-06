from rest_framework.pagination import PageNumberPagination

from foodgram.settings import NUMBER_OF_RECIPES


class CustomPagination(PageNumberPagination):
    page_size = NUMBER_OF_RECIPES
    page_size_query_param = 'limit'
