# Generated by Django 5.0.1 on 2024-02-11 02:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authors', '0003_authors_remove_author_email_remove_author_firstname_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='HasComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='MakesPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='OwnComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='OwnLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('pid', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('public', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('firstName', models.CharField(default='', max_length=50)),
                ('lastName', models.CharField(default='', max_length=50)),
                ('email', models.EmailField(default='unknown@example.com', max_length=254, unique=True)),
                ('password', models.CharField(default='', max_length=255)),
                ('github', models.CharField(default='', max_length=100)),
                ('profileImage', models.ImageField(blank=True, null=True, upload_to='assets/profile_images/')),
            ],
        ),
        migrations.DeleteModel(
            name='Authors',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='author',
        ),
        migrations.RemoveField(
            model_name='like',
            name='author',
        ),
        migrations.AddField(
            model_name='hascomment',
            name='comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.comment'),
        ),
        migrations.AddField(
            model_name='hascomment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.makespost'),
        ),
        migrations.AddField(
            model_name='owncomment',
            name='comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.comment'),
        ),
        migrations.AddField(
            model_name='ownlike',
            name='like',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.like'),
        ),
        migrations.AddField(
            model_name='makespost',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.post'),
        ),
        migrations.AddField(
            model_name='post',
            name='uid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.user'),
        ),
        migrations.AddField(
            model_name='ownlike',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.user'),
        ),
        migrations.AddField(
            model_name='owncomment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.user'),
        ),
        migrations.AddField(
            model_name='makespost',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authors.user'),
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='authors.user'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='like',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='authors.user'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='followedby',
            name='id1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follows', to='authors.user'),
        ),
        migrations.AlterField(
            model_name='followedby',
            name='id2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to='authors.user'),
        ),
        migrations.AlterField(
            model_name='follows',
            name='followed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followed_set', to='authors.user'),
        ),
        migrations.AlterField(
            model_name='follows',
            name='follower',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower_set', to='authors.user'),
        ),
    ]
