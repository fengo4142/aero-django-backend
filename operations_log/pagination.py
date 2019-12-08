from rest_framework import pagination


class LogPaginationClass(pagination.PageNumberPagination):
    page_size = 10
