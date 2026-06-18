from django.contrib import admin

from .models import AuditLog, ChangeHistory, Comment, ServiceRequest, UserProfile, UserSettings


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'service_type', 'priority', 'status', 'owner', 'assigned_to', 'updated_at')
    list_filter = ('status', 'service_type', 'priority')
    search_fields = ('title', 'description', 'owner__username')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'author', 'is_internal', 'created_at')


@admin.register(ChangeHistory)
class ChangeHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'field_name', 'actor', 'created_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department')


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'items_per_page')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'username_snapshot', 'ip_address', 'method', 'path', 'status_code', 'request_id')
    list_filter = ('status_code', 'method', 'success')
