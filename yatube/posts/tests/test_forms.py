import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models import Post, Group, Comment


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(
            username='test_user_author')
        cls.user_not_author = User.objects.create_user(
            username='test_user_not_author')
        cls.group = Group.objects.create(
            title='test title group',
            description='test desc group',
            slug='test_slug'
        )
        cls.group_two = Group.objects.create(
            title='test title group_two',
            description='test desc group_two',
            slug='test_slug_two'
        )
        for i in range(13):
            Post.objects.create(
                text=f'test post tex number {i}',
                author=cls.user_author,
                group=cls.group
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.user_not_author)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'new post text',
            'group': self.group.id,
        }
        clients = {
            'guest': self.client,
            'author': self.author_client,
        }
        page = reverse('posts:post_create')
        for test, client in clients.items():
            response = client.post(
                page,
                data=form_data,
                follow=True
            )
            new_post_count = Post.objects.count()
            with self.subTest(test=test):
                self.assertEqual(
                    new_post_count,
                    post_count + (1 if test == 'author' else 0),
                    f'{"Не " if test == "author" else ""}Изменилось '
                    f'количество постов при создании пользователем {test}'
                )
                if test == 'author':
                    last_create_post = Post.objects.all().order_by('-id')[0]
                    self.assertEqual(
                        last_create_post.text,
                        form_data['text'],
                        'Текст поста не соответствует переданному'
                    )
                    self.assertEqual(
                        last_create_post.group_id,
                        form_data['group'],
                        'Группа поста не соответствует переданному'
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:profile',
                                kwargs={'username': self.user_author})
                    )

    def test_create_post_image(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'new text image',
            'group': self.group.id,
            'data': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        new_post_count = Post.objects.count()
        self.assertEqual(
            post_count + 1,
            new_post_count,
            'Не изменилось количество постов'
        )

    def test_edit_post(self):
        post_count = Post.objects.count()
        old_post = Post.objects.get(pk=1)
        form_data = {
            'text': 'edit post',
            'group': self.group_two.id
        }
        page = reverse('posts:post_edit', kwargs={'post_id': old_post.id})
        clients = {
            'guest': self.client,
            'not_author': self.not_author_client,
            'author': self.author_client
        }
        for test, client in clients.items():
            response = client.post(
                page,
                data=form_data,
                follow=True
            )
            new_post = Post.objects.get(pk=old_post.id)
            with self.subTest(test=test):
                self.assertEqual(
                    post_count,
                    Post.objects.count(),
                    'Изменилось количество постов'
                )
                if test == 'author':
                    self.assertEqual(
                        new_post.text,
                        form_data['text'],
                        'Текст не изменился автором поста'
                    )
                    self.assertEqual(
                        new_post.group.id,
                        form_data['group'],
                        'Группа у поста не изменилась автором поста'
                    )
                    self.assertRedirects(
                        response,
                        reverse(
                            'posts:post_detail',
                            kwargs={'post_id': old_post.id}),
                    )
                else:
                    self.assertNotEqual(
                        new_post.text,
                        form_data['text'],
                        f'Текс поста изменен пользователем {test}'
                    )
                    self.assertNotEqual(
                        new_post.group_id,
                        form_data['group'],
                        f'Группа поста изменена пользователем {test}'
                    )

    def test_create_new_comment_for_guest(self):
        comment_count = Comment.objects.count()
        post_id = Post.objects.all()[0].id
        page = reverse(
            'posts:add_comment',
            kwargs={'post_id': post_id}
        )
        form_data = {
            'text': 'new comment',
        }
        response = self.client.post(
            page,
            data=form_data,
            follow=True,
        )
        new_comment_count = Comment.objects.count()
        self.assertEqual(
            comment_count,
            new_comment_count,
            'Изменилось количество комментариев при создании гостем'
        )

    def test_create_new_comment_for_authorized(self):
        comment_count = Comment.objects.count()
        post_id = Post.objects.all()[0].id
        page = reverse(
            'posts:add_comment',
            kwargs={'post_id': post_id},
        )
        form_data = {
            'text': 'new comment',
        }
        response = self.author_client.post(
            page,
            data=form_data,
            follow=True,
        )
        new_comment_count = Comment.objects.count()
        self.assertEqual(
            new_comment_count,
            comment_count + 1,
            'Не изменилось количество постов авторизованным клиентом'
        )
        expected_comment = Comment.objects.all().order_by('-id')[0]
        self.assertEqual(
            expected_comment.text,
            form_data['text'],
            'Комментарий не появился на странице поста'
        )

