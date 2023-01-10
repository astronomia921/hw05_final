import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from http import HTTPStatus

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
        cls.SMALL_GIF_1 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.SMALL_GIF_2 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_1 = SimpleUploadedFile(
            name='small_1.gif',
            content=cls.SMALL_GIF_1,
            content_type='image/gif',
        )
        cls.uploaded_2 = SimpleUploadedFile(
            name='small_2.gif',
            content=cls.SMALL_GIF_2,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.form = PostForm()
        cls.form = CommentForm
        cls.APP_NAME = 'posts/'

        cls.CREATE_POST_URL = reverse(
            'posts:create_post')
        cls.PROFILE_REVERSE = reverse(
            "posts:profile", args=(cls.post.author.username,))
        cls.POST_DETAIL_REVERSE = reverse(
            'posts:post_detail', args=(cls.post.id,))
        cls.POST_EDIT_REVERSE = reverse(
            "posts:edit", args=(cls.post.id,))
        cls.REDIRECTS_REVERSE = f'/auth/login/?next=/posts/{cls.post.id}/edit/'
        cls.ADD_COMMENT_REVERSE = f'/posts/{cls.post.id}/comment/'
        cls.LOGIN_REVERSE = f'/auth/login/?next=/posts/{cls.post.id}/comment/'

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_comm = Client()
        cls.authorized_client_comm.force_login(cls.comment_author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_create_post(self):
        """Проверка создания поста"""
        initial_posts = set(Post.objects.all())
        form_data = {
            'text': 'Текст записанный в форму',
            'group': self.group.id,
            'image': self.uploaded_1,
        }
        response = self.authorized_client.post(self.CREATE_POST_URL,
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response, self.PROFILE_REVERSE)
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

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.CREATE_POST_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_forms_show_correct_info(self):
        """Проверка коректности формы поста."""
        fields = {
            reverse('posts:create_post'),
            reverse('posts:edit', args=(self.post.id,)),
        }
        for reverse_page in fields:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField)
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField)
                self.assertIsInstance(
                    response.context['form'].fields['image'],
                    forms.fields.ImageField)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {
            "text": "Текст записанный в форму",
            "group": self.group2.id,
            "image": self.uploaded_2,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_REVERSE,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_DETAIL_REVERSE)

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
            self.POST_EDIT_REVERSE,
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, self.REDIRECTS_REVERSE)

    def test_group_null(self):
        '''Проверка что группу можно не указывать'''
        form_data = {
            'text': 'Текст записанный в форму',
            'group': ' ',
        }
        response = self.authorized_client.post(
            self.POST_EDIT_REVERSE,
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
            self.ADD_COMMENT_REVERSE,
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
            response, self.POST_DETAIL_REVERSE)
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
            self.ADD_COMMENT_REVERSE,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, self.LOGIN_REVERSE)
