from django.forms import ModelForm, Textarea

from posts.models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        help_texts = {
            'group': 'Группа, в которую будет добавлен новый пост',
            'text': 'Добавьте сюда содержание поста',
            'image': 'Добавьте сюда изображение поста'
        }

        labels = {
            'group': 'Группа',
            'text': 'Текст',
            'image': 'Изображение'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        wiget = {'text': Textarea()}
