from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Post, Group, Comment, Follow
from .utils import get_page_obj


def index(request):
    template = 'posts/index.html'
    title = 'Главная страница'

    posts_list = Post.objects.select_related('group').all()
    page_obj = get_page_obj(posts_list, request.GET.get('page'))
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    page_obj = get_page_obj(posts_list, request.GET.get('page'))
    template = 'posts/group_list.html'
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    title = f'Профиль пользователя {username}'
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.all()
    page_obj = get_page_obj(posts_list, request.GET.get('page'))
    if not request.user.is_authenticated:
        follow = False
    else:
        follow = request.user.follower.filter(author=author).exists()
    context = {
        'title': title,
        'author': author,
        'page_obj': page_obj,
        'follow': follow,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    title = post.text[:30]
    form = CommentForm()
    comments = Comment.objects.filter(post=post)
    context = {
        'title': title,
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required()
def post_create(request):
    form = PostForm(
        request.POST or None,
        request.FILES or None,
    )
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required()
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post)
    if post.author_id != request.user.id:
        return redirect('posts:post_detail', post_id=post.id)
    if not form.is_valid():
        return render(
            request,
            'posts/post_create.html',
            {'form': form, 'is_edit': True}
        )
    form.save()
    return redirect('posts:post_detail', post_id=post.id)


@login_required()
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required()
def follow_index(request):
    title = 'Ваши подписки'
    template = 'posts/follow.html'
    follow_list = request.user.follower.all().values('author')
    posts_list = Post.objects.select_related('group').filter(
        author__in=follow_list)
    page_obj = get_page_obj(posts_list, request.GET.get('page'))
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required()
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username=username)


@login_required()
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', username=username)
