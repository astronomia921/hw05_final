import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.SMALL_GIF = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Пост",
            group=cls.group,
            image=cls.uploaded,
        )
        cls.user2 = User.objects.create_user(username='author2')
        cls.group2 = Group.objects.create(
            title="Тестовая группа2",
            slug="test-slug2",
            description="Тестовое описание2",
        )
        cls.post2 = Post.objects.create(
            text='Тестовый пост от другого автора',
            author=cls.user2,
            group=cls.group2,
            image=cls.uploaded,
        )
        cls.TEMPLATES_PAGES_NAMES = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            f'{cls.group.slug}'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            f'{cls.post.author.username}'}):
                                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            cls.post.id}): 'posts/post_detail.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:edit', kwargs={'post_id': cls.post.id}):
                'posts/create_post.html',
        }
        cls.REVERSES_WAY_INDEX = reverse(
            'posts:index')
        cls.REVERSES_WAY_CREATE_POST = reverse(
            'posts:create_post')
        cls.REVERSES_WAY_GROUP_LIST = reverse(
            "posts:group_list", args=(cls.group.slug,))
        cls.REVERSES_WAY_PROFILE = reverse(
            "posts:profile", args=(cls.post.author.username,))
        cls.REVERSES_WAY_POST_DETAIL = reverse(
            'posts:post_detail', args=(cls.post.id,))

        cls.POSTS_NUM = 10
        cls.GROUP_NUM = 10
        cls.USER_POST_NUMBER = 10

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def check_post_has_correct_info(self, post):
        fields = {
            post.text: self.post.text,
            post.author: self.post.author,
            post.group.id: self.post.group.id,
            post.image: self.post.image,
        }
        for key, value in fields.items():
            with self.subTest(post=post):
                self.assertEqual(key, value)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.TEMPLATES_PAGES_NAMES.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным  контесктом."""
        response = self.guest_client.get(self.REVERSES_WAY_INDEX)
        expected = list(Post.objects.all()[:self.POSTS_NUM])
        self.assertEqual(list(response.context['page_obj']), expected)
        self.check_post_has_correct_info(
            list(response.context["page_obj"])[1])

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным  контесктом."""
        fields_assert_1 = {
            'group_list': self.REVERSES_WAY_GROUP_LIST,
            'profile': self.REVERSES_WAY_PROFILE,
        }
        for key, value in fields_assert_1.items():
            with self.subTest(key=key):
                response = self.guest_client.get(value)

        group = get_object_or_404(Group, slug=self.group.slug)
        author = get_object_or_404(User, username=self.user.username)
        fields_assert_2 = {
            'group': list(
                author.posts.select_related(
                    'author', 'group')[:self.USER_POST_NUMBER]),
            'author': list(
                group.posts.select_related(
                    'group', 'author')[:self.GROUP_NUM])
        }
        for key, expected in fields_assert_2.items():
            with self.subTest(key=key):
                self.assertEqual(list(response.context["page_obj"]), expected)
                self.check_post_has_correct_info(
                    list(response.context["page_obj"])[0])

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.REVERSES_WAY_POST_DETAIL)
        post_context = response.context.get('post')
        post_text = {
            post_context.text: 'Пост',
            post_context.group: self.group,
            post_context.author: self.post.author.username,
            post_context.image: self.post.image,
        }
        for value, expected in post_text.items():
            self.assertEqual(post_text[value], expected)

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        response_index = self.authorized_client.get(
            self.REVERSES_WAY_INDEX)
        response_group = self.authorized_client.get(
            self.REVERSES_WAY_GROUP_LIST)
        response_profile = self.authorized_client.get(
            self.REVERSES_WAY_PROFILE)
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        assert_values = (
            (self.post, index),
            (self.post, group),
            (self.post, profile),
        )
        for value, expected_value in assert_values:
            with self.subTest(value=value):
                self.assertIn(value, expected_value)

    def test_post_added_correctly_user2(self):
        """Пост при создании не добавляется другому пользователю
           Но виден на главной и в группе"""
        posts_count = Post.objects.filter(group=self.group).count()
        response_profile = self.authorized_client.get(
            self.REVERSES_WAY_PROFILE)
        group = Post.objects.filter(group=self.group).count()
        profile = response_profile.context['page_obj']
        self.assertEqual(group, posts_count, 'поста нет в другой группе')
        self.assertNotIn(self.post2, profile)

    def test_cache_index(self):
        """Тестирование хранения и очистки кэша в index"""
        post = Post.objects.create(
            text='Пост для тестирования кэша',
            author=self.user)
        response_1 = self.authorized_client.get(
            self.REVERSES_WAY_INDEX).content
        post.delete()
        response_2 = self.authorized_client.get(
            self.REVERSES_WAY_INDEX).content
        self.assertEqual(response_1, response_2)
        cache.clear()
        response_3 = self.authorized_client.get(
            self.REVERSES_WAY_INDEX).content
        self.assertNotEqual(response_3, response_2)


class PaginatorViewsTest(TestCase):
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
            group=cls.group,
        )
        cls.REVERSE_PAGE = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(cls.group.slug,)),
            reverse('posts:profile', args=(cls.post.author.username,)),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.NUM_OF_POSTS = 14
        new_post_page = [(
            Post(text=f'Тестовый текст {i}',
                 group=self.group,
                 author=self.user)) for i in range(1, self.NUM_OF_POSTS)
        ]
        Post.objects.bulk_create(new_post_page)
        self.POSTS_NUMBER_ON_PG = 10
        self.POSTS_ON_FOLLOW_PAGE = self.NUM_OF_POSTS - self.POSTS_NUMBER_ON_PG
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """ Проверка Паджинатора """
        for pages in self.REVERSE_PAGE:
            with self.subTest(pages=pages):
                self.assertEqual(len(self.guest_client.get(
                    pages).context.get('page_obj')),
                    self.POSTS_NUMBER_ON_PG
                )
                self.assertEqual(len(self.guest_client.get(
                    pages + '?page=2').context.get('page_obj')),
                    self.POSTS_ON_FOLLOW_PAGE
                )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(
            username='author',
        )
        cls.user_follower = User.objects.create(
            username='follower',
        )
        cls.user_follower_2 = User.objects.create(
            username='follower_2',
        )
        cls.post = Post.objects.create(
            text='Пост для подписки',
            author=cls.user_author,
        )
        cls.post_1 = Post.objects.create(
            text='Пост для подписки',
            author=cls.user_author,
        )
        cls.REVERSES_PROFILE_FOLLOW = reverse(
            'posts:profile_follow',
            args=(cls.user_author,)
        )
        cls.REVERSES_PROFILE = reverse(
            'posts:profile',
            args=(cls.user_author.username,)
        )
        cls.REVERSES_PROFILE_UNFOLLOW = reverse(
            'posts:profile_unfollow',
            args=(cls.user_author.username,)
        )
        cls.REDIRECT_LOGIN = (
            f'/auth/login/?next=/profile/{cls.user_author.username}/unfollow/')
        cls.FOLLOW_INDEX = reverse('posts:follow_index')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_follower)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_follower_2)
        cache.clear()

    def test_follow_user(self):
        """
        Проверка подписки на автора и удаления подписки.
        Увеличение подписки. Уменьшения подписки.
        """
        initial_follower = set(Follow.objects.all())
        form_data_follow = {
            'user': self.user_follower,
            'author': self.user_author,
        }
        response = self.authorized_client.post(
            self.REVERSES_PROFILE_FOLLOW,
            data=form_data_follow, follow=True)
        follow = Follow.objects.latest('id')
        assert_fields = {
            follow.user: self.user_follower,
            follow.author: self.post.author,
        }
        for key, value in assert_fields.items():
            with self.subTest(key=key):
                self.assertEqual(key, value)
        self.assertRedirects(response, self.REVERSES_PROFILE)

        count_follow = set(Follow.objects.all()) - initial_follower
        self.assertEqual(len(count_follow), 1)

        response = self.authorized_client.post(
            self.REVERSES_PROFILE_UNFOLLOW,
            data=form_data_follow, follow=True)

        count_follow = set(Follow.objects.all()) - initial_follower
        self.assertEqual(len(count_follow), 0)

    def test_unfollow_user(self):
        """Посты не доступны пользователю - неподписчику"""
        initial_follower = set(Follow.objects.all())
        form_data_follow = {
            'user': self.user_follower,
            'author': self.user_author,
        }
        response = self.guest_client.post(
            self.REVERSES_PROFILE_UNFOLLOW,
            data=form_data_follow, follow=True
        )
        self.assertFalse(Follow.objects.filter(
                         user=self.user_follower,
                         author=self.user_author).exists())
        self.assertRedirects(response, self.REDIRECT_LOGIN)

        count_follow = set(Follow.objects.all()) - initial_follower
        self.assertEqual(len(count_follow), 0)

    def test_follower_see_new_post(self):
        """У подписчика появляется новый пост автора"""
        post = Post.objects.create(
            author=self.user_author,
            text='Пост')
        Follow.objects.create(
            author=self.user_author,
            user=self.user_follower,
        )
        response = self.authorized_client.get(self.FOLLOW_INDEX)
        new_posts = response.context.get('page_obj')
        self.assertIn(post, new_posts)

    def test_follower_see_new_post(self):
        """У не подписчика не появляется новый пост автора"""
        post = Post.objects.create(
            author=self.user_author,
            text='Пост')
        Follow.objects.create(
            author=self.user_author,
            user=self.user_follower,
        )
        response = self.authorized_client_2.get(self.FOLLOW_INDEX)
        new_posts = response.context.get('page_obj')
        self.assertNotIn(post, new_posts)
