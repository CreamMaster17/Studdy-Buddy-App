
#Run: python manage.py test apps.accounts

from django.test import TestCase
from django.contrib.auth import get_user_model, authenticate

from .models import UserProfile


User = get_user_model()


class TestsUserModel(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@email.com",
            password="testpass123"
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@email.com")
        self.assertTrue(user.check_password("testpass123"))

    def test_profile_created_automatically(self):
        user = User.objects.create_user(
            username="profileuser",
            email="profile@email.com",
            password="testpass123"
        )

        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.user, user)


class TestsUserProfile(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="profiletest",
            email="profiletest@email.com",
            password="testpass123"
        )

    def test_profile_exists_after_user_creation(self):
        profile = self.user.profile

        self.assertIsInstance(profile, UserProfile)

    def test_update_profile_fields(self):
        profile = self.user.profile

        profile.nickname = "Study Buddy"
        profile.save()

        self.assertEqual(self.user.profile.nickname, "Study Buddy")

    def test_profile_string_representation(self):
        self.assertEqual(str(self.user.profile), self.user.username)


class TestsUserAuthentication(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@email.com",
            password="securepassword123"
        )

    def test_login_with_username(self):
        user = authenticate(
            username="testuser",
            email="test@email.com",
            password="securepassword123"
        )

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")

    def test_login_with_email(self):
        user = authenticate(
            username="testuser",
            email="test@email.com",
            password="securepassword123"
        )

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@email.com")

    def test_login_with_wrong_password(self):
        user = authenticate(
            username="testuser",
            email="test@email.com",
            password="wrongpassword123"
        )

        self.assertIsNone(user)

    def test_login_with_invalid_username_or_email(self):
        user = authenticate(
            username="doesnotexist",
            email="not@email.com",
            password="securepassword123"
        )
        

        self.assertIsNone(user)


class TestsUserLogout(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="logoutuser",
            password="securepassword123"
        )

    def test_user_can_logout(self):
        login = self.client.login(
            username="logoutuser",
            password="securepassword123"
        )

        self.assertTrue(login)

        # Confirm user is logged in (this was giving me trouble)
        response = self.client.get("/")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        response = self.client.post("/logout/")
        self.assertEqual(response.status_code, 302)

        response = self.client.get("/")
        self.assertFalse(response.wsgi_request.user.is_authenticated)