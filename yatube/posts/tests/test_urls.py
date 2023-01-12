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
        cls.FIELDS_URLS_STATUS_CODE = {
            reverse(
                'posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                args=(cls.group.slug,)): HTTPStatus.OK,
            reverse(
                'posts:profile',
                args=(cls.user.username,)): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                args=(cls.post.id,)): HTTPStatus.OK,
            reverse(
                'posts:edit',
                args=(cls.post.id,)): HTTPStatus.OK,
            reverse(
                'posts:create_post'): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        cls.REDIRECTS_URL = f"/auth/login/?next=/posts/{cls.post.id}/edit/"
        cls.REDIRECTS_POST_CREATE_URL = "/auth/login/?next=/create/"
        cls.POST_EDIT_URL = f"/posts/{cls.post.id}/edit/"
        cls.CREATE_URL = "/create/"
        cls.NO_FOUND_URL = "/unexisting_page/"

        cls.INDEX_URL = '/'
        cls.FOLLOW_URL = '/follow/'
        cls.GROUP_LIST_URL = f'/group/{cls.group.slug}/'
        cls.PROFILE_URL = f'/profile/{cls.user.username}/'
        cls.POST_DETAIL_URL = f'/posts/{cls.post.id}/'
        cls.CREATE_POST_URL = '/create/'
        cls.POST_EDIT_URL = f'/posts/{cls.post.id}/edit/'

        cls.TEMPALTES_URL = {
            cls.INDEX_URL: 'posts/index.html',
            cls.FOLLOW_URL: 'posts/follow.html',
            cls.GROUP_LIST_URL: 'posts/group_list.html',
            cls.PROFILE_URL: 'posts/profile.html',
            cls.POST_DETAIL_URL: 'posts/post_detail.html',
            cls.CREATE_POST_URL: 'posts/create_post.html',
            cls.POST_EDIT_URL: 'posts/create_post.html',
        }

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

    def test_http_status_code(self):
        """Проверка кодов возврата на всех существующих адресах."""
        for url, http_status_code in self.FIELDS_URLS_STATUS_CODE.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, http_status_code)
