from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, render, redirect

from .forms import CommentForm, PostForm

from .models import Follow, Group, Post

from .utils import get_paginator

User = get_user_model()


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    context = get_paginator(post_list, request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group', 'author')
    context = {
        'group': group,
    }
    context.update(get_paginator(post_list, request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('author', 'group')
    following = request.user.is_authenticated
    following_true = (
        following and author.following.filter(
            user=request.user, author=author
        ).exists()
    )
    context = {
        'author': author,
        'following': following_true,
    }
    context.update(get_paginator(post_list, request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    comment = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    )
    if not form.is_valid():
        context = {'form': form}
        return render(request, 'posts/create_post.html', context)
    create_post = form.save(commit=False)
    create_post.author = request.user
    create_post.save()
    return redirect('posts:profile', create_post.author)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=edit_post)
    if not form.is_valid():
        context = {
            'form': form,
            'edit_post': edit_post,
        }
        return render(request, 'posts/create_post.html', context)
    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user)
    context = get_paginator(posts, request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(
        Follow, author__username=username, user=request.user)
    follow.delete()
    return redirect('posts:profile', username)
