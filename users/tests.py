from django.urls import reverse
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class UserAuthenticationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.forgot_url = reverse('forgot_password')
        self.reset_url = reverse('reset_password')

        self.valid_user_data = {
            "email": "TestUser@example.com",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User"
        }

    def test_registration_success(self):
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], True)
        self.assertEqual(response.data['message'], "Users Registered successfully")
        
        # Verify nested data array format: "data": [ { "id": X, "name": "...", "email": "..." } ]
        self.assertEqual(response.data['data'][0]['email'], "testuser@example.com")
        self.assertEqual(response.data['data'][0]['name'], "Test User")
        
        # Ensure no tokens are returned in the response
        self.assertNotIn('access', response.data['data'][0])
        self.assertNotIn('refresh', response.data['data'][0])

        # Verify in database
        self.assertTrue(User.objects.filter(email="testuser@example.com").exists())

    def test_registration_invalid_email(self):
        data = self.valid_user_data.copy()
        data['email'] = 'not-an-email'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)
        self.assertEqual(response.data['message'], "Email: Please enter a valid email address.")
        self.assertIsNone(response.data['data'])

    def test_registration_password_strength_failures(self):
        # 1. Too short (less than 6 characters)
        data = self.valid_user_data.copy()
        data['email'] = 'short@example.com'
        data['password'] = 'Ps1!s'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)
        self.assertIn('password', response.data['message'].lower())

        # 2. No lowercase
        data['email'] = 'nolower@example.com'
        data['password'] = 'PASSWORD123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)

        # 3. No uppercase
        data['email'] = 'noupper@example.com'
        data['password'] = 'password123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)

        # 4. No number
        data['email'] = 'nonumber@example.com'
        data['password'] = 'Password!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)

        # 5. No special char
        data['email'] = 'nospecial@example.com'
        data['password'] = 'Password123'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)

    def test_login_success(self):
        user = User.objects.create_user(email="login@example.com", password="Password123!")
        login_data = {
            "email": "login@example.com",
            "password": "Password123!"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

    def test_login_case_insensitivity(self):
        user = User.objects.create_user(email="login@example.com", password="Password123!")
        # Login with mixed case email
        login_data = {
            "email": "LoGiN@ExAmPlE.CoM",
            "password": "Password123!"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        self.assertIn('access', response.data['data'])

    def test_login_fail(self):
        user = User.objects.create_user(email="login@example.com", password="Password123!")
        login_data = {
            "email": "login@example.com",
            "password": "WrongPassword"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], False)
        self.assertIn('message', response.data)

    def test_token_refresh(self):
        user = User.objects.create_user(email="refresh@example.com", password="Password123!")
        login_data = {"email": "refresh@example.com", "password": "Password123!"}
        login_response = self.client.post(self.login_url, login_data, format='json')
        
        refresh_token = login_response.data['data']['refresh']
        response = self.client.post(self.refresh_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        self.assertIn('access', response.data['data'])

    @override_settings(DEBUG=True)
    def test_forgot_password_success(self):
        user = User.objects.create_user(email="forgot@example.com", password="Password123!")
        response = self.client.post(self.forgot_url, {"email": "forgot@example.com"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        self.assertIn('message', response.data)
        self.assertIn('_debug', response.data['data'])  # DEBUG mode returns code details under data
        self.assertIn('code', response.data['data']['_debug'])
        self.assertEqual(len(response.data['data']['_debug']['code']), 6)

    def test_reset_password_success(self):
        user = User.objects.create_user(email="reset@example.com", password="Password123!")
        
        # Request forgot password to generate the 6-digit code
        forgot_response = self.client.post(self.forgot_url, {"email": "reset@example.com"}, format='json')
        self.assertEqual(forgot_response.status_code, status.HTTP_200_OK)
        
        from users.models import PasswordResetCode
        reset_code = PasswordResetCode.objects.filter(user=user).latest('created_at')

        reset_payload = {
            "email": "reset@example.com",
            "code": reset_code.code,
            "password": "NewPassword123!"
        }
        response = self.client.post(self.reset_url, reset_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        self.assertEqual(response.data['message'], "Your password has been successfully reset.")
        
        # Verify login works with new password
        login_data = {"email": "reset@example.com", "password": "NewPassword123!"}
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data['status'], True)

    def test_reset_password_invalid_code(self):
        user = User.objects.create_user(email="reset_fail@example.com", password="Password123!")
        self.client.post(self.forgot_url, {"email": "reset_fail@example.com"}, format='json')

        reset_payload = {
            "email": "reset_fail@example.com",
            "code": "000000",  # incorrect code
            "password": "NewPassword123!"
        }
        response = self.client.post(self.reset_url, reset_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], False)
        self.assertEqual(response.data['message'], "Invalid verification code.")




class AdminUserManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@example.com", password="Password123!")
        self.normal_user = User.objects.create_user(email="normal@example.com", password="Password123!")
        self.admin_users_url = '/api/admin/users/'

    def test_admin_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.admin_users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        # Should return at least the 2 users created
        self.assertGreaterEqual(len(response.data['data']), 2)

    def test_normal_user_blocked_from_admin_list(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.admin_users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['status'], False)

    def test_admin_create_user(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "email": "createdbyadmin@example.com",
            "password": "Password123!",
            "first_name": "AdminCreated",
            "is_staff": True
        }
        response = self.client.post(self.admin_users_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], True)
        self.assertEqual(response.data['data']['email'], "createdbyadmin@example.com")
        self.assertEqual(response.data['data']['is_staff'], True)

    def test_admin_delete_user(self):
        user_to_delete = User.objects.create_user(email="todelete@example.com", password="Password123!")
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"{self.admin_users_url}{user_to_delete.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Rendered returns 200 with deleted envelope, not 204
        self.assertEqual(response.data['status'], True)
        self.assertEqual(response.data['message'], "Deleted successfully")
        self.assertFalse(User.objects.filter(email="todelete@example.com").exists())
