from django.contrib.auth.models import User
from rest_framework import serializers

from .models import AuditLog, ChangeHistory, Comment, RequestStatus, RoleChoices, ServiceRequest, UserSettings, get_user_role


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']


class ServiceRequestSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    due_date = serializers.DateField(required=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        source='assigned_to',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ServiceRequest
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        if request and getattr(request.user, 'is_authenticated', False):
            role = get_user_role(request.user)
            if role == RoleChoices.USER:
                validated_data['status'] = RequestStatus.SUBMITTED
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and getattr(request.user, 'is_authenticated', False):
            role = get_user_role(request.user)
            if role == RoleChoices.USER:
                incoming_status = validated_data.get('status', instance.status)
                if incoming_status != instance.status:
                    raise serializers.ValidationError({'status': 'Обычный пользователь не может менять статус заявки.'})
                validated_data['status'] = instance.status
        if 'attachment' in validated_data and validated_data['attachment'] in {None, ''} and instance.attachment:
            instance.attachment.delete(save=False)
        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'

    def validate_is_internal(self, value):
        request = self.context.get('request')
        if not request or not getattr(request.user, 'is_authenticated', False):
            return False
        role = get_user_role(request.user)
        if value and role == RoleChoices.USER:
            raise serializers.ValidationError('Внутренние комментарии доступны только модераторам и администраторам.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and getattr(request.user, 'is_authenticated', False):
            role = get_user_role(request.user)
            if role == RoleChoices.USER:
                validated_data['is_internal'] = False
        return super().create(validated_data)


class ChangeHistorySerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = ChangeHistory
        fields = '__all__'


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = '__all__'
