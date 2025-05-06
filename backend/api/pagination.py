from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)


class Pagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class RecipePagination(LimitOffsetPagination):
    limit_query_param = 'recipes_limit'
