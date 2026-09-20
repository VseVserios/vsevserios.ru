# Database optimization utilities

import logging

from django.db import connection
from django.test.utils import CaptureQueriesContext

logger = logging.getLogger(__name__)


def log_query_count(view_func):
    """Декоратор для логирования количества SQL запросов"""
    def wrapper(*args, **kwargs):
        with CaptureQueriesContext(connection) as context:
            result = view_func(*args, **kwargs)
            logger.debug("View %s executed %s queries",
                         view_func.__name__, len(context))
        return result
    return wrapper


class DatabaseOptimizationMiddleware:
    """Middleware для логирования медленных запросов в development"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(connection, 'queries_log'):
            connection.queries = []

        response = self.get_response(request)

        if hasattr(connection, 'queries_log') and hasattr(request, 'path'):
            query_count = len(connection.queries) if hasattr(
                connection, 'queries') else 0
            if query_count > 10:  # Предупреждение при более чем 10 запросах
                logger.warning("Path %s executed %s queries",
                               request.path, query_count)
