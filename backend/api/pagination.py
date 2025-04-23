from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)


class CustomRecipePagination(LimitOffsetPagination):
    limit_query_param = 'recipes_limit'


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
