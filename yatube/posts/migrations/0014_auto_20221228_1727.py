# Generated by Django 2.2.16 on 2022-12-28 12:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_follow'),
    ]

    operations = [
        migrations.RenameField(
            model_name='follow',
            old_name='author_f',
            new_name='author',
        ),
        migrations.RenameField(
            model_name='follow',
            old_name='user_f',
            new_name='user',
        ),
    ]
