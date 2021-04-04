import os
import tempfile
from datetime import datetime

from PIL import Image

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post


class TestPosts(TestCase):
    def setUp(self):
        self.client_ano = Client()
        self.client_log = Client()

        self.anonim_user_name = 'anonim_user'
        self.anonim_user = User.objects.create_user(self.anonim_user_name,
                                                    'test_user@test.com',
                                                    'test_user_2020')

        self.login_user_name = 'login_user'
        self.login_user = User.objects.create_user(self.login_user_name,
                                                   'test_user2@test.com',
                                                   'test_user_2020')
        self.client_log.force_login(self.login_user)

    def test_personal_page(self):
        """Проверяет создание страницы нового пользователя."""

        # Переход на страницу тестового пользователя
        response = self.client_log.get(reverse('profile',
                                               args=[self.login_user_name]),
                                       follow=True)
        self.assertEqual(response.status_code, 200, msg='Userpage not found!')

    def test_create_new_post_by_login_user(self):
        """ Проверяет что авторизованный
        пользователь может опубликовать пост.
        """

        post_text = 'New TEXT !!!'
        response = self.client_log.post(reverse('new_post'),
                                        {
                                            'text': post_text,
                                            'author': self.login_user_name
                                        },
                                        follow=True)

        count = Post.objects.filter(author=self.login_user.id).count()
        self.assertEqual(1, count, msg='Пост не опубликован')
        self.assertRedirects(response, '/')

    def test_create_new_post_by_anonim_user(self):
        """Проверяет что неавторизованный пользователь
        не может опубликовать пост.
        """

        response = self.client_ano.post(reverse('new_post'),
                                        {'text': 'New TEXT !!!',
                                        'author': self.anonim_user.username},
                                        follow=True)
        login = 'login'
        new_post = 'new_post'
        url = (f'{reverse(login)}?next={reverse(new_post)}')
        self.assertRedirects(response, url)

        count = Post.objects.filter(author=self.anonim_user.id).count()
        self.assertEqual(0,
                         count,
                         msg='Создан пост неавторизованным пользователем')

    def test_check_new_post_on_pages(self):
        """Проверяет наличее созданного пост на страницах:
        Index, Post, Profile
        """

        post_text = 'New TEXT !!!'
        self.client_log.post(reverse('new_post'),
                             {
                                'text': post_text,
                                'author': self.login_user_name
                             },
                             follow=False)
        self.check_correct_text_on_pages(post_text)

    def test_login_user_can_edit_his_post(self):
        """Проверяет что залогиненый пользователь может отредактирвать свой пост.
        Изменения будут везде.
        """

        post_text = 'New TEXT !!!'
        edit_post_text = 'edit TEXT !!!'

        self.client_log.post(reverse('new_post'),
                             {
                                'text': post_text,
                                'author': self.login_user_name
                             },
                             follow=False)

        self.client_log.post(reverse('post_edit',
                                     args=[self.login_user_name, 1]),
                             {
                             'text': edit_post_text,
                             'author': self.login_user_name
                             },
                             follow=False)

        self.check_correct_text_on_pages(edit_post_text)

    def check_correct_text_on_pages(self, text_to_find):
        """Проверяет страницы 'insex', 'profile', 'post'
        на наличее поста с указанным текстом.
        """
        cache.clear()
        # Check post on the index page:
        response = self.client_log.get(reverse('index'))

        self.assertEqual(text_to_find,
                         response.context['page'].object_list[0].text,
                         msg='Нет записи с текстом на странице index')

        # Check post on the prifile page:
        response = self.client_log.get(reverse('profile',
                                               args=[self.login_user_name]))
        self.assertEqual(text_to_find,
                         response.context['page'].object_list[0].text,
                         msg='Нет записи с текстом на странице prifile')

        # Check post on the prifile/id/ page:
        response = self.client_log.get(reverse('post',
                                               args=[self.login_user_name, 1]))
        post = response.context['post']
        self.assertEqual(text_to_find,
                         post.text,
                         msg='Нет записи с текстом на стр. prifile/post_id')


class TestsFolowsImagesOthers(TestCase):
    def setUp(self):

        self.client = Client()
        self.client_author = Client()
        self.client_anonim = Client()

        self.login_user_name = 'login_user'
        self.login_user = User.objects.create_user(self.login_user_name,
                                                   'test_user2@test.com',
                                                   'test_user_2020')
        self.client.force_login(self.login_user)

        self.login_author_name = 'author_user'
        self.login_author = User.objects.create_user(self.login_author_name,
                                                     'test_user2@test.com',
                                                     'test_user_2020')
        self.client_author.force_login(self.login_author)

    def test_get_404_page(self):
        """Проверка работы страниц ошибок"""
        response = self.client.get('/strange_page_which_never_will_be_used/')
        self.assertEqual(response.status_code,
                         404,
                         msg='Сервер не возвращает код 404')

    def test_images(self):
        """Проверка загрузки и наличия изображений"""

        img_file = Image.new('RGB', (250, 250), (255, 255, 255))
        img_file.save('tmp.png')

        Group.objects.create(title='group1', slug='g')
        group = Group.objects.get(pk=1)

        with open('tmp.png', 'rb') as img:
            self.client.post(reverse('new_post'),
                             {'author': self.login_user,
                              'group': group.id,
                              'text': 'post with image',
                              'image': img})
            cache.clear()
            response = self.client.get(reverse('index'))
            self.assertContains(response, '<img')

            response = self.client.get(reverse('post',
                                               args=[self.login_user_name, 1]))
            self.assertContains(response, '<img')

            response = self.client.get(reverse('profile',
                                               args=[self.login_user_name]))
            self.assertContains(response, '<img')

            response = self.client.get(reverse('group', args=['g']))
            self.assertContains(response, '<img')

        os.remove('tmp.png')

    def test_bad_images(self):
        """Проверка загрузки не изображения"""

        cache.clear()
        fd, temp_file = tempfile.mkstemp(suffix='.txt', prefix='temp_file_')

        with open(temp_file, 'w') as f:
            f.write('post image')

        with open(temp_file, 'rb') as img:
            post = self.client.post(reverse('new_post'),
                                    {'author': self.login_user,
                                     'text': 'post with image',
                                     'image': img},
                                    follow=True)
        os.close(fd)
        os.remove(temp_file)
        self.assertContains(post, 'Загрузите правильное изображение')

    def test_cache(self):
        self.client.post(reverse('new_post'), {
                                                'author': self.login_user,
                                                'text': 'I cant see this note!'
                                              },
                         follow=True)
        cache.clear()

        # первый запрос
        dt0 = datetime.now()
        self.client.get(reverse('index'))
        dt1 = datetime.now()
        timedelta1 = dt1 - dt0

        # Второй запрос
        dt0 = datetime.now()
        self.client.get(reverse('index'))
        dt1 = datetime.now()
        timedelta2 = dt1 - dt0

        self.assertTrue(timedelta2 < timedelta1)

        cache.clear()
        self.client.get(reverse('index'))
        with self.assertNumQueries(0):
            self.client.get(reverse('index'))

    def test_user_can_follow_the_author(self):
        self.client_author.post(reverse('new_post'),
                                {
                                    'text': 'i am author',
                                    'author': self.login_author_name
                                })

        self.client.post(reverse('profile_follow',
                                 args=[self.login_author_name]))

        follows = Follow.objects.filter(user=self.login_user,
                                        author=self.login_author).all()

        self.assertEqual(1, follows.count(), msg='No follow created!')

    def test_user_can_unfollow_the_author(self):
        Follow.objects.create(user=self.login_user, author=self.login_author)
        self.client.post(reverse('profile_unfollow',
                                 args=[self.login_author_name]))

        follows = Follow.objects.filter(user=self.login_user,
                                        author=self.login_author).all()
        self.assertEqual(0, follows.count(), msg='User has not unfolow')

    def test_new_post_appeared_on_follow(self):
        self.client.post(reverse('profile_follow',
                                 args=[self.login_author_name]))

        self.client_author.post(reverse('new_post'),
                                {'text': 'i am author',
                                 'author': self.login_author_name})

        response = self.client.get(reverse('follow_index'))
        self.assertEqual(1,
                         len(response.context['page'].object_list),
                         msg='Post is not appear to follow user')

    def test_new_post_not_appeared_on_unfollow(self):
        self.client_author.post(reverse('new_post'),
                                {'text': 'i am author',
                                 'author': self.login_author_name})

        response = self.client.get(reverse('follow_index'))
        self.assertEqual(0,
                         len(response.context['page'].object_list),
                         msg='Post is appear to unfollow user')

    def test_auth_user_can_comment(self):
        self.client_author.post(reverse('new_post'),
                                {'text': 'i am author',
                                 'author': self.login_author_name})

        self.client_author.post(reverse('add_comment',
                                        args=[self.login_author_name, 1]),
                                {'text': 'my comment'})
        self.assertEqual(1,
                         len(Comment.objects.all()),
                         msg='auth. user cant comment')
