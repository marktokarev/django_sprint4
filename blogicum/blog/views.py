from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, UserForm
from .models import Category, Comment, Post

User = get_user_model()
POSTS_PER_PAGE = 10


def annotate_comment_count(queryset):
    """Аннотирует queryset количеством комментариев."""
    return queryset.annotate(
        comment_count=Count('comments'),
    ).order_by('-pub_date')


def get_published_posts():
    """Возвращает QuerySet опубликованных постов с количеством комментариев."""
    return annotate_comment_count(
        Post.objects.select_related(
            'author', 'location', 'category',
        ).filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    )


def paginate_queryset(request, queryset, per_page=POSTS_PER_PAGE):
    """Пагинация queryset."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    """Главная страница."""
    page_obj = paginate_queryset(request, get_published_posts())
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    """Страница отдельной публикации."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        post = get_object_or_404(
            get_published_posts(),
            pk=post_id,
        )
    comments = post.comments.select_related('author')
    form = CommentForm()
    return render(request, 'blog/detail.html', {
        'post': post,
        'form': form,
        'comments': comments,
    })


def category_posts(request, category_slug):
    """Страница категории."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    post_list = get_published_posts().filter(category=category)
    page_obj = paginate_queryset(request, post_list)
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
    })


def profile(request, username):
    """Страница пользователя."""
    profile_user = get_object_or_404(User, username=username)
    if request.user == profile_user:
        posts = annotate_comment_count(
            Post.objects.select_related(
                'author', 'location', 'category',
            ).filter(
                author=profile_user,
            )
        )
    else:
        posts = get_published_posts().filter(author=profile_user)
    page_obj = paginate_queryset(request, posts)
    return render(request, 'blog/profile.html', {
        'profile': profile_user,
        'page_obj': page_obj,
    })


@login_required
def edit_profile(request):
    """Редактирование профиля."""
    form = UserForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    """Создание публикации."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирование публикации."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    """Удаление публикации."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(instance=post)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', {'form': form})


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария."""
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария."""
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})
