from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class RoleChoices(models.TextChoices):
    USER = 'user', 'Пользователь'
    MODERATOR = 'moderator', 'Модератор'
    ADMIN = 'admin', 'Администратор'


class RequestStatus(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    SUBMITTED = 'submitted', 'Новая'
    IN_REVIEW = 'in_review', 'На рассмотрении'
    APPROVED = 'approved', 'Одобрена'
    REJECTED = 'rejected', 'Отклонена'
    CLOSED = 'closed', 'Закрыта'


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.USER)
    department = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'


class UserSettings(models.Model):
    THEME_CHOICES = [
        ('light', 'Светлая'),
        ('dark', 'Тёмная'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portal_settings', verbose_name='Пользователь')
    theme = models.CharField('Тема интерфейса', max_length=20, choices=THEME_CHOICES, default='light')
    items_per_page = models.PositiveIntegerField('Записей на странице', default=10)
    last_seen_request = models.ForeignKey('ServiceRequest', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Последняя заявка')

    def __str__(self):
        return f'Настройки {self.user.username}'


class ServiceRequest(models.Model):
    SERVICE_CHOICES = [
        ('it', 'IT-поддержка'),
        ('hr', 'HR-сервис'),
        ('finance', 'Финансовый сервис'),
        ('legal', 'Юридический сервис'),
        ('office', 'Офисная инфраструктура'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    service_type = models.CharField('Тип сервиса', max_length=20, choices=SERVICE_CHOICES)
    priority = models.CharField('Приоритет', max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField('Статус', max_length=20, choices=RequestStatus.choices, default=RequestStatus.DRAFT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests', verbose_name='Владелец')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_requests',
        verbose_name='Ответственный',
    )
    attachment = models.FileField('Вложение', upload_to='attachments/', blank=True, null=True)
    due_date = models.DateField('Срок исполнения', null=True, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    last_status_changed_at = models.DateTimeField('Дата изменения статуса', auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('request-detail', args=[self.pk])

    @property
    def is_locked_for_owner(self):
        return self.status in {RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CLOSED}

    def editable_by(self, user):
        if not user.is_authenticated:
            return False
        if user.is_superuser or get_user_role(user) == RoleChoices.ADMIN:
            return True
        if get_user_role(user) == RoleChoices.MODERATOR:
            return self.status != RequestStatus.CLOSED
        if self.owner_id != user.id:
            return False
        return True

    def can_change_status(self, user):
        if not user.is_authenticated:
            return False
        role = get_user_role(user)
        if user.is_superuser or role == RoleChoices.ADMIN:
            return True
        if role == RoleChoices.MODERATOR:
            return self.status != RequestStatus.CLOSED
        return self.owner_id == user.id and self.status in {RequestStatus.DRAFT, RequestStatus.SUBMITTED}


class Comment(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='request_comments')
    text = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Комментарий #{self.pk} к заявке #{self.request_id}'


class ChangeHistory(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='history')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.request_id}: {self.field_name}'


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    username_snapshot = models.CharField(max_length=150, blank=True)
    request_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    method = models.CharField(max_length=16)
    path = models.CharField(max_length=255)
    action = models.CharField(max_length=120, blank=True)
    status_code = models.PositiveIntegerField(default=200)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.method} {self.path} [{self.status_code}]'


def get_user_role(user: User | None) -> str:
    if not user or not user.is_authenticated:
        return RoleChoices.USER
    if user.is_superuser:
        return RoleChoices.ADMIN
    profile = getattr(user, 'profile', None)
    if profile:
        return profile.role
    return RoleChoices.USER
