from rest_framework.pagination import PageNumberPagination

MAX_PAGE_SIZE = 100
DEFAULT_LIMIT = 6


class RecipePagination(PageNumberPagination):
    """Пагинация для рецептов на главной странице."""

    page_size_query_param = "limit"
    MAX_PAGE_SIZE
    DEFAULT_LIMIT = 6

    def get_page_size(self, request):
        limit = request.query_params.get(self.page_size_query_param)
        if limit:
            try:
                return min(int(limit), self.max_page_size)
            except (TypeError, ValueError):
                pass
        return self.default_limit
