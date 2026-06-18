from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Comment, RequestStatus, ServiceRequest, UserSettings


class RussianAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label='Пароль', strip=False, widget=forms.PasswordInput)


class RequestFilterForm(forms.Form):
    status = forms.ChoiceField(
        label='Статус',
        choices=[('', 'Все статусы'), *RequestStatus.choices],
        required=False,
    )
    service_type = forms.ChoiceField(
        label='Тип сервиса',
        choices=[('', 'Все сервисы'), *ServiceRequest.SERVICE_CHOICES],
        required=False,
    )
    priority = forms.ChoiceField(
        label='Приоритет',
        choices=[('', 'Любой приоритет'), *ServiceRequest.PRIORITY_CHOICES],
        required=False,
    )
    overdue_only = forms.BooleanField(required=False, label='Только просроченные')
    search = forms.CharField(required=False, label='Поиск')


class ServiceRequestForm(forms.ModelForm):
    due_date = forms.DateField(
        label='Срок исполнения',
        required=True,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
    )

    class Meta:
        model = ServiceRequest
        fields = ['title', 'description', 'service_type', 'priority', 'status', 'assigned_to', 'due_date', 'attachment']
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'service_type': 'Тип сервиса',
            'priority': 'Приоритет',
            'status': 'Статус',
            'assigned_to': 'Ответственный',
            'attachment': 'Вложение',
        }
        help_texts = {
            'status': 'Статус заявки внутри портала.',
            'assigned_to': 'Выберите исполнителя, если заявка должна быть назначена.',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'attachment': forms.FileInput(),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'is_internal']
        labels = {
            'text': 'Текст',
            'is_internal': 'Внутренний комментарий',
        }
        widgets = {'text': forms.Textarea(attrs={'rows': 3})}


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['theme', 'items_per_page']
        labels = {
            'theme': 'Тема интерфейса',
            'items_per_page': 'Записей на странице',
        }
        help_texts = {
            'theme': 'Выберите одну из доступных тем.',
            'items_per_page': 'Чем меньше, тем меньше записей показывается на странице.',
        }
        widgets = {
            'theme': forms.Select(),
            'items_per_page': forms.NumberInput(attrs={'min': 1, 'max': 100}),
        }
