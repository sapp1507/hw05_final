from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class StaticURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_author = User.objects.create_user(username='test_user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='test_text ' * 20
        )
        cls.template_list = {
            'index': 'posts/index.html',
            'group': 'posts/group_list.html',
            'profile': 'posts/profile.html',
            'post_detail': 'posts/post_detail.html',
            'post_create': 'posts/post_create.html',
        }
        check_post_id = cls.post.id
        cls.address_list = {
            'index': '/',
            'group': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.user_author}/',
            'post_detail': f'/posts/{check_post_id}/',
            'post_edit': f'/posts/{check_post_id}/edit/',
            'post_create': '/create/',
            'login_redirect': '/auth/login/?next=',
            'unexciting_page': '/unexciting_page/',
            'tech': '/about/tech/',
            'author': '/about/author/',
        }

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_urls_uses_correct_template(self):
        template_url_names = {
            self.template_list['index']: self.address_list['index'],
            self.template_list['group']: self.address_list['group'],
            self.template_list['profile']: self.address_list['profile'],
            self.template_list['post_detail']: self.address_list[
                'post_detail'],
            self.template_list['post_create']: {
                self.author_client: self.address_list['post_edit'],
                self.authorized_client: self.address_list['post_create'],
            },
        }
        for template, address in template_url_names.items():
            with self.subTest(address=address):
                if type(address) is dict:
                    for client, page in address.items():
                        with self.subTest(client=client):
                            response = client.get(page)
                            self.assertTemplateUsed(response, template)
                else:
                    response = self.client.get(address)
                    self.assertTemplateUsed(
                        response,
                        template,
                        f'Не правильный шаблон страницы {address}, ожидался '
                        f'шаблон {template}'
                    )

    def test_urls_redirect(self):
        address_list = {
            self.address_list['post_edit']: {
                self.client:
                    f'{self.address_list["login_redirect"]}'
                    f'{self.address_list["post_edit"]}',
                self.authorized_client: self.address_list['post_detail']
            },
            self.address_list['post_create']:
                f'{self.address_list["login_redirect"]}'
                f'{self.address_list["post_create"]}',
        }
        for address, redirect in address_list.items():
            if type(redirect) is dict:
                for client, redirect_page in redirect.items():
                    with self.subTest(client=client):
                        response = client.get(address, follow=True)
                        self.assertRedirects(response, redirect_page)
            else:
                with self.subTest(address=address):
                    response = self.client.get(address, follow=True)
                    self.assertRedirects(response, redirect)

    def test_urls_exists_at_desired_location(self):
        address_list = [
            self.address_list['index'],
            self.address_list['group'],
            self.address_list['profile'],
            self.address_list['post_detail'],
            self.address_list['post_edit'],
            self.address_list['post_create'],
        ]
        for address in address_list:
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_unexisting_page(self):
        response = self.client.get(self.address_list['unexciting_page'])
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
