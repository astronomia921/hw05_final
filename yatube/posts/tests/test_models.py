from django.test import TestCase

from ..models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_post_and_group_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        field_str = (
            (str(self.post), self.post.text[:Post.STR_TEXT_LEN]),
            (str(self.group), self.group.title),
        )
        for value, expected_value in field_str:
            with self.subTest(value=value):
                self.assertEqual(value, expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        fields_model = {
            "text": "Текст поста",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
        }
        for field, ex_value in fields_model.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name,
                    ex_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text,
                    expected_value)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_post')
        cls.user_2 = User.objects.create_user(username='auth_comment')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            author=cls.user_2,
            text='Тестовый комментарий',
            post=cls.post,
        )

    def test_models_comment_has_correct_object_names(self):
        """Проверяем, что у модели корректно работает __str__."""
        field_str = (
            (str(self.comment), self.comment.text[:Comment.STR_TEXT_LEN]),
            (str(self.post), self.post.text[:Post.STR_TEXT_LEN]),
        )
        for value, expected_value in field_str:
            with self.subTest(value=value):
                self.assertEqual(value, expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        fields_model = {
            "text": "Комментарий",
            "created": "Дата создания",
            "author": "Автор",
            "post": 'Пост',
        }
        for field, ex_value in fields_model.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Comment._meta.get_field(field).verbose_name,
                    ex_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Напишите ваши мысли, по поводу поста (будьте вежливы)',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Comment._meta.get_field(field).help_text,
                    expected_value)


class FollowtModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.follow = Follow.objects.create(
            user=cls.user_1,
            author=cls.author,
        )

    def test_follow_str(self):
        """Проверяем, что у модели корректно работает __str__."""
        self.assertEqual(
            str(self.follow),
            f'{self.follow.user} подписался на публикации {self.follow.author}'
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        fields_model = {
            "author": "Автор",
            "user": 'Подписчик',
        }
        for field, ex_value in fields_model.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Follow._meta.get_field(field).verbose_name,
                    ex_value)
