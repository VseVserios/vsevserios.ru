# Security utilities for the application

import hashlib
import secrets
from django.utils import timezone
from datetime import timedelta


def generate_verification_code(length=6):
    """Генерирует случайный численный код верификации"""
    return str(secrets.randbelow(10 ** length)).zfill(length)


def hash_code(code):
    """Хеширует код верификации"""
    return hashlib.sha256(code.encode()).hexdigest()


def verify_code_hash(code, code_hash):
    """Проверяет соответствие кода и его хеша"""
    return hashlib.sha256(code.encode()).hexdigest() == code_hash


def check_rate_limit(request, key_prefix, max_attempts=5, window_seconds=3600):
    """
    Проверяет rate limiting для запроса
    
    Args:
        request: Django request object
        key_prefix: Префикс для ключа rate limiting
        max_attempts: Максимальное количество попыток
        window_seconds: Временное окно в секундах
    
    Returns:
        bool: True если лимит не превышен, False если превышен
    """
    from django.core.cache import cache
    
    client_ip = get_client_ip(request)
    cache_key = f"ratelimit:{key_prefix}:{client_ip}"
    
    attempt_count = cache.get(cache_key, 0)
    
    if attempt_count >= max_attempts:
        return False
    
    cache.set(cache_key, attempt_count + 1, window_seconds)
    return True


def get_client_ip(request):
    """Получает IP адрес клиента из request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_suspicious_activity(request, threshold=10):
    """
    Проверяет подозрительную активность
    
    Args:
        request: Django request object
        threshold: Количество запросов за 60 секунд для подозрения
    
    Returns:
        bool: True если активность подозрительна
    """
    from django.core.cache import cache
    
    client_ip = get_client_ip(request)
    cache_key = f"activity:{client_ip}"
    
    count = cache.get(cache_key, 0)
    
    if count >= threshold:
        return True
    
    cache.set(cache_key, count + 1, 60)
    return False


class SecurityHeaders:
    """Класс для добавления security headers к ответам"""
    
    @staticmethod
    def add_security_headers(response):
        """Добавляет security headers к HTTP ответу"""
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


def sanitize_html(html_content, allowed_tags=None):
    """
    Очищает HTML от опасного контента
    
    Args:
        html_content: HTML строка для очистки
        allowed_tags: Список разрешённых тегов
    
    Returns:
        str: Очищенный HTML
    """
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li']
    
    from html import escape
    
    # Простая очистка от опасных тегов
    dangerous = ['script', 'iframe', 'style', 'link', 'meta']
    
    result = html_content
    for tag in dangerous:
        result = result.replace(f'<{tag}', '&lt;' + tag)
        result = result.replace(f'</{tag}>', '&lt;/' + tag + '&gt;')
    
    return result
