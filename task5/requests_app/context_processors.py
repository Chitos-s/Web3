from .models import RoleChoices, UserSettings, get_user_role


def portal_context(request):
    role = get_user_role(getattr(request, 'user', None))
    portal_theme = 'light'
    if getattr(request, 'user', None) and request.user.is_authenticated:
        try:
            portal_theme = request.user.portal_settings.theme
        except UserSettings.DoesNotExist:
            portal_theme = 'light'
    return {
        'portal_role': role,
        'portal_role_label': dict(RoleChoices.choices).get(role, 'Пользователь'),
        'portal_theme': portal_theme,
    }
