# Caching utilities for the application

from functools import wraps
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.decorators import method_decorator
from datetime import timedelta


# Кеширование на разные периоды времени
CACHE_DURATIONS = {
    'short': 60,        # 1 минута
    'medium': 300,      # 5 минут
    'long': 3600,       # 1 час
    'very_long': 86400, # 1 день
}


def cache_result(duration_key='medium', key_prefix=''):
    """Декоратор для кеширования результатов функций"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            duration = CACHE_DURATIONS.get(duration_key, CACHE_DURATIONS['medium'])
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            
            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, duration)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(pattern):
    """Очистка кеша по шаблону"""
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern(pattern)
    else:
        # Fallback для БД кеша
        pass


class CachedQuerySet:
    """Вспомогательный класс для кеширования QuerySet результатов"""
    
    def __init__(self, queryset, cache_duration='medium', cache_key=None):
        self.queryset = queryset
        self.cache_duration = CACHE_DURATIONS.get(cache_duration, CACHE_DURATIONS['medium'])
        self.cache_key = cache_key or f"qs:{queryset.model.__name__}"
    
    def get(self):
        result = cache.get(self.cache_key)
        if result is None:
            result = list(self.queryset)
            cache.set(self.cache_key, result, self.cache_duration)
        return result
    
    def invalidate(self):
        cache.delete(self.cache_key)


# Кеширование для часто используемых данных
def get_user_profile_cached(user_id):
    """Получить профиль пользователя с кешем"""
    from accounts.models import User
    cache_key = f"user_profile:{user_id}"
    
    profile = cache.get(cache_key)
    if profile is None:
        try:
            user = User.objects.select_related('profile').get(id=user_id)
            profile = user.profile
            cache.set(cache_key, profile, CACHE_DURATIONS['long'])
        except User.DoesNotExist:
            return None
    
    return profile


def invalidate_user_profile_cache(user_id):
    """Очистить кеш профиля пользователя"""
    cache_key = f"user_profile:{user_id}"
    cache.delete(cache_key)
