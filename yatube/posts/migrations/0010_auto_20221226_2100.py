# Generated by Django 2.2.16 on 2022-12-26 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'default_related_name': 'comments', 'ordering': ['-created'], 'verbose_name': 'Комментарий', 'verbose_name_plural': 'Коментарии'},
        ),
    ]