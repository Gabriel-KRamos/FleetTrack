from django.test import TestCase
from django.urls import reverse

class AccountsAppTests(TestCase):

    def test_signup_page_status_code(self):
        """
        Verifica se a página de cadastro responde com o status code 200 (OK).
        """
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_signup_page_uses_correct_template(self):
        """
        Verifica se a view de cadastro está usando o template correto.
        """
        url = reverse('signup')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'accounts/signup.html')