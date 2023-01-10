# from collections import ChainMap

from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

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
        cls.TEMPALTES_URL = {
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

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def setUp(self):
        cache.clear()

    def test_urls_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.TEMPALTES_URL.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_redirect_url(self):
        """
        Страница create и edit доступны только авторизованнаому пользователю.
        """
        fields_assert = {
            self.REDIRECTS_POST_CREATE_URL: self.guest_client.get(
                self.CREATE_URL, follow=True),
            self.REDIRECTS_URL: self.guest_client.get(
                self.POST_EDIT_URL, follow=True),
        }
        for key, response in fields_assert.items():
            with self.subTest(key=key):
                self.assertRedirects(response, key)

    def test_http(self):
        """Проверка кодов возврата на всех существующих адресах."""
        # хотел через ChainMap, понимаю, что он делает
        # но не до конца понимаю как именно в этом случае сделать
        field_urls_code = {
            reverse(
                'posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                args=(self.group.slug,)): HTTPStatus.OK,
            reverse(
                'posts:profile',
                args=(self.user.username,)): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                args=(self.post.id,)): HTTPStatus.OK,
            reverse(
                'posts:edit',
                args=(self.post.id,)): HTTPStatus.OK,
            reverse(
                'posts:create_post'): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, http in field_urls_code.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, http)
