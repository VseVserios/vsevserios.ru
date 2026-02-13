# Database optimization utilities

from django.db.models import Prefetch, Select_related
from django.db import connection
from django.test.utils import CaptureQueriesContext


def log_query_count(view_func):
    """Декоратор для логирования количества SQL запросов"""
    def wrapper(*args, **kwargs):
        with CaptureQueriesContext(connection) as context:
            result = view_func(*args, **kwargs)
            print(f"View {view_func.__name__} executed {len(context)} queries")
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
            query_count = len(connection.queries) if hasattr(connection, 'queries') else 0
            if query_count > 10:  # Предупреждение при более чем 10 запросах
                import logging
                logger = logging.getLogger('django')
                logger.warning(f"Path {request.path} executed {query_count} queries")
        
        return response
