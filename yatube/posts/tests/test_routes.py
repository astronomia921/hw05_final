from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class URLTests(TestCase):
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
        cls.TEMPLATES_REVERSE = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:follow_index'): 'posts/follow.html',
            reverse(
                'posts:group_list',
                args=(cls.group.slug,)): 'posts/group_list.html',
            reverse(
                'posts:profile',
                args=(cls.user.username,)): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                args=(cls.post.id,)): 'posts/post_detail.html',
            reverse(
                'posts:create_post'): 'posts/create_post.html',
            reverse(
                'posts:edit',
                args=(cls.post.id,)): 'posts/create_post.html',
        }
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def setUp(self):
        cache.clear()

    def test_url(self):
        """Реверсы дают ожидаемые URLы"""
        for reverse_path, url in self.TEMPLATES_REVERSE.items():
            with self.subTest(reverse_path=reverse_path):
                response = self.authorized_client.get(reverse_path)
                self.assertTemplateUsed(response, url)
