from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogViewSet,
    ChangeHistoryViewSet,
    CommentViewSet,
    ServiceRequestViewSet,
    UserSettingsViewSet,
    moderator_panel,
    request_create,
    request_detail,
    request_list,
    request_update,
    settings_view,
)

router = DefaultRouter()
router.register('requests', ServiceRequestViewSet, basename='api-requests')
router.register('comments', CommentViewSet, basename='api-comments')
router.register('history', ChangeHistoryViewSet, basename='api-history')
router.register('settings', UserSettingsViewSet, basename='api-settings')
router.register('audit-log', AuditLogViewSet, basename='api-audit')

urlpatterns = [
    path('', request_list, name='request-list'),
    path('requests/create/', request_create, name='request-create'),
    path('requests/<int:pk>/', request_detail, name='request-detail'),
    path('requests/<int:pk>/edit/', request_update, name='request-update'),
    path('moderator/', moderator_panel, name='moderator-panel'),
    path('settings/', settings_view, name='user-settings'),
    path('api/', include(router.urls)),
]
