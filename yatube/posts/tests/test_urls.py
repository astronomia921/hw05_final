from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Пост",
        )
        cls.TEMPALTES_URL_FOR_GUEST = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.TEMPALTES_URL_FOR_USER = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }
        cls.REDIRECTS_URL = f"/auth/login/?next=/posts/{cls.post.id}/edit/"
        cls.REDIRECTS_POST_CREATE_URL = "/auth/login/?next=/create/"
        cls.POST_EDIT_URL = f"/posts/{cls.post.id}/edit/"
        cls.CREATE_URL = "/create/"
        cls.NO_FOUND_URL = "/unexisting_page/"

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адреса доступные гостю."""
        for address, template in self.TEMPALTES_URL_FOR_GUEST.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_author_correct_template(self):
        """URL-адреса доступный  юзеру"""
        for address, template in self.TEMPALTES_URL_FOR_USER.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_status_code_client(self):
        """URL-адрес не существует"""
        response = self.guest_client.get(self.NO_FOUND_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.guest_client.get(self.CREATE_URL, follow=True)
        self.assertRedirects(response, self.REDIRECTS_POST_CREATE_URL)

    def test_edit_url_redirect_anonymous_on_auth_login(self):
        """Страница /edit/ доступна авторизованному пользователю."""
        response = self.guest_client.get(self.POST_EDIT_URL, follow=True)
        self.assertRedirects(response, self.REDIRECTS_URL)
