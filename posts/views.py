from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница"""

    post_list = Post.objects.select_related('group').all()

    paginator = Paginator(post_list, 4)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'index.html', {
                           'page': page,
                           'paginator': paginator
                 })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts_by_group.all()

    pag = Paginator(posts, 4)
    page_number = request.GET.get('page')
    page = pag.get_page(page_number)

    return render(request, 'group.html',
                  {'group': group,
                   'posts': posts,
                   'paginator': pag,
                   'page': page})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('index')

    return render(request, 'new_post.html', {'form': form,
                                             'title': 'Создание новой записи',
                                             'button': 'Отправить'})


def profile(request, username):

    user_post = get_object_or_404(User, username=username)
    post_list = user_post.posts_by_author.all()

    pag = Paginator(post_list, 4)
    page_number = request.GET.get('page')
    page = pag.get_page(page_number)

    # проверим, подписан ли пользователь на автора поста
    if request.user.is_authenticated:
        count = Follow.objects.filter(user=request.user,
                                      author__username=username).count()
        follows = True if count > 0 else False
    else:
        follows = False

    return render(request,
                  'profile.html',
                  {'page': page,
                   'following': follows,
                   'paginator': pag,
                   'author': user_post})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)

    all_comments = post.comments.all()

    comment_form = CommentForm(request.POST or None)

    if comment_form.is_valid():
        new_comment = comment_form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()

    comment_form = CommentForm()

    # проверим, подписан ли пользователь на автора поста
    if request.user.is_authenticated:
        count = Follow.objects.filter(user=request.user,
                                      author__username=username).count()
        follows = True if count > 0 else False
    else:
        follows = False

    return render(request, 'post.html',
                           {'post': post,
                            'author': post.author,
                            'form': comment_form,
                            'following': follows,
                            'comments': all_comments
                            })


@login_required
def add_comment(request, username, post_id):

    post_parent = get_object_or_404(Post,
                                    id=post_id,
                                    author__username=username)

    comment_form = CommentForm(request.POST or None)

    if comment_form.is_valid():
        new_comment = comment_form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post_parent
        new_comment.save()
        return redirect('post', username=username, post_id=post_id)

    return render(request, 'new_comment.html', {'form': comment_form,
                                                'post': post_parent,
                                                'author': post_parent.author,
                                                'title': 'Новый комментарий',
                                                'button': 'Отправить'})


@login_required
def post_edit(request, username, post_id):

    if request.user.username != username:
        return redirect('post', username=username, post_id=post_id)

    the_post = get_object_or_404(Post, id=post_id, author__username=username)

    # проверим, подписан ли пользователь на автора поста
    count = Follow.objects.filter(user=request.user,
                                  author__username=username).count()
    follows = True if count > 0 else False

    edit_form_post = PostForm(request.POST or None,
                              files=request.FILES or None,
                              instance=the_post)

    if edit_form_post.is_valid():
        edit_form_post.save()
        return redirect('post', username=username, post_id=post_id)

    return render(request, 'new_post.html', {'form': edit_form_post,
                                             'post': the_post,
                                             'following': follows,
                                             'title': 'Редактировать заись',
                                             'button': 'Внести изменения'})


@login_required
def follow_index(request):
    """Выводит посты авторов, на которые подписан пользователь"""

    follow_posts = Post.objects.filter(author__following__user=request.user)

    pag = Paginator(follow_posts, 10)
    page_number = request.GET.get('page')
    page = pag.get_page(page_number)

    return render(request,
                  'follow.html',
                  {'page': page,
                   'paginator': pag,
                   'posts': follow_posts})


@login_required
def profile_follow(request, username):
    # username - параметр в который передается автор статьи
    # request.user - тот кто подписывается

    author = get_object_or_404(User, username=username)

    if (author.id != request.user.id):

        user = request.user
        new_follow, is_created = Follow.objects.get_or_create(author=author,
                                                              user=user)

    return HttpResponseRedirect(reverse('profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    # username - параметр в который передается автор статьи
    # request.user - тот кто подписывается
    Follow.objects.filter(author__username=username,
                          user=request.user).delete()
    return HttpResponseRedirect(reverse('profile', args=[username]))


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
