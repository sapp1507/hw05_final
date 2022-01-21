from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class UsersURLTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(user)
