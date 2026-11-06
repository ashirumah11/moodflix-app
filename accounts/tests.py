from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile

@override_settings(
    TMDB_API_KEY='',
    TMDB_READ_ACCESS_TOKEN='',
    TMDB_API_READ_ACCESS_TOKEN='',
)
class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='cinemafan',
            email='fan@example.com',
            password='Password123!',
            first_name='Alex',
            last_name='Ross'
        )

    def test_registration_success(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecretPass456!',
            'password2': 'SecretPass456!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_u = User.objects.get(username='newuser')
        self.assertTrue(hasattr(new_u, 'profile'))

    def test_registration_duplicate_email(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'anotheruser',
            'email': 'fan@example.com',  # duplicate email
            'password1': 'SecretPass456!',
            'password2': 'SecretPass456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anotheruser').exists())

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'cinemafan',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'cinemafan',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_logout(self):
        self.client.login(username='cinemafan', password='Password123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_profile_protected_for_anonymous(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_profile_view_authenticated(self):
        self.client.login(username='cinemafan', password='Password123!')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cinemafan')

    def test_profile_update(self):
        self.client.login(username='cinemafan', password='Password123!')
        response = self.client.post(reverse('accounts:profile_update'), {
            'first_name': 'Alexander',
            'last_name': 'Rossi',
            'email': 'alex@example.com',
            'bio': 'Lover of sci-fi and thrillers.',
            'preferred_genres': 'Sci-Fi, Adventure',
            'preferred_moods_select': ['happy', 'adventurous'],
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Alexander')
        self.assertEqual(self.user.profile.bio, 'Lover of sci-fi and thrillers.')
        self.assertIn('adventurous', self.user.profile.preferred_moods)
