from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': _('Текст поста'),
            'group': _('Группа'),
            'image': _('Изображение (необязательно)'),
        }
        help_texts = {
            'text': _('Введите текст поста'),
            'group': _('Укажите группу'),
            'image': _('Добавьте изображение (необязательно)'),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': _('Комментарий'),
        }
        help_texts = {
            'text': _('Напишите ваши мысли, по поводу поста (будьте вежливы)'),
        }
