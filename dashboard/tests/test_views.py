from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardHtmlTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='frontuser', password='password123')
        self.client.force_login(self.user)

    def test_dashboard_template_coverage(self):
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')