from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='А' * 100,
        )

    def test_verbose_name_post(self):
        post = PostModelTest.post
        field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text_post(self):
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу'
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        group = PostModelTest.group

        expected_object_name = {
            post: post.text[:15],
            group: group.title,
        }
        for model, expected_name in expected_object_name.items():
            with self.subTest(model=model):
                self.assertEqual(
                    str(model),
                    expected_name
                )
