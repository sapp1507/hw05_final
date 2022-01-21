from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings


from ..models import Post, Group, Follow

User = get_user_model()


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_author = User.objects.create_user(username='test_user_author')
        cls.user_author_two = User.objects.create_user(
            username='test_user_author_two')
        cls.group_one = Group.objects.create(
            title='test_group_one',
            description='test_desc_one',
            slug='test_slug_one'
        )
        cls.group_two = Group.objects.create(
            title='test_group_two',
            description='test_desc_two',
            slug='test_slug_two'
        )
        image_byte = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name='image.jpg',
            content=image_byte,
            content_type='image/jpg'
        )
        for i in range(13):
            Post.objects.create(
                text=f'test text post number {i}',
                author=cls.user_author,
                group=cls.group_one,
                image=image
            )
        for i in range(10):
            Post.objects.create(
                text=f'test text post number {i}',
                author=cls.user_author_two,
                group=cls.group_two,
                image=image
            )
        check_post_id = 1
        kwargs_user = {'username': cls.user_author}
        cls.reverse_list = {
            'index': reverse('posts:index'),
            'group_one': reverse('posts:group_posts_page',
                                 kwargs={'slug': cls.group_one.slug}),
            'group_two': reverse('posts:group_posts_page',
                                 kwargs={'slug': cls.group_two.slug}),
            'profile': reverse('posts:profile', kwargs=kwargs_user),
            'post_detail': reverse('posts:post_detail',
                                   kwargs={'post_id': check_post_id}),
            'post_edit': reverse('posts:post_edit',
                                 kwargs={'post_id': check_post_id}),
            'post_create': reverse('posts:post_create'),
            'post_follow': reverse('posts:profile_follow', kwargs=kwargs_user),
            'post_unfollow': reverse('posts:profile_unfollow',
                                     kwargs=kwargs_user),
            'post_follow_index': reverse('posts:follow_index')
        }
        cls.post_count_page = settings.POST_COUNT_DISPLAY

    def setUp(self):
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client.force_login(self.user_author)

    def test_pages_uses_correct_template(self):
        template_pages_names = {
            'posts/index.html': self.reverse_list['index'],
            'posts/group_list.html': self.reverse_list['group_one'],
            'posts/profile.html': self.reverse_list['profile'],
            'posts/post_detail.html': self.reverse_list['post_detail'],
            'posts/post_create.html': {
                self.author_client: self.reverse_list['post_edit'],
                self.authorized_client: self.reverse_list['post_create']
            }
        }

        for template, reverse_name in template_pages_names.items():
            if type(reverse_name) is dict:
                for client, rev_name in reverse_name.items():
                    with self.subTest(rev_name=rev_name):
                        response = client.get(rev_name)
                        self.assertTemplateUsed(response, template)
            else:
                with self.subTest(reverse_name=reverse_name):
                    response = self.client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def test_pages_paginator(self):
        count_post_index = Post.objects.count()
        if count_post_index < self.post_count_page:
            count_post_last_page_index = count_post_index
        else:
            count_post_last_page_index = (count_post_index %
                                          self.post_count_page)

        count_post_group = Post.objects.filter(group=self.group_one).count()
        if count_post_group < self.post_count_page:
            count_post_last_page_group = count_post_group
        else:
            count_post_last_page_group = (count_post_group %
                                          self.post_count_page)

        count_post_profile = Post.objects.filter(
            author=self.user_author).count()
        if count_post_profile < self.post_count_page:
            count_post_last_page_profile = count_post_profile
        else:
            count_post_last_page_profile = (count_post_profile %
                                            self.post_count_page)
        count_list = {
            'index': count_post_last_page_profile,
            'group': count_post_last_page_group,
            'profile': count_post_last_page_profile,
        }
        for page, count in count_list.items():
            with self.subTest(page=page):
                self.assertNotEqual(count_post_last_page_index,
                                    0,
                                    f'Тест провален! кол-во постов на '
                                    f'последней страницы {page} ровно '
                                    f'максимальному количеству постов на '
                                    f'странице. Измените кол-во постов в '
                                    f'тестовой базе для тестирования')

        last_page_index = count_post_index // self.post_count_page + 1
        last_page_group = count_post_group // self.post_count_page + 1
        last_page_profile = count_post_profile // self.post_count_page + 1
        pages = {
            'index': self.reverse_list['index'],
            'index_last':
                f'{self.reverse_list["index"]}?page={last_page_index}',
            'group': self.reverse_list['group_one'],
            'group_last':
                f'{self.reverse_list["group_one"]}?page={last_page_group}',
            'profile':
                self.reverse_list['profile'],
            'profile_last':
                f'{self.reverse_list["profile"]}?page={last_page_profile}',
        }

        for test, page in pages.items():
            response = self.client.get(page)
            if test == 'index_last':
                count_post_page = count_post_last_page_index
            elif test == 'group_last':
                count_post_page = count_post_last_page_group
            elif test == 'profile_last':
                count_post_page = count_post_last_page_profile
            else:
                count_post_page = self.post_count_page
            with self.subTest(page=page):
                self.assertEqual(
                    len(response.context.get('page_obj')),
                    count_post_page,
                    f'Неправильное кол-во постов на странице {page}'
                )

    def test_page_index_show_correct_context(self):
        response = self.client.get(self.reverse_list['index'])
        first_obj = response.context['page_obj'][0]
        title = response.context.get('title')
        expected_title = 'Главная страница'
        expected_post = Post.objects.all().order_by('-id')[0]
        self.assertEqual(
            title,
            expected_title,
            'Не правильный заголовок главной страницы'
        )
        self.assertEqual(
            first_obj.text,
            expected_post.text
        )
        self.assertEqual(
            first_obj.author,
            expected_post.author,
            'Не правильный автор паста'
        )
        self.assertEqual(
            first_obj.image,
            expected_post.image,
            'Нет картинки'
        )

    def test_page_group_show_correct_context(self):
        response = self.client.get(self.reverse_list['group_one'])
        first_obj = response.context['page_obj'][0]
        title = response.context.get('group').title
        expected_post = Post.objects.filter(
            group=self.group_one).order_by('-id')[0]
        self.assertEqual(
            title,
            expected_post.group.title,
            'Не правильное название заголовка группы',
        )
        self.assertEqual(
            first_obj.text,
            expected_post.text,
        )
        self.assertEqual(
            first_obj.author,
            expected_post.author,
            'Не правильный автор поста',
        )
        self.assertEqual(
            first_obj.group,
            expected_post.group,
            'Ожидалась другая группа',
        )
        self.assertEqual(
            first_obj.image,
            expected_post.image,
            'Нет картинки',
        )

    def test_page_profile_show_correct_context(self):
        response = self.client.get(self.reverse_list['profile'])
        first_obj = response.context['page_obj'][0]
        expected_post = Post.objects.filter(
            author=self.user_author).order_by('-id')[0]
        self.assertEqual(
            first_obj.text,
            expected_post.text,
        )
        self.assertEqual(
            first_obj.author,
            self.user_author,
            'Не правильный автор поста'
        )
        self.assertEqual(
            first_obj.image,
            expected_post.image,
            'нет Картинки'
        )

    def test_page_post_detail_show_correct_context(self):
        response = self.client.get(self.reverse_list['post_detail'])
        title = response.context.get('title')
        post_text = response.context.get('post').text
        self.assertEqual(
            len(title),
            len(post_text[:30]),
            'Не правильное количество знаков в заголовке')
        self.assertEqual(
            title,
            post_text[:30],
            'Не правильный текст заголовка')

    def test_page_create_post_show_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        pages = [
            self.reverse_list['post_create'],
            self.reverse_list['post_edit'],
        ]
        for page in pages:
            response = self.author_client.get(page)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(
                        form_field,
                        expected,
                        f'Не верное поле на странице: {page}'
                    )

    def test_create_new_post_show_pages(self):
        post_text = 'test new post'
        Post.objects.create(
            text=post_text,
            author=self.user_author,
            group=self.group_one
        )

        pages = [
            self.reverse_list['index'],
            self.reverse_list['group_one'],
            self.reverse_list['profile'],
            self.reverse_list['group_two'],
        ]

        for page in pages:
            with self.subTest(page=page):
                response = self.author_client.get(page)
                first_obj = response.context['page_obj'][0]
                if page == self.reverse_list['group_two']:
                    self.assertNotEqual(
                        first_obj.group,
                        self.group_one,
                        'Новый пост попал не в ту группу'
                    )
                else:
                    self.assertEqual(
                        first_obj.text,
                        post_text,
                        f'Новый пост не отобразился первым на странице {page}'
                    )
                    self.assertEqual(
                        first_obj.author,
                        self.user_author,
                        f'Новый пост не принадлежит автору поста на странице '
                        f'{page}'
                    )
                    self.assertEqual(
                        first_obj.group,
                        self.group_one,
                        f'Новый пост не принадлежит группе на странице {page}'
                    )

    def test_cache_index_page(self):
        page = self.reverse_list['index']
        response = self.client.get(page)
        response.context['page_obj'][0].delete()
        first_content = response.content

        response = self.client.get(page)
        cache_content = response.content
        self.assertEqual(
            cache_content,
            first_content,
            'Новый пост взят не из кеша'
        )
        cache.clear()
        response = self.client.get(page)
        self.assertNotEqual(
            cache_content,
            response.content,
            'После очистки кеша страница не изменилась'
        )

    def test_follow_unfollow_authorized(self):
        page_follow = self.reverse_list['post_follow']
        page_unfollow = self.reverse_list['post_unfollow']
        self.authorized_client.get(page_follow)
        followers = list(
            self.user.follower.all().values_list('author', flat=True))
        self.assertIn(
            self.user_author.id,
            followers,
            'Подписка не сработала'
        )
        self.authorized_client.get(page_unfollow)
        followers = list(
            self.user.follower.all().values_list('author', flat=True))
        self.assertNotIn(
            self.user_author.id,
            followers,
            'Отписка не сработала'
        )

    def test_show_post_in_follow_index(self):
        page = self.reverse_list['post_follow_index']
        response = self.authorized_client.get(page)
        self.assertEqual(
            len(response.context['page_obj']),
            0
        )
        Follow.objects.create(
            user=self.user,
            author=self.user_author
        )
        response = self.authorized_client.get(page)
        self.assertNotEqual(
            len(response.context['page_obj']),
            0
        )
        first_obj = response.context['page_obj'][0]
        self.assertEqual(
            first_obj.author,
            self.user_author,
        )
