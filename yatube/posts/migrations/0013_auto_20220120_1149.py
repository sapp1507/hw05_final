# Generated by Django 2.2.16 on 2022-01-20 11:49

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('posts', '0012_auto_20220120_1133'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='follow',
            name='user',
        ),
        migrations.AddField(
            model_name='follow',
            name='user',
            field=models.ManyToManyField(related_name='follower', to=settings.AUTH_USER_MODEL),
        ),
    ]
