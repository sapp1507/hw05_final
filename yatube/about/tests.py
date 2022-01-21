from django.test import TestCase
from http import HTTPStatus


class StaticURLTest(TestCase):

    def test_urls_exists_at_desired_location(self):
        address_list = [
            '/',
            '/about/author/',
            '/about/tech/'
        ]
        for address in address_list:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
