from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import ChangeHistory, ServiceRequest, UserProfile, UserSettings


TRACKED_FIELDS = ['title', 'description', 'service_type', 'priority', 'status', 'assigned_to_id', 'due_date']


@receiver(pre_save, sender=ServiceRequest)
def capture_request_changes(sender, instance, **kwargs):
    if not instance.pk:
        return
    previous = sender.objects.filter(pk=instance.pk).first()
    if previous is None:
        return
    for field in TRACKED_FIELDS:
        old_value = getattr(previous, field, '')
        new_value = getattr(instance, field, '')
        if old_value != new_value:
            ChangeHistory.objects.create(
                request=instance,
                actor=getattr(instance, '_history_actor', None),
                field_name=field,
                old_value=str(old_value),
                new_value=str(new_value),
            )
    if previous.status != instance.status:
        instance.last_status_changed_at = timezone.now()


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        UserSettings.objects.get_or_create(user=instance)
from django.utils import timezone
