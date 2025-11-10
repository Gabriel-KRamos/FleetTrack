from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .forms import SignUpForm
from .models import UserProfile

class AccountsAppTests(TestCase):

    def setUp(self):
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.form_data = {
            'company_name': 'Empresa de Teste',
            'cnpj': '12.345.678/0001-99',
            'first_name': 'Usuário Teste',
            'username': 'teste@email.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }

    def test_signup_page_status_code(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)

    def test_signup_page_uses_correct_template(self):
        response = self.client.get(self.signup_url)
        self.assertTemplateUsed(response, 'accounts/signup.html')
        
    def test_signup_form_success(self):
        user_count_before = User.objects.count()
        
        response = self.client.post(self.signup_url, data=self.form_data)
        
        self.assertRedirects(response, self.login_url)
        
        self.assertEqual(User.objects.count(), user_count_before + 1)
        new_user = User.objects.get(username='teste@email.com')
        self.assertEqual(new_user.first_name, 'Usuário Teste')
        self.assertTrue(new_user.userprofile.cnpj, '12345678000199')
        self.assertEqual(new_user.userprofile.company_name, 'Empresa de Teste')

    def test_signup_form_password_mismatch(self):
        data = self.form_data.copy()
        data['confirm_password'] = 'PasswordErrado123!'
        
        response = self.client.post(self.signup_url, data=data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'As senhas não coincidem')
        
    def test_signup_form_duplicate_email(self):
        User.objects.create_user(username='teste@email.com', password='pw')
        
        response = self.client.post(self.signup_url, data=self.form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este endereço de email já está em uso')

    def test_signup_form_duplicate_cnpj(self):
        user1 = User.objects.create_user(username='user1@email.com', password='pw')
        UserProfile.objects.create(user=user1, cnpj='12345678000199')
        
        data = self.form_data.copy()
        data['username'] = 'user2@email.com'
        
        response = self.client.post(self.signup_url, data=data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este CNPJ já está em uso')