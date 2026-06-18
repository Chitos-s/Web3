import time
import uuid

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from django.http import JsonResponse

from .logging import request_id_var, username_var
from .models import AuditLog


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get('X-Request-ID', uuid.uuid4().hex)
        request._request_started_at = time.monotonic()
        request_id_var.set(request.request_id)
        username_var.set('anonymous')
        response = self.get_response(request)
        request._request_duration_ms = int((time.monotonic() - request._request_started_at) * 1000)
        response['X-Request-ID'] = request.request_id
        response['X-Response-Time-ms'] = str(request._request_duration_ms)
        return response


class AutoUserDetectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_user = getattr(request, 'user', None)
        if not getattr(current_user, 'is_authenticated', False):
            username = request.headers.get('X-Portal-User')
            if username:
                try:
                    request.user = User.objects.get(username=username)
                except User.DoesNotExist:
                    request.user = AnonymousUser()
        actor = getattr(request, 'user', None)
        if actor and actor.is_authenticated:
            username_var.set(actor.username)
        return self.get_response(request)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for prefix, (limit, period) in settings.PORTAL_RATE_LIMITS.items():
            if request.path.startswith(prefix):
                identity = getattr(request.user, 'id', None) or request.META.get('REMOTE_ADDR', 'anon')
                key = f'rl:{prefix}:{identity}'
                current = cache.get(key, 0)
                if current >= limit:
                    return JsonResponse({'detail': 'Слишком много запросов. Повторите позже.'}, status=429)
                cache.set(key, current + 1, timeout=period)
                break
        return self.get_response(request)


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, 'user', None)
        if not request.path.startswith('/static/'):
            AuditLog.objects.create(
                user=user if getattr(user, 'is_authenticated', False) else None,
                username_snapshot=getattr(user, 'username', ''),
                request_id=getattr(request, 'request_id', ''),
                ip_address=_extract_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                method=request.method,
                path=request.path[:255],
                action=_resolve_action_name(request),
                status_code=response.status_code,
                success=200 <= response.status_code < 400,
            )
        return response


def _extract_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _resolve_action_name(request):
    try:
        from django.urls import resolve

        return resolve(request.path_info).url_name or ''
    except Exception:
        return ''
