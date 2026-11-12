# Error handling and logging utilities

import logging
import traceback
from functools import wraps
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404

logger = logging.getLogger(__name__)


def log_view_execution(view_func):
    """Декоратор для логирования выполнения view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            logger.info(f"Executing view: {view_func.__name__}")
            result = view_func(request, *args, **kwargs)
            logger.info(f"View {view_func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in view {view_func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    return wrapper


def handle_exceptions(view_func):
    """Декоратор для обработки исключений в view"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return JsonResponse({'error': str(e)}, status=400)
        except PermissionDenied:
            logger.warning(f"Permission denied for user {request.user}")
            return JsonResponse({'error': 'Permission denied'}, status=403)
        except Http404:
            logger.warning(f"Not found for URL {request.path}")
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': 'Internal server error'}, status=500)
    return wrapper


class ErrorHandlingMiddleware:
    """Middleware для обработки ошибок на уровне приложения"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            logger.error(traceback.format_exc())
            
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse(
                    {'error': 'Internal server error'},
                    status=500
                )
            
            return HttpResponse(
                'Internal server error',
                status=500
            )


def log_db_query(queryset):
    """Логирует SQL запрос для QuerySet"""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    
    with CaptureQueriesContext(connection) as context:
        list(queryset)
        if context:
            for query in context:
                logger.debug(f"SQL Query: {query['sql']}")
                logger.debug(f"Execution time: {query['time']}ms")


def get_error_context(exception):
    """Формирует контекст ошибки для логирования"""
    return {
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'traceback': traceback.format_exc(),
    }


class APIException(Exception):
    """Базовый класс для исключений API"""
    
    def __init__(self, message, code=400):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationAPIException(APIException):
    """Исключение для ошибок валидации"""
    def __init__(self, message):
        super().__init__(message, 400)


class PermissionAPIException(APIException):
    """Исключение для ошибок прав доступа"""
    def __init__(self, message='Permission denied'):
        super().__init__(message, 403)


class NotFoundAPIException(APIException):
    """Исключение для ошибки 404"""
    def __init__(self, message='Not found'):
        super().__init__(message, 404)


class RateLimitException(APIException):
    """Исключение для превышения rate limit"""
    def __init__(self, message='Too many requests'):
        super().__init__(message, 429)
