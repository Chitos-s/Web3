from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .forms import CommentForm, RequestFilterForm, ServiceRequestForm, UserSettingsForm
from .models import AuditLog, ChangeHistory, Comment, RequestStatus, RoleChoices, ServiceRequest, UserSettings, get_user_role
from .permissions import ModeratorOrAdminPermission, RequestAccessPermission, ChangeHistoryPermission
from .serializers import AuditLogSerializer, ChangeHistorySerializer, CommentSerializer, ServiceRequestSerializer, UserSettingsSerializer


@login_required
def request_list(request):
    queryset = ServiceRequest.objects.select_related('owner', 'assigned_to').all()
    role = get_user_role(request.user)
    if role not in {RoleChoices.MODERATOR, RoleChoices.ADMIN}:
        queryset = queryset.filter(owner=request.user)
    form = RequestFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data['status']:
            queryset = queryset.filter(status=form.cleaned_data['status'])
        if form.cleaned_data['service_type']:
            queryset = queryset.filter(service_type=form.cleaned_data['service_type'])
        if form.cleaned_data['priority']:
            queryset = queryset.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data['overdue_only']:
            queryset = queryset.filter(due_date__lt=timezone.localdate()).exclude(status=RequestStatus.CLOSED)
        if form.cleaned_data['search']:
            term = form.cleaned_data['search']
            queryset = queryset.filter(Q(title__icontains=term) | Q(description__icontains=term))
    return render(request, 'requests_app/request_list.html', {'form': form, 'requests': queryset})


@login_required
def request_detail(request, pk):
    obj = get_object_or_404(ServiceRequest.objects.select_related('owner', 'assigned_to'), pk=pk)
    role = get_user_role(request.user)
    if role not in {RoleChoices.MODERATOR, RoleChoices.ADMIN} and obj.owner_id != request.user.id:
        return HttpResponseForbidden('Недостаточно прав.')
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    settings_obj.last_seen_request = obj
    settings_obj.save(update_fields=['last_seen_request'])
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if role == RoleChoices.USER:
            comment_form.fields.pop('is_internal', None)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.request = obj
            comment.author = request.user
            if role == RoleChoices.USER:
                comment.is_internal = False
            comment.save()
            messages.success(request, 'Комментарий добавлен.')
            return redirect(obj.get_absolute_url())
    else:
        comment_form = CommentForm()
        if role == RoleChoices.USER:
            comment_form.fields.pop('is_internal', None)
    visible_comments = obj.comments.all()
    if role == RoleChoices.USER:
        visible_comments = visible_comments.filter(is_internal=False)
    return render(request, 'requests_app/request_detail.html', {'request_obj': obj, 'comment_form': comment_form, 'visible_comments': visible_comments})


@login_required
def request_create(request):
    form = ServiceRequestForm(request.POST or None, request.FILES or None)
    form.fields['assigned_to'].queryset = User.objects.filter(profile__role__in=[RoleChoices.MODERATOR, RoleChoices.ADMIN])
    user_role = get_user_role(request.user)
    if user_role == RoleChoices.USER:
        form.fields['assigned_to'].required = False
        form.fields['assigned_to'].disabled = True
        form.fields.pop('status', None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.owner = request.user
        obj._history_actor = request.user
        if user_role == RoleChoices.USER:
            obj.status = RequestStatus.SUBMITTED
        obj.save()
        messages.success(request, 'Заявка создана.')
        return redirect(obj.get_absolute_url())
    return render(request, 'requests_app/request_form.html', {'form': form, 'is_create': True})


@login_required
def request_update(request, pk):
    obj = get_object_or_404(ServiceRequest, pk=pk)
    if not obj.editable_by(request.user):
        return HttpResponseForbidden('Редактирование недоступно для этой заявки.')
    form = ServiceRequestForm(request.POST or None, request.FILES or None, instance=obj)
    form.fields['assigned_to'].queryset = User.objects.filter(profile__role__in=[RoleChoices.MODERATOR, RoleChoices.ADMIN])
    user_role = get_user_role(request.user)
    if user_role == RoleChoices.USER:
        form.fields['assigned_to'].disabled = True
        form.fields.pop('status', None)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        updated._history_actor = request.user
        if user_role == RoleChoices.USER:
            updated.status = obj.status
        if request.POST.get('clear_attachment') == '1':
            if obj.attachment:
                obj.attachment.delete(save=False)
            updated.attachment = None
        updated.save()
        messages.success(request, 'Заявка обновлена.')
        return redirect(updated.get_absolute_url())
    return render(request, 'requests_app/request_form.html', {'form': form, 'is_create': False, 'request_obj': obj})


@login_required
def moderator_panel(request):
    role = get_user_role(request.user)
    if role not in {RoleChoices.MODERATOR, RoleChoices.ADMIN}:
        return HttpResponseForbidden('Только для модераторов и администраторов.')
    queue = ServiceRequest.objects.exclude(status=RequestStatus.CLOSED).select_related('owner', 'assigned_to')[:20]
    latest_audit = AuditLog.objects.select_related('user')[:20]
    active_tab = request.GET.get('tab', 'queue')
    if active_tab not in {'queue', 'audit'}:
        active_tab = 'queue'
    return render(request, 'requests_app/moderator_panel.html', {
        'queue': queue,
        'latest_audit': latest_audit,
        'active_tab': active_tab,
    })


@login_required
def settings_view(request):
    obj, _ = UserSettings.objects.get_or_create(user=request.user)
    form = UserSettingsForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Настройки сохранены.')
        return redirect('user-settings')
    return render(request, 'requests_app/settings.html', {'form': form})


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.select_related('owner', 'assigned_to').all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [RequestAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_user_role(self.request.user)
        if role not in {RoleChoices.MODERATOR, RoleChoices.ADMIN}:
            qs = qs.filter(owner=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        obj = serializer.instance
        if not obj.editable_by(self.request.user):
            raise permissions.PermissionDenied('Редактирование недоступно для этой заявки.')
        serializer.validated_data['_history_actor'] = self.request.user
        serializer.save()

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        obj = self.get_object()
        status_value = request.data.get('status')
        if status_value not in RequestStatus.values or not obj.can_change_status(request.user):
            return Response({'detail': 'Статус изменить нельзя.'}, status=400)
        obj.status = status_value
        obj._history_actor = request.user
        obj.save()
        return Response(self.get_serializer(obj).data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author', 'request').all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_user_role(self.request.user)
        if role == RoleChoices.USER:
            qs = qs.filter(request__owner=self.request.user, is_internal=False)
        return qs

    def perform_create(self, serializer):
        request_obj = serializer.validated_data['request']
        role = get_user_role(self.request.user)
        if role == RoleChoices.USER and request_obj.owner_id != self.request.user.id:
            raise permissions.PermissionDenied('Нельзя комментировать чужую заявку.')
        if role == RoleChoices.USER:
            serializer.validated_data['is_internal'] = False
        serializer.save(author=self.request.user)


class ChangeHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChangeHistory.objects.select_related('actor', 'request').all()
    serializer_class = ChangeHistorySerializer
    permission_classes = [ChangeHistoryPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        role = get_user_role(self.request.user)
        request_id = self.request.query_params.get('request_id')

        if request_id:
            qs = qs.filter(request_id=request_id)

        if role == RoleChoices.USER:
            qs = qs.filter(request__owner=self.request.user)

        return qs


class UserSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = UserSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSettings.objects.filter(user=self.request.user)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [ModeratorOrAdminPermission]
