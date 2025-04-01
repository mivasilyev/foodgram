from rest_framework.pagination import LimitOffsetPagination


class CustomRecipePagination(LimitOffsetPagination):
    limit_query_param = 'recipes_limit'
