from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from datetime import date
from rest_framework.test import APIClient

from .models import AuditLog, Comment, RequestStatus, RoleChoices, ServiceRequest


class MiddlewareTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='employee', password='portal12345')
        self.user.profile.role = RoleChoices.USER
        self.user.profile.save()

        self.moderator = User.objects.create_user(username='moderator', password='portal12345')
        self.moderator.profile.role = RoleChoices.MODERATOR
        self.moderator.profile.save()

        self.request_obj = ServiceRequest.objects.create(
            title='Access to VPN',
            description='Need VPN access for remote work.',
            service_type='it',
            priority='medium',
            status=RequestStatus.SUBMITTED,
            owner=self.user,
        )

    def test_request_id_header_is_returned(self):
        client = Client()
        client.force_login(self.user)
        response = client.get(reverse('request-list'), HTTP_X_REQUEST_ID='lab-123')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Request-ID'], 'lab-123')

    def test_auto_user_detection_by_header_creates_audit_log(self):
        client = Client()
        response = client.get(reverse('request-list'), HTTP_X_PORTAL_USER='employee')
        self.assertEqual(response.status_code, 200)
        log = AuditLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.username_snapshot, 'employee')

    def test_rate_limit_returns_429(self):
        from django.test import override_settings

        with override_settings(PORTAL_RATE_LIMITS={'/': (1, 60)}):
            client = Client()
            client.force_login(self.user)
            first = client.get(reverse('request-list'))
            second = client.get(reverse('request-list'))
            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 429)

    def test_regular_user_can_create_request_without_status(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(
            reverse('request-create'),
            {
                'title': 'New laptop',
                'description': 'Need a replacement laptop.',
                'service_type': 'it',
                'priority': 'medium',
                'assigned_to': '',
                'due_date': '2026-06-30',
                'attachment': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        created = ServiceRequest.objects.latest('created_at')
        self.assertEqual(created.owner, self.user)
        self.assertEqual(created.status, RequestStatus.SUBMITTED)

    def test_regular_user_cannot_create_request_without_due_date(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(
            reverse('request-create'),
            {
                'title': 'No date',
                'description': 'Missing due date.',
                'service_type': 'it',
                'priority': 'medium',
                'assigned_to': '',
                'attachment': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ServiceRequest.objects.filter(title='No date').exists())

    def test_regular_user_cannot_change_status_in_html_edit(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(
            reverse('request-update', args=[self.request_obj.pk]),
            {
                'title': self.request_obj.title,
                'description': self.request_obj.description,
                'service_type': self.request_obj.service_type,
                'priority': self.request_obj.priority,
                'assigned_to': '',
                'due_date': '2026-06-30',
                'attachment': '',
                'status': 'approved',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, RequestStatus.SUBMITTED)

    def test_regular_user_cannot_change_status_via_api(self):
        client = APIClient()
        client.force_login(self.user)
        response = client.patch(
            reverse('api-requests-detail', args=[self.request_obj.pk]),
            {'status': 'approved'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, RequestStatus.SUBMITTED)

    def test_attachment_can_be_cleared_in_html_edit(self):
        self.request_obj.attachment.save(
            'guide.txt',
            SimpleUploadedFile('guide.txt', b'demo content', content_type='text/plain'),
            save=True,
        )

        client = Client()
        client.force_login(self.user)
        response = client.post(
            reverse('request-update', args=[self.request_obj.pk]),
            {
                'title': self.request_obj.title,
                'description': self.request_obj.description,
                'service_type': self.request_obj.service_type,
                'priority': self.request_obj.priority,
                'assigned_to': '',
                'due_date': '2026-06-30',
                'clear_attachment': '1',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.request_obj.refresh_from_db()
        self.assertFalse(self.request_obj.attachment)

    def test_edit_form_prefills_due_date(self):
        self.request_obj.due_date = date(2026, 6, 30)
        self.request_obj.save(update_fields=['due_date'])

        client = Client()
        client.force_login(self.user)
        response = client.get(reverse('request-update', args=[self.request_obj.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="2026-06-30"', html=False)

    def test_regular_user_cannot_create_internal_comment_in_html(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(
            reverse('request-detail', args=[self.request_obj.pk]),
            {'text': 'Public note', 'is_internal': 'on'},
        )
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.latest('created_at')
        self.assertFalse(comment.is_internal)
        self.assertEqual(comment.author, self.user)

    def test_regular_user_cannot_create_internal_comment_via_api(self):
        client = APIClient()
        client.force_login(self.user)
        response = client.post(
            reverse('api-comments-list'),
            {'request': self.request_obj.pk, 'text': 'API note', 'is_internal': True},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('is_internal', response.data)

    def test_moderator_can_create_internal_comment_via_api(self):
        client = APIClient()
        client.force_login(self.moderator)
        response = client.post(
            reverse('api-comments-list'),
            {'request': self.request_obj.pk, 'text': 'Internal note', 'is_internal': True},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        comment = Comment.objects.latest('created_at')
        self.assertTrue(comment.is_internal)
        self.assertEqual(comment.author, self.moderator)
