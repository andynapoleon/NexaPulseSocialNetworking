# Generated by Django 5.0.1 on 2024-04-07 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authors', '0007_alter_author_github_alter_author_profileimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='host',
            field=models.URLField(blank=True, default='https://nexapulse1-7fbca99d2d7b.herokuapp.com/', max_length=500, null=True),
        ),
    ]
