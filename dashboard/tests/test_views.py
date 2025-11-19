from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardHtmlTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='frontuser', password='123')
        self.client.login(username='frontuser', password='123')

    def test_dashboard_template_coverage(self):
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')