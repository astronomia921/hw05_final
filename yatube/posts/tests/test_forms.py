import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.comment_author = User.objects.create_user(
            username='comm_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа_2',
            slug='test-group',
            description='Тестовое описание_2'
        )
        cls.small_gif_1 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.small_gif_2 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_1 = SimpleUploadedFile(
            name='small_1.gif',
            content=cls.small_gif_1,
            content_type='image/gif',
        )
        cls.uploaded_2 = SimpleUploadedFile(
            name='small_2.gif',
            content=cls.small_gif_2,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.form = PostForm()
        cls.form = CommentForm
        cls.APP_NAME = 'posts/'

        cls.REVERSES_WAY_CREATE_POST = reverse(
            'posts:create_post')
        cls.REVERSES_WAY_PROFILE = reverse(
            "posts:profile", args=(cls.post.author.username,))
        cls.REVERSES_WAY_POST_DETAIL = reverse(
            'posts:post_detail', args=(cls.post.id,))
        cls.REVERSES_WAY_EDIT = reverse(
            "posts:edit", args=(cls.post.id,))
        cls.REDIRECTS_URL = f'/auth/login/?next=/posts/{cls.post.id}/edit/'
        cls.ADD_COMMENT = f'/posts/{cls.post.id}/comment/'
        cls.LOGIN = f'/auth/login/?next=/posts/{cls.post.id}/comment/'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_comm = Client()
        self.authorized_client_comm.force_login(self.comment_author)

    def test_create_post(self):
        """Проверка создания поста"""
        initial_posts = set(Post.objects.all())
        form_data = {
            'text': 'Текст записанный в форму',
            'group': self.group.id,
            'image': self.uploaded_1,
        }
        response = self.authorized_client.post(self.REVERSES_WAY_CREATE_POST,
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response, self.REVERSES_WAY_PROFILE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        latest_post = Post.objects.latest('id')
        assert_fields = {
            latest_post.text: form_data.get('text'),
            latest_post.author: self.post.author,
            latest_post.group.id: form_data.get('group'),
            latest_post.image: self.APP_NAME + self.uploaded_1.name,
        }
        for value, ex_value in assert_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, ex_value)

        count_posts = set(Post.objects.all()) - initial_posts
        self.assertEqual(len(count_posts), 1)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {
            "text": "Текст записанный в форму",
            "group": self.group2.id,
            "image": self.uploaded_2,
        }
        response = self.authorized_client.post(
            self.REVERSES_WAY_EDIT,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.REVERSES_WAY_POST_DETAIL)

        edit_post = Post.objects.get(id=self.post.id)
        assert_fields = {
            edit_post.text: form_data.get('text'),
            edit_post.group.id: form_data.get('group'),
            edit_post.image: self.APP_NAME + self.uploaded_2.name,
        }
        for value, ex_value in assert_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, ex_value)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_not_create_guest_client(self):
        """Валидная форма не изменит запись в Post если неавторизован."""
        form_data = {
            "text": "Текст записанный в форму",
            "group": self.group.id
        }
        response = self.guest_client.post(
            self.REVERSES_WAY_EDIT,
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, self.REDIRECTS_URL)

    def test_group_null(self):
        '''Проверка что группу можно не указывать'''
        form_data = {
            'text': 'Текст записанный в форму',
            'group': ' ',
        }
        response = self.authorized_client.post(
            self.REVERSES_WAY_EDIT,
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(self.group, form_data.get('group'))

    def test_add_comment_user(self):
        """
        Проверка, что  посты можно комментировать
        только авторизованным пользователям
        """
        initial_comment = set(Comment.objects.all())
        form_data = {
            "text": "Текст комментария",
        }
        response = self.authorized_client_comm.post(
            self.ADD_COMMENT,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        comment = Comment.objects.latest('id')
        assert_fields = {
            comment.text: form_data.get("text"),
            comment.author: self.comment_author,
            comment.post_id: self.post.id,
        }
        for key, value in assert_fields.items():
            with self.subTest(key=key):
                self.assertEqual(key, value)
        self.assertRedirects(
            response, self.REVERSES_WAY_POST_DETAIL)
        count_comment = set(Comment.objects.all()) - initial_comment
        self.assertEqual(len(count_comment), 1)

    def test_add_comment_guest(self):
        """
        Проверка, что посты нельзя комментировать
        неавторизованным пользователям
        """
        form_data = {
            "text": "Текст комментария",
        }
        response = self.guest_client.post(
            self.ADD_COMMENT,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, self.LOGIN)
